import json
from typing import Optional

class TeacherDAO:
    @staticmethod
    def insert_manual(teacher_id, filename, title, language, level, total_pages, total_chunks, chapters, conn) -> int:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM insert_teacher_manual(%s, %s, %s, %s, %s, %s, %s, %s)",
                (teacher_id, filename, title, language, level, total_pages, total_chunks, json.dumps(chapters))
            )
            return cur.fetchone()[0]

    @staticmethod
    def mark_manual_processed(manual_id, conn):
        with conn.cursor() as cur:
            cur.execute("CALL mark_manual_processed(%s)", (manual_id,))

    @staticmethod
    def get_manual(manual_id, teacher_id, conn) -> Optional[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM get_teacher_manual(%s, %s)", (manual_id, teacher_id))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "manual_id": row[0], "title": row[1], "filename": row[2],
                "language": row[3], "level": row[4], "total_pages": row[5],
                "chapters": row[6], "is_processed": row[7],
            }

    @staticmethod
    def list_manuals_for_teacher(teacher_id, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM public.list_teacher_manuals(%s)", (teacher_id,))
            return [{
                "manual_id": r[0], "title": r[1], "filename": r[2],
                "language": r[3], "level": r[4], "total_pages": r[5],
                "is_processed": r[6],
                "uploaded_at": r[7].isoformat() if r[7] else None,
            } for r in cur.fetchall()]


    @staticmethod
    def publish_worksheet_from_items(teacher_id, manual_id, classroom_id, title, items, language, level, source_manual, due_date, config, conn,) -> dict:
        with conn.cursor() as cur:
            cur.execute("SELECT worksheet_id, assignment_id, exercise_count FROM publish_worksheet(%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s::jsonb)",
                (teacher_id, manual_id, classroom_id, title, json.dumps(items), language, level, source_manual, due_date, json.dumps(config),)
            )
            row = cur.fetchone()
            conn.commit()
            return {
                "worksheet_id": row[0],
                "assignment_id": row[1],
                "exercise_count": row[2],
            }

    @staticmethod
    def list_worksheets_for_teacher(teacher_id, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM list_teacher_worksheets(%s)",(teacher_id,))
            
            return [{
                "worksheet_id": r[0], "title": r[1],
                "due_date": r[2].isoformat() if r[2] else None,
                "created_at": r[3].isoformat() if r[3] else None,
                "published_at": r[4].isoformat() if r[4] else None,
                "manual_title": r[5], "classroom_name": r[6],
                "exercise_count": r[7],
            } for r in cur.fetchall()]

    @staticmethod
    def get_worksheet_progress(worksheet_id, teacher_id, conn) -> Optional[dict]:
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT * FROM get_worksheet_progress(%s, %s)",(worksheet_id, teacher_id))
                rows = cur.fetchall()
                return {
                    "worksheet_id": worksheet_id,
                    "students": [{
                        "student_id": r[0], "student_name": r[1],
                        "elo_score": r[2], "current_level": r[3],
                        "total_exercises": r[4], "correct": r[5],
                        "total_attempts": r[6],
                        "accuracy": float(r[7]) if r[7] else 0,
                        "avg_response_time": float(r[8]) if r[8] else None,
                    } for r in rows]
                }
            except Exception as e:
                if "not owned" in str(e).lower() or "not found" in str(e).lower():
                    return None
                raise