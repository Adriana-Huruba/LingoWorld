from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_id: int
    name: str
    email: str
    role: str
    native_language: str
    target_language: str
    password_hash: Optional[str] = None
    level: Optional[str] = None
    elo_score: Optional[int] = None
    xp: Optional[int] = None
    total_responses: Optional[int] = None

    @staticmethod
    def from_row(row: dict) -> "User":
        return User(
            user_id=row.get("user_id") or row.get("id"),
            name=row.get("name", ""),
            email=row.get("email", ""),
            role=str(row.get("role", "")),
            native_language=row.get("native_language", "") or "",
            target_language=row.get("target_language", "") or "",
            password_hash=row.get("password_hash"),
            level=row.get("level") or row.get("current_level"),
            elo_score=row.get("elo_score"),
            xp=row.get("xp_total") or row.get("xp"),
            total_responses=row.get("total_responses"),
        )

    def to_dict(self) -> dict:
        """Returns a client-safe dict (no password_hash)."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "native_language": self.native_language,
            "target_language": self.target_language,
            "level": self.level,
            "elo_score": self.elo_score,
            "xp": self.xp,
            "total_responses": self.total_responses,
        }
