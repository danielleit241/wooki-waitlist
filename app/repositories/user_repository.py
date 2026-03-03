from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import Session
from uuid import UUID

from app.models import User, UserStatus
from app.schemas import UserCreate
from app.schemas.user import UNKNOWN_REFERRAL_CODE, normalize_email_value, normalize_phone_number_value


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_users(self, page: int, limit: int) -> tuple[list[User], int]:
        base_query = self.db.query(User).filter(User.is_active.is_(True))
        total_items = base_query.count()
        offset = (page - 1) * limit
        users = (
            base_query
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return users, total_items

    def find_duplicate_field(self, email: str | None, phone_number: str | None) -> str | None:
        if email is not None:
            existing_emails = self.db.query(User.email).filter(User.email.isnot(None)).all()
            for (existing_email,) in existing_emails:
                if normalize_email_value(existing_email) == email:
                    return "email"

        if phone_number is not None:
            existing_phones = self.db.query(User.phone_number).filter(User.phone_number.isnot(None)).all()
            for (existing_phone,) in existing_phones:
                try:
                    normalized_phone = normalize_phone_number_value(existing_phone)
                except ValueError:
                    normalized_phone = None
                if normalized_phone == phone_number:
                    return "phone_number"

        return None

    def create_user(self, payload: UserCreate) -> User:
        user = User(
            email=payload.email,
            phone_number=payload.phone_number,
            full_name=payload.full_name,
            referral_code=payload.referral_code,
            status=UserStatus.PENDING.value,
            is_active=True,
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def delete_user(self, user_id: UUID):
        self.db.query(User).filter(User.id == user_id, User.is_active.is_(True)).update({"is_active": False})
        self.db.commit()

    def get_referral_code_stats(self) -> list[tuple[str, int]]:
        normalized_referral_code = func.coalesce(
            func.nullif(func.trim(User.referral_code), ""),
            UNKNOWN_REFERRAL_CODE,
        )
        rows = (
            self.db.query(normalized_referral_code, func.count(User.id))
            .filter(User.is_active.is_(True))
            .group_by(normalized_referral_code)
            .order_by(func.count(User.id).desc(), normalized_referral_code.asc())
            .all()
        )
        return [(referral_code, total_users) for referral_code, total_users in rows]