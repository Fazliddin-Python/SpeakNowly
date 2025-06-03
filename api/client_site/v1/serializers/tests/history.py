from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class TestTypeEnum(str, Enum):
    READING_ENG   = "reading"
    SPEAKING_ENG  = "speaking"
    WRITING_ENG   = "writing"
    LISTENING_ENG = "listening"


class HistoryItem(BaseModel):
    type: TestTypeEnum
    score: float
    created_at: datetime
    duration: Optional[int]
