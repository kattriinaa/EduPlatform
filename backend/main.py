from bson import ObjectId
from fastapi import FastAPI, HTTPException, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
from app.core.security import get_password_hash, verify_password

app = FastAPI()
router = APIRouter()

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.eduplatform

class Lesson(BaseModel):
    id: int
    title: str
    duration: str
    content: Optional[str] = ""

    type: Optional[str] = None 
    assignment_instruction: Optional[str] = None
    videoUrl: Optional[str] = None
    videoDescription: Optional[str] = None
    quiz: Optional[dict] = None
    days_offset: int = 0
    is_event: bool = False

class Module(BaseModel):
    id: int
    title: str
    lessons: List[Lesson]
    
class Course(BaseModel):
    id: int
    title: str
    teacher: str
    rating: float = 0.0          
    students: int = 0            
    duration: str = ""
    image: str = ""
    description: Optional[str] = "" 
    modules: List[Module] = []

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str

class LoginRequest(BaseModel):
    email: str
    password: str

class MessageModel(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[MessageModel]

class EnrollRequest(BaseModel):
    user_id: int
    course_id: int

class Submission(BaseModel):
    user_id: int
    student_name: str
    course_id: int
    lesson_id: int
    lesson_title: str
    answer: str
    status: str = "pending"
    submitted_at: str = datetime.now().strftime("%Y-%m-%d %H:%M")

class StatusUpdate(BaseModel):
    status: str

class RevisionPayload(BaseModel):
    status: str
    feedback: str

class CourseCreate(BaseModel):
    id: int
    teacher_id: int
    teacher: str
    title: str
    description: str
    rating: float
    students: int
    duration: str
    image: str
    enrolled_students: List = []
    modules: List[Module]

class EventCreate(BaseModel):
    title: str
    course_id: int
    course: str
    type: str = "lecture"
    day: str  # Формат YYYY-MM-DD
    color: Optional[str] = "bg-blue-100 text-blue-800"

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Intro to Python",
                "course_id": 12345,
                "course": "Python Pro",
                "type": "lecture",
                "day": "2026-04-26",
                "color": "bg-blue-100 text-blue-800"
            }
        }

@app.get("/")
async def root():
    return {"message": "Server is running! Go to /api/courses to see data"}


@app.get("/api/courses", response_model=List[Course])
async def get_courses():
    courses_cursor = db.courses.find({}, {"_id": 0})
    courses = await courses_cursor.to_list(length=100)
    return courses


@app.get("/api/courses/student/{user_id}")
async def get_student_courses(user_id: int):
    student = await db.users.find_one({"id": user_id, "role": "student"})
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    course_ids = student.get("enrolled_courses", [])
    
    courses = await db.courses.find(
        {"id": {"$in": course_ids}},
        {"_id": 0}
    ).to_list(100)
    
    return courses


@app.get("/api/courses/teacher/{user_id}")
async def get_teacher_courses(user_id: int):
    courses = await db.courses.find(
        {"teacher_id": user_id}, 
        {"_id": 0}
    ).to_list(100)
    
    if not courses:
        return []
        
    return courses


@app.get("/api/courses/{course_id}")
async def get_course(course_id: int):
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if course:
        return course
    raise HTTPException(status_code=404, detail="Course not found")


@app.get("/api/events")
async def get_events():
    events_cursor = db.events.find({}, {"_id": 0})
    events = await events_cursor.to_list(length=100)
    return events


@app.post("/api/register")
async def register(data: RegisterRequest):
    hashed_pass = get_password_hash(data.password)
    existing_user = await db.users.find_one({"email": data.email})
    if existing_user:
        return JSONResponse(
            status_code=400, 
            content={"message": "Email already registered"}
        )

    last_user = await db.users.find_one(sort=[("id", -1)])
    new_id = (last_user["id"] + 1) if last_user else 1

    new_user = {
        "id": new_id,
        "name": data.name,
        "email": data.email,
        "password": hashed_pass,
        "role": data.role,
        "enrolled_courses": []
    }

    await db.users.insert_one(new_user)

    return {
        "id": new_user["id"],
        "name": new_user["name"],
        "role": new_user["role"],
        "email": new_user["email"]
    }


@app.post("/api/login")
async def login(data: LoginRequest):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "message": "Login successful",
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
        "email": user["email"]
    }

@app.post("/api/ai/chat")
async def chat_with_ai(data: ChatRequest):
    try:
        system_instruction = {
            "role": "system", 
            "content": """You are the Edu Assistant on the EduPlatform. 
            Your goal is to help students with the following courses:
            1. JavaScript Mastery (from basics to React).
            2. Python Development (syntax, APIs, and FastAPI).
            3. UI/UX Design Essentials.
            Please be concise, professional, and focus on educational content."""
        }

        full_messages = [system_instruction] + [m.dict() for m in data.messages]

        response = await openai_client.chat.completions.create(
            model="gpt-4o", 
            messages=full_messages
        )
        
        ai_reply = response.choices[0].message.content
        return {"reply": ai_reply}

    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

