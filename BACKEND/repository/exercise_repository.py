from typing import Optional
from entities.exercise import Exercise
from dao.exercise_dao import ExerciseDAO

class ExerciseRepository:
    @staticmethod
    def find_by_id(exercise_id: int, conn) -> Optional[Exercise]:
        row = ExerciseDAO.find_by_id(exercise_id, conn)
        return Exercise.from_row(row) if row else None

    @staticmethod
    def find_for_quiz(language: str, conn) -> list[Exercise]:
        rows = ExerciseDAO.get_quiz_exercises(language, conn)
        return [Exercise.from_row(r) for r in rows]

    @staticmethod
    def find_spaced_repetition(user_id, user_elo, target_levels, language, skill_type, topic, conn) -> Optional[Exercise]:
        row = ExerciseDAO.find_spaced_repetition(
            user_id, user_elo, target_levels, language, skill_type, topic, conn)
        return Exercise.from_row(row) if row else None

    @staticmethod
    def find_new(user_id, user_elo, target_levels,language, skill_type, topic, conn) -> Optional[Exercise]:
        row = ExerciseDAO.find_new(
            user_id, user_elo, target_levels, language, skill_type, topic, conn)
        return Exercise.from_row(row) if row else None

    @staticmethod
    def find_reinforcement(user_id, user_elo, target_levels, language, skill_type, topic, conn) -> Optional[Exercise]:
        row = ExerciseDAO.find_reinforcement(
            user_id, user_elo, target_levels, language, skill_type, topic, conn)
        return Exercise.from_row(row) if row else None

    @staticmethod
    def save(language, level, exercise_type, category, topic,content, correct_answer, elo_difficulty, source_manual, conn) -> Optional[int]:
        return ExerciseDAO.insert_exercise(
            language, level, exercise_type, category, topic,
            content, correct_answer, elo_difficulty, source_manual, conn)
    
    @staticmethod
    def get_all_topics(conn) -> list[str]:
        return ExerciseDAO.get_all_topics(conn)