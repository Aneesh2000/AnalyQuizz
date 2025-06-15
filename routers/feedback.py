from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List
from bson import ObjectId
from utils.database import get_database
from routers.auth import get_current_user
from utils.llm_client import generate_feedback_analysis

router = APIRouter()

# Pydantic models
class FeedbackRequest(BaseModel):
    result_id: str

class FeedbackResponse(BaseModel):
    id: str
    result_id: str
    overall_analysis: str
    strengths: List[str]
    weaknesses: List[str]
    topic_wise_performance: Dict[str, Any]
    recommendations: List[str]
    study_plan: str
    generated_at: datetime

@router.post("/generate", response_model=FeedbackResponse)
async def generate_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    # Get quiz result
    try:
        quiz_result = db.quiz_results.find_one({
            "_id": ObjectId(request.result_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid result ID")
    
    if not quiz_result:
        raise HTTPException(status_code=404, detail="Quiz result not found")
    
    # Check if feedback already exists
    existing_feedback = db.feedback.find_one({"result_id": request.result_id})
    if existing_feedback:
        return FeedbackResponse(
            id=str(existing_feedback["_id"]),
            result_id=existing_feedback["result_id"],
            overall_analysis=existing_feedback["overall_analysis"],
            strengths=existing_feedback["strengths"],
            weaknesses=existing_feedback["weaknesses"],
            topic_wise_performance=existing_feedback["topic_wise_performance"],
            recommendations=existing_feedback["recommendations"],
            study_plan=existing_feedback["study_plan"],
            generated_at=existing_feedback["generated_at"]
        )
    
    # Get quiz and syllabus information
    quiz = db.quizzes.find_one({"_id": ObjectId(quiz_result["quiz_id"])})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    syllabus = db.syllabi.find_one({"_id": ObjectId(quiz["syllabus_id"])})
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    
    try:
        # Generate feedback using LLM
        feedback_data = await generate_feedback_analysis(
            quiz_result["detailed_results"],
            quiz_result["score"],
            syllabus["extracted_text"]
        )
        
        # Save feedback to database
        feedback_doc = {
            "result_id": request.result_id,
            "user_id": str(current_user["_id"]),
            "overall_analysis": feedback_data["overall_analysis"],
            "strengths": feedback_data["strengths"],
            "weaknesses": feedback_data["weaknesses"],
            "topic_wise_performance": feedback_data["topic_wise_performance"],
            "recommendations": feedback_data["recommendations"],
            "study_plan": feedback_data["study_plan"],
            "generated_at": datetime.utcnow()
        }
        
        result = db.feedback.insert_one(feedback_doc)
        feedback_doc["_id"] = result.inserted_id
        
        return FeedbackResponse(
            id=str(feedback_doc["_id"]),
            result_id=feedback_doc["result_id"],
            overall_analysis=feedback_doc["overall_analysis"],
            strengths=feedback_doc["strengths"],
            weaknesses=feedback_doc["weaknesses"],
            topic_wise_performance=feedback_doc["topic_wise_performance"],
            recommendations=feedback_doc["recommendations"],
            study_plan=feedback_doc["study_plan"],
            generated_at=feedback_doc["generated_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate feedback: {str(e)}")

@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    try:
        feedback = db.feedback.find_one({
            "_id": ObjectId(feedback_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid feedback ID")
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return FeedbackResponse(
        id=str(feedback["_id"]),
        result_id=feedback["result_id"],
        overall_analysis=feedback["overall_analysis"],
        strengths=feedback["strengths"],
        weaknesses=feedback["weaknesses"],
        topic_wise_performance=feedback["topic_wise_performance"],
        recommendations=feedback["recommendations"],
        study_plan=feedback["study_plan"],
        generated_at=feedback["generated_at"]
    ) 