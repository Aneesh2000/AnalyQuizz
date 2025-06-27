from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List
import os
import shutil
from bson import ObjectId
from utils.database import get_database
from routers.auth import get_current_user
from utils.pdf_processor import extract_text_from_pdf

router = APIRouter()

# Pydantic models
class SyllabusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    filename: str
    file_path: str
    extracted_text: str
    created_at: datetime

class SyllabusListResponse(BaseModel):
    id: str
    filename: str
    created_at: datetime
    quiz_count: int

@router.post("/upload", response_model=SyllabusResponse)
async def upload_syllabus(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    try:
        # Decide where to store the upload. "uploads/" works locally but most
        # serverless platforms (e.g. Vercel) mount the project directory as
        # read-only. They do, however, offer a writable /tmp directory. We try
        # the normal folder first and gracefully fall back to /tmp/uploads.

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"

        primary_dir = "uploads"
        fallback_dir = "/tmp/uploads"

        # Ensure a writable directory exists
        uploads_dir = primary_dir
        try:
            os.makedirs(primary_dir, exist_ok=True)
            # Test write permission by attempting to open a dummy file
            _test_path = os.path.join(primary_dir, ".permcheck")
            with open(_test_path, "w") as _tmp:
                _tmp.write("ok")
            os.remove(_test_path)
        except Exception:
            # Primary directory not writable (likely read-only FS)
            uploads_dir = fallback_dir
            os.makedirs(uploads_dir, exist_ok=True)

        file_path = os.path.join(uploads_dir, filename)

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from PDF
        try:
            extracted_text = extract_text_from_pdf(file_path)
        except Exception as e:
            # Clean up file if text extraction fails
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")
        
        if not extracted_text.strip():
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
        
        # Save to database
        db = get_database()
        syllabus_doc = {
            "user_id": str(current_user["_id"]),
            "filename": file.filename,
            "file_path": file_path,
            "extracted_text": extracted_text,
            "created_at": datetime.utcnow()
        }
        
        result = db.syllabi.insert_one(syllabus_doc)
        syllabus_doc["_id"] = result.inserted_id
        
        return SyllabusResponse(
            id=str(syllabus_doc["_id"]),
            user_id=syllabus_doc["user_id"],
            filename=syllabus_doc["filename"],
            file_path=syllabus_doc["file_path"],
            extracted_text=syllabus_doc["extracted_text"],
            created_at=syllabus_doc["created_at"]
        )
        
    except Exception as e:
        # Clean up file if any error occurs
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.get("/list", response_model=List[SyllabusListResponse])
async def list_syllabi(current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Get syllabi for current user
    syllabi = list(db.syllabi.find({"user_id": str(current_user["_id"])}).sort("created_at", -1))
    
    # Count quizzes for each syllabus
    result = []
    for syllabus in syllabi:
        quiz_count = db.quizzes.count_documents({"syllabus_id": str(syllabus["_id"])})
        result.append(SyllabusListResponse(
            id=str(syllabus["_id"]),
            filename=syllabus["filename"],
            created_at=syllabus["created_at"],
            quiz_count=quiz_count
        ))
    
    return result

@router.get("/{syllabus_id}", response_model=SyllabusResponse)
async def get_syllabus(
    syllabus_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    try:
        syllabus = db.syllabi.find_one({
            "_id": ObjectId(syllabus_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID")
    
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    
    return SyllabusResponse(
        id=str(syllabus["_id"]),
        user_id=syllabus["user_id"],
        filename=syllabus["filename"],
        file_path=syllabus["file_path"],
        extracted_text=syllabus["extracted_text"],
        created_at=syllabus["created_at"]
    )

@router.delete("/{syllabus_id}")
async def delete_syllabus(
    syllabus_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    try:
        syllabus = db.syllabi.find_one({
            "_id": ObjectId(syllabus_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID")
    
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    
    # Delete associated quizzes
    db.quizzes.delete_many({"syllabus_id": syllabus_id})
    
    # Delete file
    if os.path.exists(syllabus["file_path"]):
        os.remove(syllabus["file_path"])
    
    # Delete from database
    db.syllabi.delete_one({"_id": ObjectId(syllabus_id)})
    
    return {"message": "Syllabus deleted successfully"} 