@app.post("/api/ai/generate-course")
async def generate_course_ai(payload: dict):
    syllabus = payload.get("syllabus")
    start_date = payload.get("start_date", "today")
    end_date = payload.get("end_date", "8 weeks from today")
    
    if not syllabus:
        raise HTTPException(status_code=400, detail="Syllabus is required")

    # Промт всередині generate_course_ai
    full_user_content = f"""
    Syllabus: {syllabus}
    Course Period: {start_date} to {end_date}

    INSTRUCTION:
    Generate a professional course with logical progression. 
    Each module MUST follow a "Theory -> Practice -> Test" flow.
    Every lesson must be meaningful.

    STRICT CONTENT RULES:
    1. EVERY lesson must have a "content" field (minimum 3 paragraphs). 
       - FOR ALL TYPES: "content" must be a deep-dive textbook-style explanation. 
       - PROHIBITION: Never include lists of tasks (1., 2., 3...) inside "content". 
       - Use grammar explanations, examples, and nuances (with Spanish-to-Ukrainian translations).

    2. Lesson 1 (type: "text"): 
       - "content": Detailed theoretical foundation (no tasks here).
       - "assignment_instruction": null.
       - "quiz": null.

    3. Lesson 2 (type: "assignment"): 
       - "content": Detailed theory/rules only (the "study material").
       - "assignment_instruction": MUST contain ONLY the practical tasks (numbered list). 
         Do not repeat theory here.
       - "quiz": null.

    4. Lesson 3 (type: "quiz"): 
       - "content": A concise summary/recap of the module topic to prepare for the test.
       - "assignment_instruction": null.
       - "quiz": A complete object with questions, options, and correct answers.

    5. METADATA:
       - "scheduled_date": Plan logically across the course period.
       - "teacher_hours": 0.5 for text, 2.0 for assignments, 0.5 for quiz.

    6. Pedagogical Style:
       - Tone: Professional, encouraging, and highly instructional.
    
    JSON STRUCTURE:
    {{
    "title": "Course Title",
    "description": "Summary",
    "modules": [
        {{
        "title": "Module Name",
        "lessons": [
            {{
            "title": "Deep Dive into Theory",
            "type": "text",
            "duration": "25 min",
            "content": "Full theory text here...",
            "assignment_instruction": null,
            "quiz": null,
            "scheduled_date": "YYYY-MM-DD"
            }},
            {{
            "title": "Practical Implementation",
            "type": "assignment",
            "duration": "50 min",
            "content": null,
            "assignment_instruction": "1. Setup... 2. Build... 3. Test...",
            "quiz": null,
            "scheduled_date": "YYYY-MM-DD"
            }},
            {{
            "title": "Final Knowledge Check",
            "type": "quiz",
            "duration": "15 min",
            "content": null,
            "assignment_instruction": null,
            "quiz": {{
                "questions": [
                {{ "question": "The main concept is...", "options": ["A", "B", "C", "D"], "correctAnswer": 0 }}
                ]
            }},
            "scheduled_date": "YYYY-MM-DD"
            }}
        ]
        }}
    ]
    }}
    """

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are a professional course creator that outputs only valid JSON without markdown formatting."},
                {"role": "user", "content": full_user_content}
            ],
            response_format={ "type": "json_object" }
        )
        
        raw_content = response.choices[0].message.content
        
        if not raw_content:
            raise HTTPException(status_code=500, detail="AI returned empty content")

        clean_json = raw_content.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.replace("```json", "").replace("```", "").strip()
        
        return json.loads(clean_json)
    
    except Exception as e:
        print(f"AI Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/api/courses/enroll")
async def enroll_course(data: EnrollRequest):
    try:
        user_result = await db.users.update_one(
            {"id": data.user_id, "role": "student"},
            {"$addToSet": {"enrolled_courses": data.course_id}}
        )

        if user_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Student not found")

        course_result = await db.courses.update_one(
            {"id": data.course_id},
            {
                "$addToSet": {"enrolled_students": data.user_id},
                "$inc": {"students": 1}
            }
        )

        if course_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Course not found")

        return {"message": "Successfully enrolled", "course_id": data.course_id}

    except Exception as e:
        print(f"Enrollment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to enroll in course")


@app.post("/api/courses/unenroll")
async def unenroll_course(data: EnrollRequest):
    try:
        course = await db.courses.find_one({"id": data.course_id})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        lesson_ids = []
        for m in course.get("modules", []):
            for l in m.get("lessons", []):
                lesson_ids.append(l["id"])

        user_result = await db.users.update_one(
            {"id": data.user_id, "role": "student"},
            {"$pull": {
                "enrolled_courses": data.course_id,
                "completed_lessons": {"$in": lesson_ids}
            }}
        )

        if user_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Student not found")

        course_result = await db.courses.update_one(
            {"id": data.course_id},
            {
                "$pull": {"enrolled_students": data.user_id},
                "$inc": {"students": -1}
            }
        )

        if course_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Course not found")

        return {"message": "Successfully unenrolled", "course_id": data.course_id}

    except Exception as e:
        print(f"Unenrollment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unenroll from course")
    

