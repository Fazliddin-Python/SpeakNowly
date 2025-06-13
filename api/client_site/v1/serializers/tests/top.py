from pydantic import BaseModel
from typing import Optional

class TopUserIELTSSerializer(BaseModel):
    first_name: str
    last_name: str
    ielts_score: float
    image: Optional[str]