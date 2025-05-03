from pydantic import BaseModel
from typing import Optional, List


class ListeningSerializer(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True


class ListeningPartSerializer(BaseModel):
    id: int
    listening_id: int
    part_number: int
    audio_file: str

    class Config:
        from_attributes = True


class ListeningSectionSerializer(BaseModel):
    id: int
    part_id: int
    section_number: int
    start_index: int
    end_index: int
    question_type: str
    question_text: Optional[str]
    options: Optional[List[str]]

    class Config:
        from_attributes = True


class ListeningQuestionSerializer(BaseModel):
    id: int
    section_id: int
    index: int
    options: Optional[List[str]]
    correct_answer: str

    class Config:
        from_attributes = True


class UserListeningSessionSerializer(BaseModel):
    id: int
    user_id: int
    exam_id: int
    status: str
    start_time: str
    end_time: Optional[str]

    class Config:
        from_attributes = True


class UserResponseSerializer(BaseModel):
    id: int
    session_id: int
    user_id: int
    question_id: int
    user_answer: str
    is_correct: bool
    score: int

    class Config:
        from_attributes = True