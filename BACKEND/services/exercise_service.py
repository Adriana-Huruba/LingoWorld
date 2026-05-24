from typing import Optional

from entities.exercise import Exercise
from repository.exercise_repository import ExerciseRepository
from core.embeddings import create_embedding
from services.vector_service import search_similar
from services.llm_service import generate_exercises as llm_generate
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

# using the agent (agent_service)
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


# using only llm (llm_service)
# def get_or_generate_exercise(user_id, topic, level, language, exercise_type: str = "multiple-choice", skill_type: Optional[str] = None, conn = None) -> Optional[Exercise]:
#     _validate(topic, level, exercise_type)

#     if conn:
#         existing = ExerciseRepository.find_new(
#             user_id=user_id,
#             user_elo=cefr_to_elo_difficulty(level),
#             target_levels=[level],
#             language=language.lower(),
#             skill_type=skill_type,
#             topic=topic,
#             conn=conn,
#         )
#         if existing:
#             existing.reason = "from_database"
#             return existing

#     query_vector = create_embedding(topic)
#     relevant_chunks = search_similar(vector=query_vector, language=language.lower(), level=level, skill_type=skill_type)

#     if not relevant_chunks:
#         return None

#     raw = llm_generate(context_chunks=relevant_chunks, topic=topic, level=level, type=exercise_type, language=language)

#     try:
#         content = json.loads(raw)
#     except json.JSONDecodeError:
#         return None

#     questions = content.get("questions", [])
#     if not questions:
#         return None

#     exercise_title = content.get("exercise_title", "Exercise")

#     chunk_payload = relevant_chunks[0].payload
#     chunk_skill = chunk_payload.get("skill_type", skill_type or "general")
#     chunk_topic = chunk_payload.get("topic", topic)
#     chunk_source = chunk_payload.get("source", "")
#     elo_diff = cefr_to_elo_difficulty(level)

#     saved_exercises = [] # each ex saved separately

#     if conn:
#         for q in questions:
#             single_content = {
#                 "exercise_title": exercise_title,
#                 "questions": [q]
#             }
#             correct_ans = q.get("answer", "")

#             ex_id = ExerciseDAO.insert_exercise(
#                 language=language.lower(),
#                 level=level,
#                 exercise_type=exercise_type,
#                 category=chunk_skill,
#                 topic=chunk_topic,
#                 content=single_content,
#                 correct_answer=correct_ans,
#                 elo_difficulty=elo_diff,
#                 source_manual=chunk_source,
#                 conn=conn,
#             )
            
#             if ex_id:
#                 saved_exercises.append({
#                     "id": ex_id,
#                     "content": single_content,
#                     "correct_answer": correct_ans
#                 })

#     if not saved_exercises:
#         return None

#     first_ex = saved_exercises[0]
#     return Exercise(
#         exercise_id=first_ex["id"],
#         language=language.lower(),
#         level=level,
#         type=exercise_type,
#         category=chunk_skill,
#         topic=chunk_topic,
#         content=first_ex["content"],
#         correct_answer=first_ex["correct_answer"],
#         elo_difficulty=elo_diff,
#         source_manual=chunk_source,
#         reason="newly_generated",
#     )


def get_all_topics(conn) -> list[str]:
    return ExerciseRepository.get_all_topics(conn)