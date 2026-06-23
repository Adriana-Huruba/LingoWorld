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
            cur.execute("SELECT * FROM get_classrooms_by_teacher(%s)", (teacher_id,))
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
    def save_worksheet_completion(student_id, worksheet_id, score, total):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("CALL save_worksheet_completion_proc(%s, %s, %s, %s)", (student_id, worksheet_id, score, total))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"DAO save_worksheet_completion error: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_student_progress_for_classroom(classroom_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM get_classroom_student_progress(%s)", (classroom_id,))
            rows = cur.fetchall()
            return [{"id": r[0], "name": r[1], "email": r[2], 
                     "exercises_attempted": r[3], "exercises_correct": r[4],
                     "elo_current": r[5], "xp": r[6], 
                     "assignments_done": r[7]} for r in rows] 
        except Exception as e:
            print(f"DAO get_student_progress_for_classroom error: {e}")
            return []
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
            cur.execute("SELECT * FROM  get_classroom_assignments_data(%s)", (classroom_id,))
            rows = cur.fetchall()

            worksheets = {}
            for row in rows:
                worksheet_id = row[0]
                if worksheet_id not in worksheets:
                    worksheets[worksheet_id] = {
                        "id": worksheet_id,
                        "title": row[1],
                        "due_date": row[2].isoformat() if row[2] else None,
                        "status": "pending",
                        "questions": []
                    }

                content  = row[4] or {}
                correct  = row[5] or ""
                db_type  = (row[6] or "").lower()

                if db_type in ("translation", "fill-in-the-blank", "multiple-choice", "match"):
                    ex_type = db_type
                elif content.get("pairs"):
                    ex_type = "match"
                elif content.get("options"):
                    ex_type = "multiple-choice"
                elif content.get("base_sentence"):
                    q_text = content.get("question", "").lower()
                    ex_type = "translation" if "translat" in q_text else "fill-in-the-blank"
                else:
                    ex_type = "multiple-choice"

                exercise_id = row[3]

                if ex_type == "match":
                    worksheets[worksheet_id]["questions"].append({
                        "exercise_id": exercise_id,
                        "type": "match",
                        "exercise_title": content.get("exercise_title", ""),
                        "pairs": content.get("pairs", []),
                        "answer": correct,
                    })
                elif ex_type in ("translation", "fill-in-the-blank"):
                    worksheets[worksheet_id]["questions"].append({
                        "exercise_id": exercise_id,
                        "type": ex_type,
                        "exercise_title": content.get("exercise_title", ""),
                        "base_sentence": content.get("base_sentence", ""),
                        "question": content.get("question", ""),
                        "answer": correct,
                        "options": [],
                    })
                else:
                    if "questions" in content:
                        q = content["questions"][0] if content["questions"] else {}
                        question_text = q.get("question", "")
                        options = q.get("options", [])
                    else:
                        question_text = content.get("question", "")
                        options = content.get("options", [])
                    worksheets[worksheet_id]["questions"].append({
                        "exercise_id": exercise_id,
                        "type": "multiple-choice",
                        "exercise_title": content.get("exercise_title", ""),
                        "question": question_text,
                        "options": options,
                        "answer": correct,
                    })

            return list(worksheets.values())
        except Exception as e:
            print(f"DAO get_classroom_assignments error: {e}")
            return []
        finally:
            cur.close()
            conn.close()