from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def list_users(self, page: int, limit: int):
        return self.repository.list_users(page=page, limit=limit)

    def get_referral_code_stats(self):
        return self.repository.get_referral_code_stats()

    def create_user(self, payload: UserCreate):
        duplicate_field = self.repository.find_duplicate_field(
            email=payload.email,
            phone_number=payload.phone_number,
        )

        if duplicate_field == "email":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã tồn tại")
        if duplicate_field == "phone_number":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Số điện thoại đã tồn tại")

        try:
            return self.repository.create_user(payload)
        except IntegrityError as exc:
            error_text = str(exc.orig)

            if "ix_waiting_list_users_email" in error_text:
                detail = "Email đã tồn tại"
            elif "ix_waiting_list_users_phone_number" in error_text:
                detail = "Số điện thoại đã tồn tại"
            else:
                detail = "Dữ liệu bị trùng với bản ghi đã tồn tại"

            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
        
    def delete_user(self, user_id: UUID):
        user = self.repository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User không tồn tại")
        self.repository.delete_user(user_id)