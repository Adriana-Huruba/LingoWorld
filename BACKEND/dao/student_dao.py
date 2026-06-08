from typing import Optional

class StudentAssignmentDAO:
    @staticmethod
    def get_student_assignments(student_id, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM public.get_student_assignments(%s)",(student_id,))
            return [{
                "assignment_id": r[0], "classroom_id": r[1], "worksheet_id": r[2], "title": r[3],
                "due_date": r[4].isoformat() if r[4] else None,
                "classroom_name": r[5], "exercise_count": r[6], "completed_count": r[7],
                "is_completed": r[7] >= r[6] if r[6] > 0 else False,
            } for r in cur.fetchall()]

    @staticmethod
    def get_assignment_exercises(assignment_id, student_id, conn) -> Optional[dict]:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "SELECT * FROM public.get_assignment_exercises(%s, %s)",(assignment_id, student_id))
                rows = cur.fetchall()
                if not rows:
                    return {"worksheet_id": None, "title": None, "exercises": []}
                
                first = rows[0]
                return {
                    "worksheet_id": first[5],
                    "title": first[6],
                    "exercises": [{
                        "exercise_id": r[0], "type": r[1], "content": r[2], "elo_difficulty": r[3], "is_correct": r[4],
                    } for r in rows]
                }
            except Exception as e:
                if "not accessible" in str(e).lower():
                    return None
                raise