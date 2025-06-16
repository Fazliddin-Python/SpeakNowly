from pydantic import BaseModel
from typing import Optional

class TopUserIELTSSerializer(BaseModel):
    """Serializer for top user IELTS score."""
    first_name: str
    last_name: str
    ielts_score: float
    image: Optional[str]