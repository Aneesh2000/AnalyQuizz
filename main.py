from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from fastapi.responses import Response

# Load environment variables from .env file
load_dotenv()

# Import database utilities
from utils.database import initialize_database, close_database

# Import routers
from routers import auth, syllabus, quiz, feedback

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        initialize_database()
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    close_database()

# Create FastAPI app
app = FastAPI(
    title="AnalyQuiz API",
    description="API for syllabus-based MCQ quiz generation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:8080",
        "https://*.onrender.com",  # For Render deployment
        "https://*.vercel.app",    # For Vercel deployment
        "*"  # Allow all origins in production (you can restrict this later)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(syllabus.router, prefix="/api/syllabus", tags=["syllabus"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    except FileNotFoundError:
        return {"message": "AnalyQuiz API is running!"}

@app.get("/health")
async def health_check():
    from utils.database import get_database
    try:
        db = get_database()
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "healthy", "database": "disconnected"}
