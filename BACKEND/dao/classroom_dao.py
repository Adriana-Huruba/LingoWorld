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
            cur.execute("CALL get_classrooms_by_teacher(%s)", (teacher_id,)) # to do: stored procedure!
            classrooms = cur.fetchall()
            return [{"id": c[0], "name": c[1], "invite_code": c[2]} for c in classrooms]
        except Exception as e:
            print(f"DAO classroom error: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_classroom_by_id(classroom_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("CALL get_classroom_by_id(%s)", (classroom_id,)) # to do: stored procedure
            classroom = cur.fetchone()
            if classroom:
                return {"id": classroom[0], "name": classroom[1], "invite_code": classroom[2]}  
            return None
        except Exception as e:
            print(f"DAO classroom error: {e}")
            return None

    @staticmethod
    def get_students_by_classroom(classroom_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("CALL get_students_by_classroom(%s)", (classroom_id,)) # to do: stored procedure
            students = cur.fetchall()
            return [{"id": s[0], "name": s[1], "email": s[2]} for s in students]
        except Exception as e:
            print(f"DAO classroom students error: {e}")
            return []
        finally:
            cur.close()
            conn.close()