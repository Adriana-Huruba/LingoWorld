import json
from entities.exercise import Exercise
from repository.exercise_repository import ExerciseRepository
from dao.exercise_dao import ExerciseDAO
from core.embeddings import create_embedding
from services.vector_service import search_similar
from services.llm_service import generate_exercises as llm_generate

CEFR_TO_ELO = {
    "A1": 200, 
    "A2": 450, 
    "B1": 700,
    "B2": 900, 
    "C1": 1100, 
    "C2": 1300,
}

LEVEL_WEIGHTS = {
    "A1": 1, 
    "A2": 2,
    "B1": 3,
    "B2": 4,
    "C1": 5,
    "C2": 6,
}

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

def has_completed_quiz(user_id: int, conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM initial_quiz WHERE user_id = %s", [user_id])
        row = cur.fetchone()
        return (row[0] or 0) > 0


def get_quiz_exercises(language: str, conn) -> list[Exercise]:
    if not language or not language.strip():
        raise ValueError("Language filed can't be empty.")

    exercises = ExerciseRepository.find_for_quiz(language=language.lower(), conn=conn)
    levels_found = {e.level for e in exercises}

    for level in CEFR_ORDER:
        if level not in levels_found:
            generated = _generate_for_level(language, level, conn)
            exercises.extend(generated)

    if not exercises:
        raise ValueError(
            f"There is no content for '{language}'. "
            f"Upload a manual."
        )

    exercises.sort(key=lambda e: CEFR_ORDER.index(e.level) if e.level in CEFR_ORDER else 99)
    return exercises


def _generate_for_level(language: str, level: str, conn) -> list[Exercise]:
    generated = []
    for _ in range(2):
        chunks = search_similar(vector=create_embedding(f"{language} {level} exercise"), language=language.lower(), level=level)
        if not chunks:
            continue

        raw = llm_generate(context_chunks=chunks, topic="general", level=level, type="multiple-choice", language=language)
        try:
            content = json.loads(raw)
        except json.JSONDecodeError:
            continue

        questions = content.get("questions", [])
        correct_ans = questions[0]["answer"] if questions else ""
        payload = chunks[0].payload
        elo_diff = CEFR_TO_ELO.get(level, 200)

        exercise_id = ExerciseRepository.save(
            language=language.lower(), level=level,
            exercise_type="multiple-choice",
            category=payload.get("skill_type", "general"),
            topic=payload.get("topic", "general"),
            content=content, correct_answer=correct_ans,
            elo_difficulty=elo_diff,
            source_manual=payload.get("source", ""),
            conn=conn,
        )

        if exercise_id:
            generated.append(Exercise(
                exercise_id=exercise_id, language=language.lower(),
                level=level, type="multiple-choice",
                category=payload.get("skill_type", "general"),
                topic=payload.get("topic", "general"),
                content=content, correct_answer=correct_ans,
                elo_difficulty=elo_diff,
                source_manual=payload.get("source", ""),
            ))
    return generated

def submit_quiz_results(user_id: int, responses: list[dict], conn) -> dict:
    if not responses:
        raise ValueError("There are no responses to analyze.")

    total_weight = sum(LEVEL_WEIGHTS.get(r.get("level", "A1"), 1) for r in responses)
    earned_weight = sum(
        LEVEL_WEIGHTS.get(r.get("level", "A1"), 1)
        for r in responses if r.get("is_correct", False)
    )

    ratio = earned_weight / total_weight if total_weight > 0 else 0

    if ratio < 0.20:        
        estimated_level = "A1"
    elif ratio < 0.40:      
        estimated_level = "A2"
    elif ratio < 0.60:      
        estimated_level = "B1"
    elif ratio < 0.75:      
        estimated_level = "B2"
    elif ratio < 0.90:      
        estimated_level = "C1"
    else:                   
        estimated_level = "C2"

    starting_elo = CEFR_TO_ELO[estimated_level]

    success = ExerciseDAO.save_initial_quiz_result(
        user_id=user_id,
        score=round(ratio, 4),
        estimated_level=estimated_level,
        starting_elo=starting_elo,
        conn=conn,
    )

    if not success:
        raise Exception("Error at saving quiz results.")

    return {
        "estimated_level": estimated_level,
        "starting_elo": starting_elo,
        "score_percent": round(ratio * 100, 1),
        "correct": sum(1 for r in responses if r.get("is_correct")),
        "total": len(responses),
    }