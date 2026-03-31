from fastapi import FastAPI,  HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.vector_service import search_similar
from services.llm_service import generate_exercises
from core.embeddings import create_embedding

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExerciseRequest(BaseModel):
    topic: str
    category: str = "general"
    level: str = "B2"          
    type: str = "multiple choice" # implicit, if not specified in Angular
    language: str = "english" # implicit, if not specified in Angular

@app.get("/")
async def root():
    return {"message": "Communication with Angular frontend successful!"}

@app.post("/generate-exercise")
async def get_exercise(request: ExerciseRequest):
    try:
        print(f"Sent request for topic: {request.topic}")
        
        # retrieval - looking in qdrant for relevant chunks from the textbook
        vector = create_embedding(request.topic)
        relevant_chunks = search_similar(vector)
        
        if not relevant_chunks:
            raise HTTPException(status_code=404, detail="Did not find relevant content for the given topic!")

        # generation - sending the chunks to LLM to generate the exercise
        exercise_json_text = generate_exercises(
            context_chunks=relevant_chunks, 
            topic=request.topic, 
            level=request.level, 
            type=request.type,
            language='english'
        )
        
        return {
            "topic": request.topic,
            "exercise": exercise_json_text,
            "sources_count": len(relevant_chunks)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)