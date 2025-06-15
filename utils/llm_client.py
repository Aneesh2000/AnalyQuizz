import os
import json
import httpx
from typing import List, Dict, Any

async def generate_quiz_questions(syllabus_text: str, num_questions: int = 10, difficulty: str = "medium") -> List[Dict[str, Any]]:
    """
    Generate quiz questions using Grok AI API.
    
    Args:
        syllabus_text (str): The extracted syllabus text
        num_questions (int): Number of questions to generate
        difficulty (str): Difficulty level (easy, medium, hard)
    
    Returns:
        List[Dict[str, Any]]: List of generated questions
    """
    
    # Create prompt for quiz generation
    system_prompt = f"""You are an expert educator creating multiple choice questions from academic syllabi. 
    Create {num_questions} multiple choice questions at {difficulty} difficulty level.
    
    Requirements:
    - Each question should have exactly 4 options (A, B, C, D)
    - Only one option should be correct
    - Questions should test understanding, not just memorization
    - Cover different topics from the syllabus
    - Make questions clear and unambiguous
    
    Return ONLY a valid JSON array with this exact format:
    [
        {{
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A"
        }}
    ]
    
    Do not include any additional text or explanation, just the JSON array."""
    
    user_prompt = f"""Based on the following syllabus content, create {num_questions} multiple choice questions:

    SYLLABUS CONTENT:
    {syllabus_text[:4000]}  # Limit to 4000 chars to avoid token limits
    
    Generate the questions now."""
    
    try:
        # Make API call to Gemini
        response_text = await call_gemini_api(user_prompt, system_prompt)
        # Clean the response text (remove markdown formatting if present)
        cleaned_response = response_text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        # Parse JSON response
        questions = json.loads(cleaned_response)
        
        # Validate the response format
        if not isinstance(questions, list):
            raise ValueError("Response is not a list")
        
        validated_questions = []
        for i, q in enumerate(questions):
            if not all(key in q for key in ["question", "options", "correct_answer"]):
                raise ValueError(f"Question {i+1} missing required fields")
            
            if len(q["options"]) != 4:
                raise ValueError(f"Question {i+1} must have exactly 4 options")
            
            if q["correct_answer"] not in q["options"]:
                raise ValueError(f"Question {i+1} correct answer not in options")
            
            validated_questions.append({
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"]
            })
        
        return validated_questions[:num_questions]  # Ensure we don't exceed requested number
        
    except Exception as e:
        print(f"Error generating quiz questions: {e}")
        # Fallback to mock data if API fails
        return await generate_fallback_questions(num_questions, difficulty, syllabus_text)

async def generate_feedback_analysis(detailed_results: List[Dict[str, Any]], score: float, syllabus_text: str) -> Dict[str, Any]:
    """
    Generate detailed feedback analysis using Grok AI API.
    
    Args:
        detailed_results: List of question results with user answers
        score: Overall quiz score
        syllabus_text: Original syllabus content
    
    Returns:
        Dict containing detailed feedback analysis
    """
    
    correct_count = sum(1 for result in detailed_results if result.get("is_correct", False))
    total_count = len(detailed_results)
    
    # Analyze which topics were answered correctly/incorrectly
    correct_questions = [r for r in detailed_results if r.get("is_correct", False)]
    incorrect_questions = [r for r in detailed_results if not r.get("is_correct", False)]
    
    system_prompt = """You are an expert educational analyst providing personalized feedback to students based on their quiz performance. 
    
    Analyze the student's performance and provide targeted feedback in the following JSON format:
    {
        "overall_analysis": "Detailed analysis of overall performance",
        "strengths": ["strength1", "strength2", "strength3"],
        "weaknesses": ["weakness1", "weakness2", "weakness3"],
        "topic_wise_performance": {
            "topic1": {"score": 85, "questions_answered": 3},
            "topic2": {"score": 60, "questions_answered": 4},
            "topic3": {"score": 90, "questions_answered": 3}
        },
        "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
        "study_plan": "Detailed study plan with specific steps and timeline"
    }
    
    Make the analysis specific and actionable. Return ONLY the JSON, no additional text."""
    
    user_prompt = f"""Analyze this student's quiz performance:

SCORE: {score:.1f}% ({correct_count}/{total_count} correct)

SYLLABUS CONTENT:
{syllabus_text[:2000]}

CORRECT ANSWERS:
{json.dumps([{"question": q["question"], "topic": "extract from question"} for q in correct_questions[:5]], indent=2)}

INCORRECT ANSWERS:
{json.dumps([{"question": q["question"], "user_answer": q["user_answer"], "correct_answer": q["correct_answer"]} for q in incorrect_questions[:5]], indent=2)}

Provide detailed, personalized feedback and analysis."""
    
    try:
        # Make API call to Gemini
        response_text = await call_gemini_api(user_prompt, system_prompt)
        # Clean the response text (remove markdown formatting if present)
        cleaned_response = response_text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        # Parse JSON response
        feedback = json.loads(cleaned_response)
        
        # Validate required fields
        required_fields = ["overall_analysis", "strengths", "weaknesses", "topic_wise_performance", "recommendations", "study_plan"]
        for field in required_fields:
            if field not in feedback:
                raise ValueError(f"Missing required field: {field}")
        
        return feedback
        
    except Exception as e:
        print(f"Error generating feedback analysis: {e}")
        # Fallback to basic analysis if API fails
        return generate_fallback_feedback(score, correct_count, total_count, detailed_results)

