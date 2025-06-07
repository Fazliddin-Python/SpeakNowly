from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

# --- History Serializers ---
class BaseHistorySerializer(BaseModel):
    type: Literal["Listening", "Reading", "Writing", "Speaking"]
    score: float
    created_at: datetime
    duration: Optional[int]

class ReadingHistorySerializer(BaseHistorySerializer):
    type: Literal["Reading"] = "Reading"

class ListeningHistorySerializer(BaseHistorySerializer):
    type: Literal["Listening"] = "Listening"

class WritingHistorySerializer(BaseHistorySerializer):
    type: Literal["Writing"] = "Writing"

class SpeakingHistorySerializer(BaseHistorySerializer):
    type: Literal["Speaking"] = "Speaking"

HistoryItem = (
    ReadingHistorySerializer
    | ListeningHistorySerializer
    | WritingHistorySerializer
    | SpeakingHistorySerializer
)

# --- User Progress Serializer ---
class LatestAnalysis(BaseModel):
    listening: Optional[float]
    speaking: Optional[float]
    writing: Optional[float]
    reading: Optional[float]

class UserProgressSerializer(BaseModel):
    latest_analysis: LatestAnalysis
    highest_score: float

# --- Main Stats Serializer ---
class MainStatsSerializer(BaseModel):
    reading: int
    speaking: int
    writing: int
    listening: int

