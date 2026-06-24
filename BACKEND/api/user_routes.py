import re

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from services.user_service import UserService
from services.classroom_service import ClassroomService

ALLOWED_LANGUAGES = {"english", "romanian", "french", "spanish"}
ALLOWED_ROLES = {"student", "teacher", "adult_learner"}

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    native_language: str = ""
    target_language: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 50:
            raise ValueError("Name must be at most 50 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ALLOWED_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(sorted(ALLOWED_ROLES))}")
        return v

    @field_validator("native_language", "target_language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v and v.lower() not in ALLOWED_LANGUAGES:
            raise ValueError(f"Language must be one of: {', '.join(sorted(ALLOWED_LANGUAGES))}")
        return v.lower() if v else v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

user_router = APIRouter()

@user_router.post('/register')
async def register(user_info: RegisterRequest):
    success = UserService.register_user(user_info.model_dump())
    if success:
        return {"message": "User registered successfully!"}
    raise HTTPException(status_code=400, detail="Registration failed. Email might already be in use.")

@user_router.post('/login')
async def login(credentials: LoginRequest):
    # UserService.login_user already generates the JWT and includes it as user["token"]
    user = UserService.login_user(credentials.email, credentials.password)
    if user:
        return {"message": "Login successful", "user": user}
    raise HTTPException(status_code=401, detail="Invalid email or password")
    
# endpoints for teachers - classroom management
class ClassroomCreateRequest(BaseModel):
    name: str
    teacher_id: int

class CompleteWorksheetRequest(BaseModel):
    student_id: int
    worksheet_id: int
    score: int
    total: int

class EnrollStudent(BaseModel):
    invite_code: str
    student_id: int 

classroom_router = APIRouter()

@classroom_router.post('/create')
async def create_classroom(data: ClassroomCreateRequest):
    invite_code = ClassroomService.create_new_class(data.name, data.teacher_id)
    if invite_code:
        return {
            "message": "Classroom created successfully",
            "invite_code": invite_code
        }
    else:
        raise HTTPException(status_code=400, detail="Could not create classroom")

@classroom_router.post('/enroll')
async def enroll_student(data: EnrollStudent):
    success, message = ClassroomService.enroll_student(data.student_id, data.invite_code)
    if success:
        return {"message": message}
    else:
        raise HTTPException(status_code=400, detail=message)

@classroom_router.post('/complete-worksheet')
async def complete_worksheet(data: CompleteWorksheetRequest):
    ok = ClassroomService.complete_worksheet(data.student_id, data.worksheet_id, data.score, data.total)
    if not ok:
        raise HTTPException(status_code=500, detail="Could not save completion")
    return {"message": "Completion saved", "worksheet_id": data.worksheet_id, "score": data.score, "total": data.total}

@classroom_router.get('/all/{teacher_id}')
async def get_teacher_classrooms(teacher_id: int):
    classrooms = ClassroomService.get_teacher_classrooms(teacher_id)
    return {"classrooms": classrooms}


@classroom_router.get('/student-classes/{student_id}')
async def get_student_classrooms(student_id: int):
    classrooms = ClassroomService.get_student_classrooms(student_id)
    return {"classrooms": classrooms}


@classroom_router.get('/{classroom_id}')
async def get_classroom(classroom_id: int):
    classroom = ClassroomService.get_classroom(classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail='Classroom not found')
    return classroom

@classroom_router.get('/{classroom_id}/students')
async def get_classroom_students(classroom_id: int):
    students = ClassroomService.get_classroom_students(classroom_id)
    return {"students": students}

@classroom_router.get('/student/{student_id}/pending-assignments')
async def get_pending_assignments(student_id: int):
    assignments = ClassroomService.get_pending_assignments_for_student(student_id)
    return {"assignments": assignments}

@classroom_router.get('/{classroom_id}/assignments')
async def get_classroom_assignments(classroom_id: int, student_id: Optional[int] = None):
    assignments = ClassroomService.get_classroom_assignments(classroom_id, student_id=student_id)
    return {"assignments": assignments}

@classroom_router.get('/{classroom_id}/student-progress')
async def get_student_progress(classroom_id: int):
    progress = ClassroomService.get_student_progress(classroom_id)
    return {"students": progress}