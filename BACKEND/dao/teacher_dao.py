import json
from typing import Optional

class TeacherDAO:
    @staticmethod
    def insert_manual(teacher_id, filename, title, language, level, total_pages, total_chunks, chapters, conn, file_hash=None) -> int:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM insert_teacher_manual(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (teacher_id, filename, title, language, level, total_pages, total_chunks, json.dumps(chapters), file_hash)
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
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, row))

    @staticmethod
    def delete_manual(manual_id, teacher_id, conn) -> bool:
        with conn.cursor() as cur:
            cur.execute("CALL delete_teacher_manual(%s, %s, NULL)", (manual_id, teacher_id))
            row = cur.fetchone()
            return bool(row[0]) if row else False

    @staticmethod
    def find_manual_by_filename(teacher_id, filename, conn) -> Optional[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT manual_id, title FROM find_manual_by_filename(%s, %s)", (teacher_id, filename))
            row = cur.fetchone()
            if not row:
                return None
            return {"manual_id": row[0], "title": row[1]}

    @staticmethod
    def find_manual_by_hash(teacher_id, file_hash, conn) -> Optional[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT manual_id, title FROM find_manual_by_hash(%s, %s)", (teacher_id, file_hash))
            row = cur.fetchone()
            if not row:
                return None
            return {"manual_id": row[0], "title": row[1]}

    @staticmethod
    def list_manuals_for_teacher(teacher_id, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM public.list_teacher_manuals(%s)", (teacher_id,))
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            result = []
            for r in rows:
                d = dict(zip(columns, r))
                if "uploaded_at" in d and d["uploaded_at"]:
                    d["uploaded_at"] = d["uploaded_at"].isoformat()
                result.append(d)
            return result


    @staticmethod
    def publish_worksheet_from_items(teacher_id, manual_id, classroom_id, title, items, language, level, source_manual, due_date, config, conn,) -> dict:
        with conn.cursor() as cur:
            cur.execute("SELECT worksheet_id, assignment_id, exercise_count FROM publish_worksheet(%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s::jsonb)",
                (teacher_id, manual_id, classroom_id, title, json.dumps(items), language, level, source_manual, due_date, json.dumps(config),)
            )
            row = cur.fetchone()
            conn.commit()
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, row))

    @staticmethod
    def list_worksheets_for_teacher(teacher_id, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM list_teacher_worksheets(%s)", (teacher_id,))
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            result = []
            for r in rows:
                d = dict(zip(columns, r))
                for date_col in ("due_date", "created_at", "published_at"):
                    if date_col in d and d[date_col]:
                        d[date_col] = d[date_col].isoformat()
                result.append(d)
            return result

    @staticmethod
    def get_worksheet_progress(worksheet_id, teacher_id, conn) -> Optional[dict]:
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT * FROM get_worksheet_progress(%s, %s)", (worksheet_id, teacher_id))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                students = []
                for r in rows:
                    d = dict(zip(columns, r))
                    if "accuracy" in d and d["accuracy"] is not None:
                        d["accuracy"] = float(d["accuracy"])
                    if "avg_response_time" in d and d["avg_response_time"] is not None:
                        d["avg_response_time"] = float(d["avg_response_time"])
                    students.append(d)
                return {"worksheet_id": worksheet_id, "students": students}
            except Exception as e:
                if "not owned" in str(e).lower() or "not found" in str(e).lower():
                    return None
                raise