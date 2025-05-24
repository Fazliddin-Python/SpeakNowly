from turtle import st
from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime

# --- For creation (POST) ---
class ListeningCreateSerializer(BaseModel):
    title: str
    description: str

class ListeningSectionCreateSerializer(BaseModel):
    part_id: int
    section_number: int
    start_index: int
    end_index: int
    question_type: str
    question_text: Optional[str]
    options: Optional[List[str]]

class ListeningQuestionCreateSerializer(BaseModel):
    section_id: int
    index: int
    options: Optional[List[str]]
    correct_answer: str

# --- For reading (GET) ---
class ListeningSerializer(BaseModel):
    id: int
    title: str
    description: str

class ListeningPartSerializer(BaseModel):
    id: int
    listening_id: int
    part_number: int
    audio_file: str

class ListeningSectionSerializer(BaseModel):
    id: int
    part_id: int
    section_number: int
    start_index: int
    end_index: int
    question_type: str
    question_text: Optional[str]
    options: Optional[List[str]]

class ListeningQuestionSerializer(BaseModel):
    section_id: int
    index: int
    options: Optional[List[str]]
    correct_answer: str

class UserListeningSessionSerializer(BaseModel):
    id: int
    user_id: int
    exam_id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]

class UserResponseSerializer(BaseModel):
    session_id: int
    user_id: int
    question_id: int
    user_answer: str
    is_correct: bool
    score: int