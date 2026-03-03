from datetime import datetime
import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from app.schemas.api import ApiResponse, PaginatedApiResponse


UNKNOWN_REFERRAL_CODE = "Unknown"


def normalize_email_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def normalize_phone_number_value(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    if not re.fullmatch(r"\+?[0-9\s\-().]+", cleaned):
        raise ValueError("phone_number chỉ được chứa số và các ký tự định dạng phổ biến")

    digits = "".join(char for char in cleaned if char.isdigit())
    if len(digits) < 9 or len(digits) > 15:
        raise ValueError("phone_number phải có từ 9 đến 15 chữ số")

    return digits


class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    referral_code: Optional[str] = None

    @field_validator("phone_number", "full_name", mode="before")
    @classmethod
    def normalize_optional_text(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value

    @field_validator("referral_code", mode="before")
    @classmethod
    def normalize_referral_code(cls, value):
        if value is None:
            return UNKNOWN_REFERRAL_CODE
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or UNKNOWN_REFERRAL_CODE
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: Optional[str]) -> Optional[str]:
        return normalize_email_value(value)

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        return normalize_phone_number_value(value)

    @model_validator(mode="after")
    def validate_contact_info(self):
        if not self.email and not self.phone_number:
            raise ValueError("Cần cung cấp ít nhất email hoặc phone_number")
        return self


class UserResponse(BaseModel):
    id: UUID
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    referral_code: Optional[str] = None
    status: str
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ReferralCodeStats(BaseModel):
    referral_code: str
    total_users: int


class UserSingleApiResponse(ApiResponse[UserResponse]):
    pass


class UserListApiResponse(PaginatedApiResponse[UserResponse]):
    pass


class ReferralCodeStatsApiResponse(ApiResponse[list[ReferralCodeStats]]):
    pass
