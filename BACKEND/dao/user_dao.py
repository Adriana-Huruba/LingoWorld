import psycopg2
from core.database import get_db_connection 

class UserDAO:
    @staticmethod
    def insert_user_via_procedure(name, email, password_hash, role, native_language, target_language):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("CALL register_user(%s, %s, %s, %s, %s, %s)", (name, email, password_hash, role, native_language, target_language))
            conn.commit()
            return True
        except Exception as e:
            print(f"DAO error: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_user_by_email(email):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM get_user_for_login(%s)", (email,))
            user = cur.fetchone()
            return user
        except Exception as e:
            print(f"DAO error: {e}")
            return None
        finally:
            cur.close()
            conn.close()