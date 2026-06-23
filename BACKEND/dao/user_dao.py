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
    def get_user_by_email(email) -> dict | None:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM get_user_for_login(%s)", (email,))
            row = cur.fetchone()
            if not row:
                return None
            columns = [desc[0] for desc in cur.description]
            result = dict(zip(columns, row))
            # get_user_for_login returns positional:
            # user_id, name, password_hash, role, native_language, target_language
            # Normalize to canonical keys regardless of what the SQL function names them.
            canonical = ["user_id", "name", "password_hash", "role", "native_language", "target_language"]
            if "user_id" not in result:
                for i, key in enumerate(canonical):
                    if i < len(row):
                        result[key] = row[i]
            return result
        except Exception as e:
            print(f"DAO error: {e}")
            return None
        finally:
            cur.close()
            conn.close()