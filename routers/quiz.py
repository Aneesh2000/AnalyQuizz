from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any
from bson import ObjectId
from utils.database import get_database
from routers.auth import get_current_user
from utils.llm_client import generate_quiz_questions

router = APIRouter()

# Pydantic models
class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str

class QuizGenerationRequest(BaseModel):
    syllabus_id: str
    num_questions: int = 10
    difficulty: str = "medium"  # easy, medium, hard

class QuizResponse(BaseModel):
    id: str
    syllabus_id: str
    questions: List[Dict[str, Any]]  # Without correct answers for taking quiz
    created_at: datetime
    time_limit: int  # in minutes

class QuizSubmission(BaseModel):
    quiz_id: str
    answers: Dict[str, str]  # question_id -> selected_answer

class QuizResult(BaseModel):
    id: str
    quiz_id: str
    user_id: str
    answers: Dict[str, str]
    score: float
    total_questions: int
    correct_answers: int
    submitted_at: datetime
    detailed_results: List[Dict[str, Any]]

class QuizListResponse(BaseModel):
    id: str
    syllabus_filename: str
    score: float
    total_questions: int
    created_at: datetime
    submitted_at: datetime

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    # Verify syllabus exists and belongs to user
    try:
        syllabus = db.syllabi.find_one({
            "_id": ObjectId(request.syllabus_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid syllabus ID")
    
    if not syllabus:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    
    try:
        # Generate questions using LLM
        questions = await generate_quiz_questions(
            syllabus["extracted_text"],
            request.num_questions,
            request.difficulty
        )
        
        # Prepare questions for storage (with correct answers)
        questions_with_answers = []
        questions_for_quiz = []  # Without correct answers for frontend
        
        for i, q in enumerate(questions):
            question_id = str(i)
            question_with_answer = {
                "id": question_id,
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"]
            }
            questions_with_answers.append(question_with_answer)
            
            # Remove correct answer for quiz taking
            question_for_quiz = {
                "id": question_id,
                "question": q["question"],
                "options": q["options"]
            }
            questions_for_quiz.append(question_for_quiz)
        
        # Save quiz to database
        quiz_doc = {
            "user_id": str(current_user["_id"]),
            "syllabus_id": request.syllabus_id,
            "questions": questions_with_answers,
            "difficulty": request.difficulty,
            "time_limit": 30,  # 30 minutes default
            "created_at": datetime.utcnow()
        }
        
        result = db.quizzes.insert_one(quiz_doc)
        quiz_doc["_id"] = result.inserted_id
        
        return QuizResponse(
            id=str(quiz_doc["_id"]),
            syllabus_id=quiz_doc["syllabus_id"],
            questions=questions_for_quiz,
            created_at=quiz_doc["created_at"],
            time_limit=quiz_doc["time_limit"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    try:
        quiz = db.quizzes.find_one({
            "_id": ObjectId(quiz_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid quiz ID")
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Remove correct answers from questions
    questions_for_quiz = []
    for q in quiz["questions"]:
        question_for_quiz = {
            "id": q["id"],
            "question": q["question"],
            "options": q["options"]
        }
        questions_for_quiz.append(question_for_quiz)
    
    return QuizResponse(
        id=str(quiz["_id"]),
        syllabus_id=quiz["syllabus_id"],
        questions=questions_for_quiz,
        created_at=quiz["created_at"],
        time_limit=quiz["time_limit"]
    )

@router.post("/submit", response_model=QuizResult)
async def submit_quiz(
    submission: QuizSubmission,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    # Get quiz
    try:
        quiz = db.quizzes.find_one({
            "_id": ObjectId(submission.quiz_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid quiz ID")
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Calculate score
    correct_answers = 0
    total_questions = len(quiz["questions"])
    detailed_results = []
    
    for question in quiz["questions"]:
        question_id = question["id"]
        user_answer = submission.answers.get(question_id, "")
        is_correct = user_answer == question["correct_answer"]
        
        if is_correct:
            correct_answers += 1
        
        detailed_results.append({
            "question_id": question_id,
            "question": question["question"],
            "options": question["options"],
            "user_answer": user_answer,
            "correct_answer": question["correct_answer"],
            "is_correct": is_correct
        })
    
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Save quiz result
    result_doc = {
        "quiz_id": submission.quiz_id,
        "user_id": str(current_user["_id"]),
        "answers": submission.answers,
        "score": score,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "detailed_results": detailed_results,
        "submitted_at": datetime.utcnow()
    }
    
    result = db.quiz_results.insert_one(result_doc)
    result_id = str(result.inserted_id)
    
    return QuizResult(
        id=result_id,
        quiz_id=submission.quiz_id,
        user_id=str(current_user["_id"]),
        answers=submission.answers,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_answers,
        submitted_at=result_doc["submitted_at"],
        detailed_results=result_doc["detailed_results"]
    )

@router.get("/results/{result_id}", response_model=QuizResult)
async def get_quiz_result(
    result_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    try:
        result = db.quiz_results.find_one({
            "_id": ObjectId(result_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid result ID")
    
    if not result:
        raise HTTPException(status_code=404, detail="Quiz result not found")
    
    return QuizResult(
        id=str(result["_id"]),
        quiz_id=result["quiz_id"],
        user_id=result["user_id"],
        answers=result["answers"],
        score=result["score"],
        total_questions=result["total_questions"],
        correct_answers=result["correct_answers"],
        submitted_at=result["submitted_at"],
        detailed_results=result["detailed_results"]
    )

@router.get("/list/results", response_model=List[QuizListResponse])
async def list_quiz_results(current_user: dict = Depends(get_current_user)):
    db = get_database()
    
    # Get all quiz results for the user
    results = list(db.quiz_results.find({"user_id": str(current_user["_id"])}).sort("submitted_at", -1))
    
    response = []
    for result in results:
        # Get quiz and syllabus info
        quiz = db.quizzes.find_one({"_id": ObjectId(result["quiz_id"])})
        if quiz:
            syllabus = db.syllabi.find_one({"_id": ObjectId(quiz["syllabus_id"])})
            syllabus_filename = syllabus["filename"] if syllabus else "Unknown"
        else:
            syllabus_filename = "Unknown"
        
        response.append(QuizListResponse(
            id=str(result["_id"]),
            syllabus_filename=syllabus_filename,
            score=result["score"],
            total_questions=result["total_questions"],
            created_at=quiz["created_at"] if quiz else result["submitted_at"],
            submitted_at=result["submitted_at"]
        ))
    
    return response 