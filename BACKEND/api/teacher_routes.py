import os
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader

from core.database import get_db
from core.security import get_current_user
from services.teacher_service import TeacherService
from repository.teacher_repository import TeacherRepository
from services.didactic_agent import generate_worksheet_preview, regenerate_single_preview
from services.vector_service import delete_teacher_material_chunks

teacher_router = APIRouter()

UPLOAD_FOLDER = "/tmp/teacher_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class PreviewRequest(BaseModel):
    teacher_id: int
    manual_id: int
    exercise_counts: dict[str, int]
    level: str
    language: str
    topic: str = "general"
    native_language: str = "romanian"
    page_range: Optional[list[int]] = None
    chapter: Optional[str] = None
    extra_instructions: str = ""


class RegenerateRequest(BaseModel):
    teacher_id: int
    exercise_type: str
    generation_config: dict


class PublishItem(BaseModel):
    exercise_type: str
    content: dict
    correct_answer: str
    elo_difficulty: int = 450


class PublishRequest(BaseModel):
    teacher_id: int
    manual_id: int
    classroom_id: int
    title: str
    due_date: Optional[datetime] = None
    items: list[PublishItem]
    config: dict = {}


@teacher_router.post("/manuals/upload", status_code=201)
async def upload_manual(file: UploadFile = File(...), teacher_id: int = Form(...), title: str = Form(...), language: str = Form(...), level: str = Form(...), conn=Depends(get_db), _=Depends(get_current_user)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    filepath = os.path.join(UPLOAD_FOLDER, f"{teacher_id}_{file.filename}")
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        reader = PdfReader(filepath)
        sample_text = ""

        pages_to_check = min(3, len(reader.pages))
        for i in range(pages_to_check):
            sample_text += reader.pages[i].extract_text() or ""
        
        if len(sample_text.strip()) < 50:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise HTTPException(
                status_code=400, 
                detail="The document may be scanned and full of images. Please upload a PDF text file!"
            )
            
    except HTTPException:
        raise
    except Exception:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=400, detail="PDF file cannot be read")

    try:
        result = TeacherService.process_and_ingest_manual(pdf_path=filepath, teacher_id=teacher_id, language=language, level=level, title=title, conn=conn)
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@teacher_router.get("/manuals")
def list_manuals(teacher_id: int, conn=Depends(get_db), _=Depends(get_current_user)):
    try:
        return TeacherRepository.list_manuals(teacher_id, conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.delete("/manuals/{manual_id}", status_code=200)
def delete_manual(manual_id: int, teacher_id: int, conn=Depends(get_db), _=Depends(get_current_user)):
    try:
        manual = TeacherRepository.get_manual_by_id(manual_id, teacher_id, conn)
        if not manual:
            raise HTTPException(status_code=404, detail="Manual not found or not owned by you")
        delete_teacher_material_chunks(manual_id)
        deleted = TeacherRepository.delete_manual(manual_id, teacher_id, conn)
        if not deleted:
            raise HTTPException(status_code=404, detail="Manual not found or not owned by you")
        return {"detail": "Manual deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.get("/manuals/{manual_id}")
def get_manual(manual_id: int, teacher_id: int, conn=Depends(get_db), _=Depends(get_current_user)):
    try:
        manual = TeacherRepository.get_manual_by_id(manual_id, teacher_id, conn)
        if not manual:
            raise HTTPException(status_code=404, detail="Manual not found")
        return manual
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@teacher_router.post("/worksheets/preview")
def preview_worksheet(payload: PreviewRequest, conn=Depends(get_db), _=Depends(get_current_user)):
    try:
        page_range = tuple(payload.page_range) if payload.page_range else None
        result = generate_worksheet_preview(
            teacher_id=payload.teacher_id,
            manual_id=payload.manual_id,
            exercise_counts=payload.exercise_counts,
            level=payload.level,
            language=payload.language,
            topic=payload.topic,
            native_language=payload.native_language,
            page_range=page_range,
            chapter=payload.chapter,
            extra_instructions=payload.extra_instructions,
            conn=conn,
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.post("/worksheets/regenerate-item")
def regenerate_item(payload: RegenerateRequest, conn=Depends(get_db), _=Depends(get_current_user)):
    try:
        result = regenerate_single_preview(
            teacher_id=payload.teacher_id,
            exercise_type=payload.exercise_type,
            generation_config=payload.generation_config,
            conn=conn,
        )
        if not result:
            raise HTTPException(status_code=500, detail="Regeneration failed")
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.post("/worksheets/publish", status_code=201)
def publish_worksheet(payload: PublishRequest, conn=Depends(get_db), _=Depends(get_current_user)):
    try:
        result = TeacherRepository.publish_complete_worksheet(payload, conn)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.get("/worksheets")
def list_worksheets(teacher_id: int, conn=Depends(get_db), _=Depends(get_current_user)):
    try:
        return TeacherRepository.list_worksheets(teacher_id, conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@teacher_router.get("/worksheets/{worksheet_id}/progress")
def get_worksheet_progress(worksheet_id: int, teacher_id: int, conn=Depends(get_db), _=Depends(get_current_user)):
    try:
        result = TeacherRepository.get_worksheet_progress(worksheet_id, teacher_id, conn)
        if not result:
            raise HTTPException(status_code=403, detail="Not authorized or worksheet not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))