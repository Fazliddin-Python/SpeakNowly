from pydantic import BaseModel
from typing import Optional

class TopUserIELTSSerializer(BaseModel):
    """Serializer for top user IELTS score."""
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    ielts_score: float
    image: Optional[str]