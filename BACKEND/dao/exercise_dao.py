import json
from typing import Optional

class ExerciseDAO:
    @staticmethod
    def insert_exercise(language, level, exercise_type, category, topic, content, correct_answer, elo_difficulty, source_manual, conn) -> Optional[int]:
        try:
            with conn.cursor() as cur:
                cur.execute("CALL insert_exercise(%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,NULL)", (
                    language, level, exercise_type, category, topic, json.dumps(content), correct_answer, elo_difficulty, source_manual,
                ))
                conn.commit()
                row = cur.fetchone()
                
                return row[0] if row else None 
                
        except Exception as e:
            conn.rollback()
            print(f"[ExerciseDAO.insert_exercise] {e}")
            return None

    @staticmethod
    def find_by_id(exercise_id: int, conn) -> Optional[dict]:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_exercise_by_id(%s)", [exercise_id])
                row = cur.fetchone()
                if not row: 
                    return None
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        except Exception as e:
            print(f"[ExerciseDAO.find_by_id] {e}")
            return None

    @staticmethod
    def get_quiz_exercises(language: str, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM get_quiz_exercises(%s)", [language])
            
            columns = [desc[0] for desc in cur.description]
            
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    @staticmethod
    def find_spaced_repetition(user_id, user_elo, levels, language, skill_type, topic, conn) -> Optional[dict]:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_spaced_repetition_exercise(%s,%s,%s,%s,%s,%s)",
                    (user_id, user_elo, levels, language, skill_type, topic)
                )
                row = cur.fetchone()
                if not row: 
                    return None
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        except Exception as e:
            print(f"[ExerciseDAO.find_spaced_repetition] {e}")
            return None

    @staticmethod
    def find_new(user_id, user_elo, levels, language, skill_type, topic, conn) -> Optional[dict]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM get_new_exercise(%s,%s,%s,%s,%s,%s)",
                    (user_id, user_elo, levels, language, skill_type, topic)
                )
                row = cur.fetchone()
                if not row: 
                    return None
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        except Exception as e:
            print(f"[ExerciseDAO.find_new] {e}")
            return None

    @staticmethod
    def find_reinforcement(user_id, user_elo, levels, language, skill_type, topic, conn) -> Optional[dict]:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_reinforcement_exercise(%s,%s,%s,%s,%s,%s)",
                    (user_id, user_elo, levels, language, skill_type, topic)
                )
                row = cur.fetchone()
                if not row: 
                    return None
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        except Exception as e:
            print(f"[ExerciseDAO.find_reinforcement] {e}")
            return None

    @staticmethod
    def get_user_for_rs(user_id: int, conn) -> Optional[dict]:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_user_for_rs(%s)", (user_id,))
                row = cur.fetchone()
                if not row:
                    return None
            
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        except Exception as e:
            print(f"[ExerciseDAO.get_user_for_rs] {e}")
            return None

    @staticmethod
    def get_last_progress(user_id: int, exercise_id: int, conn) -> Optional[dict]:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_last_progress(%s,%s)", (user_id, exercise_id))
                row = cur.fetchone()
                
                if not row:
                    return None
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        except Exception as e:
            print(f"[ExerciseDAO.get_last_progress] {e}")
            return None

    @staticmethod
    def get_attempt_number(user_id: int, exercise_id: int, conn) -> int:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT get_attempt_number(%s,%s) AS n", (user_id, exercise_id)
                )
                row = cur.fetchone()
                return row[0] if row else 1
        except Exception as e:
            print(f"[ExerciseDAO.get_attempt_number] {e}")
            return 1

    @staticmethod
    def save_response(user_id, exercise_id, assignment_id, is_correct, xp_gained, response_time_seconds, next_review_at, consecutive_correct, attempt_number,
        easiness_factor, last_interval, quality, used_hint, new_elo, new_cefr, new_total_responses, new_xp, conn) -> bool:
        try:
            with conn.cursor() as cur:
                cur.execute("CALL save_response(%s::INTEGER, %s::INTEGER, %s::INTEGER, %s::BOOLEAN, %s::INTEGER, %s::INTEGER,"
                " %s::TIMESTAMP WITH TIME ZONE, %s::INTEGER, %s::INTEGER, %s::FLOAT, %s::INTEGER, %s::SMALLINT, %s::BOOLEAN, "
                "%s::INTEGER, %s::VARCHAR(5), %s::INTEGER, %s::INTEGER)", (
                    user_id, exercise_id, assignment_id, is_correct, xp_gained, response_time_seconds, next_review_at, consecutive_correct, attempt_number,
                    easiness_factor, last_interval, quality, used_hint, new_elo, new_cefr, new_total_responses, new_xp
                ))
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"[ExerciseDAO.save_response] {e}")
            return False

    @staticmethod
    def save_initial_quiz_result(user_id, score, estimated_level, starting_elo, conn) -> bool:
        try:
            with conn.cursor() as cur:
                cur.execute("CALL save_initial_quiz_result(%s,%s,%s,%s)",
                    (user_id, score, estimated_level, starting_elo)
                )
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"[ExerciseDAO.save_initial_quiz_result] {e}")
            return False