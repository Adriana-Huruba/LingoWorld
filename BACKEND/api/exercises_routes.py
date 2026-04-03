# endpoints for types of exercises: translation, multiple-choice, fill-in-the-blank, matching, pronunciation

import os
import shutil

from fastapi import APIRouter, File, Form,  HTTPException, UploadFile
from pydantic import BaseModel

from core.ingest_pdf import run_ingestion
from services.vector_service import search_similar
from services.llm_service import generate_exercises
from core.embeddings import create_embedding

exercises_router = APIRouter()

class ExerciseRequest(BaseModel):
    topic: str
    category: str = "general"
    level: str = "B2"          
    type: str = "multiple choice" # implicit, if not specified
    language: str = "english" # implicit, if not specified 

@exercises_router.post("/generate-exercise")
async def get_exercise(request: ExerciseRequest):
    try:
        print(f"Sent request for topic: {request.topic}")
        
        # retrieval - looking in qdrant for relevant chunks from the textbook
        vector = create_embedding(request.topic)
        relevant_chunks = search_similar(vector, language=request.language, category=request.category)
        
        if not relevant_chunks:
            raise HTTPException(status_code=404, detail="Did not find relevant content for the given language and category!")

        # generation - sending the chunks to LLM to generate the exercise
        exercise_json_text = generate_exercises(
            context_chunks=relevant_chunks, 
            topic=request.topic, 
            level=request.level, 
            type=request.type,
            language=request.language
        )
        
        return {
            "topic": request.topic,
            "exercise": exercise_json_text,
            "sources_count": len(relevant_chunks)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@exercises_router.post("/upload-manual")
async def upload_manual(language: str = Form(...), level: str = Form(...), category: str = Form(...), file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        run_ingestion(temp_path, category, language, level)
        return {"message": f"File {file.filename} uploaded for {language} {level}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)