from core.embeddings import create_embedding
from services.vector_service import search_similar
from services import llm_service

def generate_exercises(topic, level, exercise_type="multiple-choice"):

    query_vector = create_embedding(topic).tolist()
    hits = search_similar(query_vector, topic=topic)
    
    # if it doesn't find anything, use an empty text/fallback
    if not hits:
        print(f"Did not find relevant content for topic: {topic}")
        hits = [] 
    context = "\n".join([hit.payload["text"] for hit in hits])
    
    # sending context to LLM to generate the exercise
    exercises = llm_service.generate_exercises(context, topic, level, exercise_type)

    return exercises