from dao.user_dao import UserDAO
from core.security import get_password_hash, verify_password

class UserService:
    @staticmethod
    def register_user(user_data):
        try:
            password = user_data.get('password')
            if not password or not isinstance(password, str):
                print("Service Error: password is required and must be a text value")
                return False

            password_bytes = password.encode("utf-8")
            if len(password_bytes) > 72:
                print("Service Error: password cannot be longer than 72 bytes, truncate manually if necessary")
                return False

            hashed_password = get_password_hash(password)
            
            success = UserDAO.insert_user_via_procedure(
                name= user_data.get('name'),
                email= user_data.get('email'),
                password_hash= hashed_password,
                role= user_data.get('role'),
                native_language= user_data.get('native_language'),
                target_language= user_data.get('target_language')
            )
            return success
        except Exception as e:
            print(f"Service Error: {e}")
            return False

    @staticmethod
    def login_user(email, password):
        try:
            user = UserDAO.get_user_by_email(email)
            if not user:
                print(f"Login Error: User with email {email} not found.")
                return None # user not found
            
            user_id, name, password_hash, role, native_language, target_language = user
            
            if verify_password(password, password_hash):
                return {
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "role": str(role),
                    "native_language": native_language,
                    "target_language": target_language
                }
            print("Login Error: Incorrect password.")
            return None
        except Exception as e:
            print(f"Service Error: {e}")
            return None