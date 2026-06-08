from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.exercises_routes import exercises_router
from api.user_routes import user_router
from api.user_routes import classroom_router
from api.teacher_routes import teacher_router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Communication with Angular frontend successful!"}

app.include_router(exercises_router, prefix="/api", tags=["Exercises"])
app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(teacher_router, prefix="/api", tags=["Teacher"])
app.include_router(classroom_router, prefix="/api/classrooms", tags=["Classrooms"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)