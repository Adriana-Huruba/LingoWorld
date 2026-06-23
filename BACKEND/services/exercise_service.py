from typing import Optional

from entities.exercise import Exercise
from repository.exercise_repository import ExerciseRepository
from services.agent_service import run_exercise_agent


CEFR_TO_ELO: dict[str, int] = {
    "A1": 200, 
    "A2": 450, 
    "B1": 700,
    "B2": 900, 
    "C1": 1100,
    "C2": 1300,
}

VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
VALID_TYPES  = {"multiple-choice", "fill-in-the-blank", "translation", "match"}

def cefr_to_elo_difficulty(level):
    return CEFR_TO_ELO.get(level, 200)

def _validate(topic, level, exercise_type):
    if not topic or not topic.strip():
        raise ValueError("Topic can't be empty.")
    if len(topic) > 200:
        raise ValueError("Topic can't be longer then 200 characters.")
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid level '{level}'. Accepted levels: {sorted(VALID_LEVELS)}")
    if exercise_type not in VALID_TYPES:
        raise ValueError(f"Type of exercise is invalid: '{exercise_type}'. Accepted types: {sorted(VALID_TYPES)}")


def get_or_generate_exercise(user_id, topic, level, language, exercise_type: str = "multiple-choice", skill_type: Optional[str] = None, native_language: str = "romanian", conn=None) -> Optional[Exercise]:
    _validate(topic, level, exercise_type)

    if conn:
        existing = ExerciseRepository.find_new(
            user_id=user_id,
            user_elo=cefr_to_elo_difficulty(level),
            target_levels=[level],
            language=language.lower(),
            skill_type=skill_type,
            topic=topic,
            conn=conn,
        )
        if existing:
            existing.reason = "from_database"
            return existing

    result = run_exercise_agent(user_id, topic, level, exercise_type, language, skill_type, native_language, conn)
    if not result:
        return None

    return Exercise.from_row({**result, "reason": "newly_generated"})


_CEFR_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

def _zpd_levels(level: str) -> list[str]:
    """Return the user's current CEFR level plus one above (ZPD zone)"""
    try:
        idx = _CEFR_ORDER.index(level.upper())
    except ValueError:
        return _CEFR_ORDER
    result = [_CEFR_ORDER[idx]]
    if idx + 1 < len(_CEFR_ORDER):
        result.append(_CEFR_ORDER[idx + 1])
    return result

def get_all_topics(conn, language: str = None, level: str = None) -> list[str]:
    levels = _zpd_levels(level) if level else None
    return ExerciseRepository.get_all_topics(conn, language=language, levels=levels)