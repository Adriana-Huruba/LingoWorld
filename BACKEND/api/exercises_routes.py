from ast import If
import os
import shutil

from typing import Optional
from fastapi import APIRouter, Depends, File, Form,  HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.database import get_db
from core.ingest_pdf import run_ingestion
from services.exercise_service import get_or_generate_exercise
from services.initial_quiz_service import get_quiz_exercises, submit_quiz_results, has_completed_quiz
from services.recommender_service import get_next_exercise, record_answer

exercises_router = APIRouter()

class ExerciseRequest(BaseModel):
    user_id: int
    topic: str
    level: str = "B2"
    type: str = "multiple-choice" # implicit, if not specified
    language: str = "english" # implicit, if not specified 
    skill_type: Optional[str] = None

class NextExerciseRequest(BaseModel):
    user_id: int
    target_language: str = "english"
    skill_type: Optional[str] = None
    topic: Optional[str] = None

class SubmitAnswerRequest(BaseModel):
    user_id: int
    exercise_id: int
    is_correct: bool
    response_time_seconds: int
    exercise_type: str # multiple-choice, fill-in-the-blank, translation
    used_hint: bool = False
    assignment_id: Optional[int] = None

class InitialQuizSubmitRequest(BaseModel):
    user_id: int
    language: str
    responses: list[dict] # exercise_id, is_correct, response_time, exercise_type, used_hint

@exercises_router.post("/generate-exercise")
async def get_exercise(request: ExerciseRequest, conn=Depends(get_db)):
    """
    1. Searching in postgreSQL for relevant exercises based on the topic, language and level. 
    2. If not found, searching in qdrant for relevant chunks from the textbooks, then sending them to LLM to generate the exercise.
    """
    
    try:
        exercise = get_or_generate_exercise(
            user_id=request.user_id,
            topic=request.topic,
            level=request.level,
            language=request.language,
            exercise_type=request.type,
            skill_type=request.skill_type,
            conn=conn,
        )
        if not exercise:
            raise HTTPException(
                status_code=404,
                detail="Did not find any relevant chunks. Try for another topic/manual."
            )
        return exercise.to_dict()
 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@exercises_router.post("/next-exercise")
async def next_exercise(request: NextExerciseRequest, conn = Depends(get_db)):
    try:
        exercise = get_next_exercise(user_id=request.user_id, target_language=request.target_language, conn=conn, skill_type=request.skill_type, topic=request.topic)
        if not exercise:
            raise HTTPException(
                status_code=404,
                detail="There are no exercises available"
            )
        if hasattr(exercise, "to_dict"):
            return exercise.to_dict()
        return exercise
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@exercises_router.post("/submit-answer")
async def submit_answer(request: SubmitAnswerRequest, conn = Depends(get_db)):
    try:
        return record_answer(
            user_id=request.user_id, 
            exercise_id=request.exercise_id,
            is_correct=request.is_correct,
            response_time_seconds=request.response_time_seconds,
            exercise_type=request.exercise_type,
            used_hint=request.used_hint,
            conn=conn,
            assignment_id=request.assignment_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@exercises_router.get("/initial-quiz/{language}")
async def get_initial_quiz(language: str, conn = Depends(get_db)):
    try:
        exercises = get_quiz_exercises(language=language, conn=conn)
        return {
            "language": language,
            "exercises": [e.to_dict() for e in exercises],
            "total": len(exercises),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@exercises_router.post("/initial-quiz/submit")
async def submit_initial_quiz(request: InitialQuizSubmitRequest, conn = Depends(get_db),):
    try:
        if has_completed_quiz(request.user_id, conn):
            raise HTTPException(
                status_code=409,
                detail="Initial quiz was already completed"
            )
        return submit_quiz_results(user_id=request.user_id, responses=request.responses, conn=conn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@exercises_router.post("/upload-manual")
async def upload_manual(language: str = Form(...), level: str = Form(...), file: UploadFile = File(...), uploaded_by_user_id: Optional[int] = Form(None)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted!")

    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        run_ingestion(pdf_path=temp_path, language=language, level=level, uploaded_by_user=uploaded_by_user_id)
        return {"message": f"File {file.filename} uploaded for {language} {level}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)