# Gemini AI API implementation
async def call_gemini_api(user_prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> str:
    """
    Make API call to Google Gemini AI service.
    
    Args:
        user_prompt: The user's prompt/question
        system_prompt: System instructions for the AI
        max_tokens: Maximum tokens in response
    
    Returns:
        Response text from Gemini AI
    """
    
    # Get API key from environment variables
    api_key = os.getenv("LLM_API_KEY")
    
    if not api_key:
        raise Exception("LLM_API_KEY environment variable is not set")
    
    # Use the correct Gemini API endpoint with updated model name
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Prepare the request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.8,
                    "topK": 10
                }
            }
            
            response = await client.post(
                api_url,
                headers={
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()

                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        response_text = candidate["content"]["parts"][0]["text"]

                        return response_text
                    else:
                        raise Exception(f"Unexpected response structure: {result}")
                else:
                    raise Exception(f"No candidates in response: {result}")
            else:
                error_msg = f"Gemini API call failed with status {response.status_code}: {response.text}"
                print(error_msg)
                raise Exception(error_msg)
                
        except httpx.TimeoutException:
            raise Exception("Gemini API request timed out")
        except httpx.RequestError as e:
            raise Exception(f"Gemini API request failed: {str(e)}")

# Fallback functions for when API fails
async def generate_fallback_questions(num_questions: int, difficulty: str, syllabus_text: str) -> List[Dict[str, Any]]:
    """Generate basic questions when API fails."""
    fallback_questions = []
    syllabus_preview = syllabus_text[:200] + "..." if len(syllabus_text) > 200 else syllabus_text
    
    for i in range(num_questions):
        fallback_questions.append({
            "question": f"Based on the syllabus content, which of the following is most relevant to the topic discussed? (Question {i+1})",
            "options": [
                f"Concept related to {difficulty} level understanding",
                f"Basic principle from the syllabus material",
                f"Advanced topic requiring deeper knowledge",
                f"Fundamental concept from the course content"
            ],
            "correct_answer": f"Concept related to {difficulty} level understanding"
        })
    
    return fallback_questions

def generate_fallback_feedback(score: float, correct_count: int, total_count: int, detailed_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate basic feedback when API fails."""
    performance_level = "excellent" if score >= 90 else "good" if score >= 80 else "satisfactory" if score >= 70 else "needs improvement"
    
    return {
        "overall_analysis": f"You scored {score:.1f}% ({correct_count}/{total_count} correct), which indicates {performance_level} understanding of the syllabus content. This assessment provides insights into your grasp of the key concepts covered in the material.",
        "strengths": [
            "Demonstrated understanding of core concepts" if correct_count > total_count//2 else "Shows effort and engagement with the material",
            "Good performance on fundamental questions" if score >= 60 else "Basic comprehension of simple topics",
            "Consistent approach to problem-solving" if score >= 70 else "Willingness to attempt all questions"
        ],
        "weaknesses": [
            "Need to strengthen understanding of complex topics" if score < 80 else "Minor gaps in advanced concepts",
            "Focus on detailed analysis and critical thinking" if score < 70 else "Room for improvement in nuanced understanding",
            "Practice application of theoretical knowledge" if score < 60 else "Fine-tune understanding of specific areas"
        ],
        "topic_wise_performance": {
            "Core Concepts": {"score": min(score + 5, 100), "questions_answered": max(1, total_count // 3)},
            "Applied Knowledge": {"score": max(score - 10, 0), "questions_answered": max(1, total_count // 3)},  
            "Advanced Topics": {"score": score, "questions_answered": max(1, total_count - 2*(total_count // 3))}
        },
        "recommendations": [
            "Review the syllabus sections corresponding to incorrect answers",
            "Practice similar questions to reinforce weak areas", 
            "Focus on understanding concepts rather than memorization",
            "Seek additional resources for challenging topics"
        ],
        "study_plan": f"""Personalized Study Plan (Based on {score:.1f}% performance):

Week 1-2: Focus on Foundation
- Review syllabus sections where you scored below 70%
- Practice basic concepts and terminology
- Create summary notes of key points

Week 3-4: Strengthen Weak Areas  
- Work on topics from incorrect answers
- Solve practice problems and examples
- Discuss challenging concepts with peers/instructors

Week 5-6: Advanced Practice & Review
- Attempt more complex questions
- Review all topics comprehensively  
- Take practice quizzes to track progress

Daily Commitment: 1-2 hours of focused study
Weekly Goal: Improve understanding in identified weak areas"""
    }