@app.get("/api/courses/{course_id}/lessons/{lesson_id}")
async def get_lesson(course_id: int, lesson_id: int):
    course = await db.courses.find_one({"id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    for module in course.get("modules", []):
        for lesson in module.get("lessons", []):
            if lesson["id"] == lesson_id:
                return lesson
                
    raise HTTPException(status_code=404, detail="Lesson not found")

    

@app.post("/api/lessons/complete")
async def complete_lesson(data: dict):
    user_id = data.get("user_id")
    lesson_id = data.get("lesson_id")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$addToSet": {"completed_lessons": lesson_id}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"message": "Progress saved"}


@app.get("/api/users/{user_id}")
async def get_user_data(user_id: int):
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/api/courses/{course_id}")
async def update_course(course_id: int, updated_data: dict):
    result = await db.courses.update_one(
        {"id": course_id}, 
        {"$set": updated_data}
    )
    
    if result.matched_count == 0:
        return {"error": "Course not found"}, 404
        
    return {"message": "Course updated successfully"}


@app.get("/api/submissions/pending-count")
async def get_pending_count():
    count = await db.submissions.count_documents({"status": "pending"})
    return {"count": count}


@app.get("/api/instructor/all-submissions")
async def get_pending_submissions():
    cursor = db.submissions.find()
    submissions = await cursor.to_list(length=100)
    for s in submissions:
        s["id"] = str(s["_id"])
        del s["_id"]
    return submissions


@app.patch("/api/submissions/{sub_id}")
async def update_submission_status(sub_id: str, update: StatusUpdate):
    from bson import ObjectId
    
    result = await db.submissions.update_one(
        {"_id": ObjectId(sub_id)},
        {"$set": {"status": update.status}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    if update.status == "approved":
        submission = await db.submissions.find_one({"_id": ObjectId(sub_id)})
        lesson_key = f"{submission['course_id']}_{submission['lesson_id']}"
        
        await db.users.update_one(
            {"id": submission["user_id"]},
            {"$addToSet": {"completed_lessons": lesson_key}}
        )
        
    return {"message": f"Status updated to {update.status}"}


@app.post("/api/assignments/submit")
async def submit_assignment_form(submission: Submission):
    result = await db.submissions.update_one(
        {
            "user_id": submission.user_id,
            "lesson_id": submission.lesson_id
        },
        {
            "$set": submission.dict()
        },
        upsert=True
    )
    return {"message": "Assignment updated/submitted successfully"}


@app.post("/api/assignments/{submission_id}/revision")
async def update_assignment_revision(submission_id: str, payload: RevisionPayload):
    result = await db.submissions.update_one(
        {"_id": ObjectId(submission_id)},
        {"$set": {"status": payload.status, "feedback": payload.feedback}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    return {"message": "Success"}


@app.post("/api/courses/create")
async def create_course(course: CourseCreate):
    course_dict = course.dict()
    course_dict["students_count"] = 0
    result = await db.courses.insert_one(course_dict)
    return {"id": str(result.inserted_id)}


@app.post("/api/events/create", status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate):
    try:
        event_dict = event.dict()
        
        result = await db.events.insert_one(event_dict)
        
        if result.inserted_id:
            return {"message": "Event created successfully", "id": str(result.inserted_id)}
        
        raise HTTPException(status_code=400, detail="Failed to create event")
        
    except Exception as e:
        print(f"Error saving event: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: int):
    try:
        delete_result = await db.courses.delete_one({"id": course_id})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Course with id {course_id} not found"
            )

        events_result = await db.events.delete_many({"course_id": course_id})
        
        print(f"Deleted course {course_id} and {events_result.deleted_count} associated events")

        return {
            "status": "success",
            "message": "Course and all related events have been deleted",
            "details": {
                "course_id": course_id,
                "deleted_events_count": events_result.deleted_count
            }
        }

    except Exception as e:
        print(f"Error deleting course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An error occurred while deleting the course"
        )


@app.get("/api/submissions/teacher/{user_id}/stats")
async def get_teacher_submission_stats(user_id: str):
    approved_count = await db.submissions.count_documents({"status": "approved"})
    revision_count = await db.submissions.count_documents({"status": "needs_revision"})
    pending_count = await db.submissions.count_documents({"status": "pending"})
    
    return {
        "approved": approved_count,
        "needs_revision": revision_count,
        "pending": pending_count
    }


@app.get("/api/submissions/status")
async def get_submission_status(user_id: int, lesson_id: str):

    submission = await db.submissions.find_one({
        "user_id": int(user_id),
        "lesson_id": lesson_id
    })

    if not submission:
        return {"status": None, "feedback": ""}

    return {
        "status": submission.get("status"),
        "feedback": submission.get("feedback", "")
    }