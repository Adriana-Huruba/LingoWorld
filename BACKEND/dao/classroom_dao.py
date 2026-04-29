from core.database import get_db_connection

class ClassroomDAO:
    @staticmethod
    def create_classroom_db(name, teacher_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("CALL create_classroom(%s, %s, %s)", (name, teacher_id, None))
            invite_code = cur.fetchone()[0]
            conn.commit()
            return invite_code
        except Exception as e:
            print(f"DAO Classroom Error: {e}")
            conn.rollback()
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_classrooms_by_teacher(teacher_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, invite_code FROM classrooms WHERE teacher_id = %s", (teacher_id,))
            classrooms = cur.fetchall()
            return [{"id": c[0], "name": c[1], "invite_code": c[2]} for c in classrooms]
        except Exception as e:
            print(f"DAO classroom error: {e}")
            return []
        finally:
            cur.close()
            conn.close()