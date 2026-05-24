import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from dao.exercise_dao import ExerciseDAO
from repository.exercise_repository import ExerciseRepository
from services.agent_service import run_exercise_agent

"""
Recommender system using ELO Rating, ZPD(Zone of Proximal Development) and Spaced Repetition (SM-2)
"""

CEFR_TO_ELO: dict[str, int] = {
    "A1": 200, 
    "A2": 500, 
    "B1": 700,
    "B2": 900,
    "C1": 1100,
    "C2": 1400
}
 
CEFR_LEVELS: dict[str, tuple[int, int]] = {
    "A1": (0, 400),  
    "A2": (400, 600),
    "B1": (600, 800), 
    "B2": (800, 1000),
    "C1": (1000, 1200), 
    "C2": (1200, 1600)
}

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
# ELO_DEFAULT = 200
ELO_K_NEW = 32  # K-factor for new users(quiz < 20 questions)
ELO_K_STABLE = 16   # K-factor after stabilization
EXPECTED_TIME_PER_TYPE = {
    "multiple-choice": 8,
    "gap_fill": 20,
    "translation": 35,
}
  
def elo_expected_score(user_elo, item_elo):
    return 1.0 / (1.0 + 10.0 ** ((item_elo - user_elo) / 400.0))
 
 
def calculate_new_elo(user_elo, item_elo, correct, total_responses):
    k = ELO_K_NEW if total_responses < 20 else ELO_K_STABLE

    expected = elo_expected_score(user_elo, item_elo)
    actual = 1.0 if correct else 0.0
    new_elo = user_elo + k * (actual - expected)

    return max(0, min(1600, round(new_elo)))
 
def elo_to_cefr(elo): # mapping elo to cefr level
    for level, (low, high) in CEFR_LEVELS.items():
        if low <= elo < high:
            return level
    return "C2"
 
def cefr_to_elo(level):
    return CEFR_TO_ELO.get(level, 200) # default for A1 
 
#  ZPD
def get_target_levels(user_elo):
    current_level = elo_to_cefr(user_elo)
    idx = CEFR_ORDER.index(current_level)
    low, high = CEFR_LEVELS[current_level]
 
    position = (user_elo - low) / (high - low) if high > low else 0.5
    levels   = [current_level]

    if position >= 0.80 and idx < len(CEFR_ORDER) - 1:
        levels.append(CEFR_ORDER[idx + 1])
 
    if position <= 0.20 and idx > 0:
        levels.append(CEFR_ORDER[idx - 1])
 
    return levels
 

# SM-2 for spaced repetition - scheduling of exercises - based on user performance
def estimate_quality(is_correct, used_hint, response_time, exercise_type) -> int:
    """
    Estimating quality of response= q between 1-5 (from SM-2) from:
    -is_correct
    -used_hint
    -time for an ex
   
    Normalization:
      ratio < 0.5 -fast (possibly guessed)
      ratio 0.5-1 -normal
      ratio 1-2 -slow
      ratio > 2 -very slow
    """
    expected = EXPECTED_TIME_PER_TYPE.get(exercise_type, 15)
    ratio = response_time / expected 

    if not is_correct:
        if ratio < 1.0:
            return 2  
        return 1 

    if used_hint:
        return 3     

    if ratio < 0.5:   
        return 5  
    if ratio < 1.0:   
        return 4  
    if ratio < 2.0:   
        return 3 
    return 2                    

def calculate_next_review_sm2(is_correct, used_hint, response_time, exercise_type, consecutive_correct, easiness_factor, last_interval):
    q = estimate_quality(is_correct, used_hint, response_time, exercise_type)

    if q < 3:
        new_interval = 1
        new_ef = easiness_factor 
    else:
        if consecutive_correct == 0:
            new_interval = 1
        elif consecutive_correct == 1:
            new_interval = 6
        else:
            new_interval = round(last_interval * easiness_factor)

        new_ef = easiness_factor + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        new_ef = max(1.3, new_ef) 

    next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)
    return next_review, new_ef, new_interval, q
 
def _find_exercise_in_db(user_id, user_elo, target_levels, language, skill_type, topic, conn):
    exercise = ExerciseRepository.find_spaced_repetition( user_id, user_elo, target_levels, language, skill_type, topic, conn)
    if exercise:
        print(f"[RS] branch: spaced_repetition")
        return exercise

    exercise = ExerciseRepository.find_new(user_id, user_elo, target_levels, language, skill_type, topic, conn)
    if exercise:
        print(f"[RS] branch: find_new")
        return exercise

    return None 

