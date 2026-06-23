from typing import Optional

from dao.user_dao import UserDAO
from entities.user import User


class UserRepository:
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Returns a User entity (with password_hash) or None. Used for authentication."""
        row = UserDAO.get_user_by_email(email)
        if not row:
            return None
        # get_user_for_login does not return the email column; inject it from the param
        if not row.get("email"):
            row["email"] = email
        return User.from_row(row)

    @staticmethod
    def create(name: str, email: str, password_hash: str, role: str,
               native_language: str, target_language: str) -> bool:
        return UserDAO.insert_user_via_procedure(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            native_language=native_language,
            target_language=target_language,
        )
