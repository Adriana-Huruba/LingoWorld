from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.user_service import UserService

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