# rs
def get_next_exercise(user_id: int, target_language: str, conn, skill_type: Optional[str] = None, topic: Optional[str] = None):
    user = ExerciseDAO.get_user_for_rs(user_id, conn)
    if not user:
        print(f"[RS] user_id={user_id} does not exist in db or did not complete the quiz")
        return None

    user_elo = user["elo_score"]
    total_responses = user["total_responses"]
    target_levels = get_target_levels(user_elo)
    primary_level = elo_to_cefr(user_elo)

    exercise = _find_exercise_in_db(user_id, user_elo, target_levels, target_language, skill_type, topic, conn)
    if exercise:
        return exercise.to_dict() if hasattr(exercise, "to_dict") else exercise

    print(f"[RS] Agent is generating new ex")
    result = run_exercise_agent(
        user_id=user_id,
        topic=topic or "general",
        level=primary_level,
        exercise_type="multiple-choice",
        language=target_language,
        skill_type=skill_type,
        conn=conn,
    )
    if result:
        result["reason"] = "newly_generated"
        print(f"[RS] Agent generated new ex with id={result.get('exercise_id')}")
        return result

    print(f"[RS] Agent failed - reinforcement from DB")
    exercise = ExerciseRepository.find_reinforcement(user_id, user_elo, target_levels, target_language, skill_type, topic, conn)
    if exercise:
        return exercise.to_dict() if hasattr(exercise, "to_dict") else exercise

    print(f"[RS] No ex available")
    return None
 
 
def record_answer(user_id: int, exercise_id: int,  is_correct: bool, response_time_seconds: int, exercise_type: str, used_hint: bool, conn, assignment_id: Optional[int] = None,) -> dict:
    user = ExerciseDAO.get_user_for_rs(user_id, conn)
    exercise = ExerciseDAO.find_by_id(exercise_id, conn)
    prev = ExerciseDAO.get_last_progress(user_id, exercise_id, conn)
 
    current_elo =user["elo_score"]
    total_responses = user["total_responses"]
    item_elo = exercise["elo_difficulty"] or cefr_to_elo(exercise["level"])
    ex_type = exercise_type or exercise["type"]
 
    # SM-2 state from prev answer
    prev_consecutive = 0
    prev_ef = 2.5
    prev_interval = 1
    if prev:
        prev_ef = prev.get("easiness_factor") or 2.5
        prev_interval = prev.get("last_interval")   or 1
        prev_consecutive = (prev.get("consecutive_correct") or 0) \
        if prev.get("is_correct") else 0
 
    # elo
    new_elo  = calculate_new_elo(current_elo, item_elo, is_correct, total_responses)
    new_cefr = elo_to_cefr(new_elo)
 
    # SM-2
    new_consecutive = (prev_consecutive + 1) if is_correct else 0
 
    next_review, new_ef, new_interval, quality = calculate_next_review_sm2(
        is_correct=is_correct,
        used_hint=used_hint,
        response_time=response_time_seconds,
        exercise_type=ex_type,
        consecutive_correct=prev_consecutive,
        easiness_factor=prev_ef,
        last_interval=prev_interval,
    )
 
    attempt_num = ExerciseDAO.get_attempt_number(user_id, exercise_id, conn)
 
    # XP 
    expected_time = EXPECTED_TIME_PER_TYPE.get(ex_type, 15)
    if is_correct and response_time_seconds < expected_time * 0.5:
        xp_gained = 15
    elif is_correct:
        xp_gained = 10
    else:
        xp_gained= 0
 
    ExerciseDAO.save_response(
        user_id=user_id,
        exercise_id=exercise_id,
        assignment_id=assignment_id,
        is_correct=is_correct,
        xp_gained=xp_gained,
        response_time_seconds=response_time_seconds,
        next_review_at=next_review,
        consecutive_correct=new_consecutive,
        attempt_number=attempt_num,
        easiness_factor=new_ef,
        last_interval=new_interval,
        quality=quality,
        used_hint=used_hint,
        new_elo=new_elo,
        new_cefr=new_cefr,
        new_total_responses=total_responses + 1,
        new_xp=xp_gained,
        conn=conn,
    )
 
    return {
        "old_elo": current_elo,
        "new_elo": new_elo,
        "delta_elo": new_elo - current_elo,
        "new_cefr": new_cefr,
        "level_changed": new_cefr != elo_to_cefr(current_elo),
        "next_review": next_review.isoformat(),
        "new_interval": new_interval,
        "quality": quality,
        "xp_gained": xp_gained,
    }
 

def complete_initial_quiz(user_id: int, responses: list[dict], conn) -> dict:
    from services.initial_quiz_service import submit_quiz_results
    return submit_quiz_results(user_id, responses, conn)