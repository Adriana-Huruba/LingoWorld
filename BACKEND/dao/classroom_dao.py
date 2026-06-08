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
            cur.execute("SELECT * FROM get_classrooms_by_teacher(%s)", (teacher_id,)) # function- only for READ operations
            classrooms = cur.fetchall()
            return [{"id": c[0], "name": c[1], "invite_code": c[2], "student_count": c[3]} for c in classrooms]
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
            cur.execute("SELECT * FROM get_classroom_by_id(%s)", (classroom_id,))
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
            cur.execute("SELECT * FROM get_students_by_classroom(%s)", (classroom_id,))
            students = cur.fetchall()
            return [{"id": s[0], "name": s[1], "email": s[2], "elo_score":s[3], "xp": s[4]} for s in students]
        except Exception as e:
            print(f"DAO classroom students error: {e}")
            return []
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def enroll_student(student_id, invite_code):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("CALL enroll_student_by_code(%s, %s)", (student_id, invite_code))
            conn.commit()
            return True, 'Enrolling succesful'
        except Exception as e:
            conn.rollback()
            error_message = str(e).split('\n')[0] 
            print(f"DAO classroom enroll students error: {error_message}")
            return False, error_message
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_classrooms_by_student(student_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM get_classrooms_by_student(%s)", (student_id,))
            classrooms = cur.fetchall()
            
            return [ { "id": c[0], "name": c[1], "invite_code": c[2], "teacher_name": c[3] } for c in classrooms]
        except Exception as e:
            print(f"DAO classroom student error: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_classroom_assignments(classroom_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM  get_classroom_assignments(%s)", (classroom_id,))
            rows = cur.fetchall()

            worksheets = {}
            for row in rows:
                worksheet_id = row[0]
                if  worksheet_id not in worksheets:
                    worksheets[ worksheet_id] = {
                        "id": worksheet_id, "title": row[1],
                        "due_date": row[2].isoformat() if row[2] else None,
                        "status": row[3] or "pending",
                        "questions": []
                    }
                content = row[5]
                q = content.get("questions", [{}])[0] if content else {}
                worksheets[worksheet_id]["questions"].append({
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "answer": row[6]
                })
            
            return list(worksheets.values())
        except Exception as e:
            print(f"DAO get_classroom_assignments error: {e}")
            return []
        finally:
            cur.close()
            conn.close()