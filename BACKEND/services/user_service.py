from core.database import get_db_connection
from core.security import get_password_hash, verify_password, create_access_token
from dao.exercise_dao import ExerciseDAO
from repository.user_repository import UserRepository

_CEFR_LEVELS: dict[str, tuple[int, int]] = {
    "A1": (0, 400), "A2": (400, 600), "B1": (600, 800),
    "B2": (800, 1000), "C1": (1000, 1200), "C2": (1200, 1600),
}

def _elo_to_cefr(elo: int) -> str:
    for level, (low, high) in _CEFR_LEVELS.items():
        if low <= elo < high:
            return level
    return "C2"


class UserService:
    @staticmethod
    def register_user(user_data: dict) -> bool:
        try:
            password = user_data.get("password")
            if not password or not isinstance(password, str):
                print("Service error: password is required and must be a string")
                return False

            if len(password.encode("utf-8")) > 72:
                print("Service error: password cannot be longer than 72 bytes")
                return False

            return UserRepository.create(
                name=user_data.get("name"),
                email=user_data.get("email"),
                password_hash=get_password_hash(password),
                role=user_data.get("role"),
                native_language=user_data.get("native_language", ""),
                target_language=user_data.get("target_language", ""),
            )
        except Exception as e:
            print(f"Service error: {e}")
            return False

    @staticmethod
    def login_user(email: str, password: str) -> dict | None:
        try:
            user = UserRepository.get_by_email(email)
            if not user:
                print(f"Login error: user with email {email} not found")
                return None

            if not verify_password(password, user.password_hash):
                print("Login error: incorrect password")
                return None

            result = user.to_dict()

            # Enrich with current ELO/level if user has completed the initial quiz
            conn = get_db_connection()
            if conn:
                try:
                    rs_data = ExerciseDAO.get_user_for_rs(user.user_id, conn)
                    if rs_data:
                        result["level"] = _elo_to_cefr(rs_data["elo_score"])
                        result["elo_score"] = rs_data["elo_score"]
                        result["xp"] = rs_data.get("xp_total") or rs_data.get("xp")
                except Exception as e:
                    print(f"[UserService.login_user] Could not fetch RS data: {e}")
                finally:
                    conn.close()

            result["token"] = create_access_token({"sub": str(user.user_id), "role": user.role})
            return result
        except Exception as e:
            print(f"Service error: {e}")
            return None
