from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.user_service import UserService
from services.classroom_service import ClassroomService

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str
    native_language: str = ""
    target_language: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

user_router = APIRouter()

@user_router.post('/register')
async def register(user_info: RegisterRequest):
    success = UserService.register_user(user_info.model_dump())
    if success:
        return {"message": "User registered successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Error during registration. Email might already exist.")

@user_router.post('/login')
async def login(credentials: LoginRequest):
    user = UserService.login_user(credentials.email, credentials.password)
    if user:
        return {
            "message": "Login successful",
            "user": user
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
# endpoints for teachers - classroom management
class ClassroomCreateRequest(BaseModel):
    name: str
    teacher_id: int # future: auth token jwt

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

@classroom_router.get('/all/{teacher_id}')
async def get_teacher_classrooms(teacher_id: int):
    classrooms = ClassroomService.get_teacher_classrooms(teacher_id)
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