from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
from datetime import datetime


class CommentBaseSerializer(BaseModel):
    """Base serializer for a comment."""
    text: str = Field(..., description="Comment text")
    rate: float = Field(..., ge=0, le=5, description="Rating (0 to 5)")

    @validator("text")
    def validate_text(cls, value):
        if len(value.strip()) == 0:
            raise ValueError("Comment text cannot be empty")
        if len(value) > 500:
            raise ValueError("Comment text cannot exceed 500 characters")
        return value


class CommentCreateSerializer(CommentBaseSerializer):
    """Serializer for creating a comment."""
    pass


class CommentUpdateSerializer(BaseModel):
    """Serializer for updating a comment."""
    text: Optional[str] = Field(None, description="Updated comment text")
    rate: Optional[float] = Field(None, ge=0, le=5, description="Updated rating (0 to 5)")

    @validator("text")
    def validate_text(cls, value):
        if value and len(value.strip()) == 0:
            raise ValueError("Comment text cannot be empty")
        if value and len(value) > 500:
            raise ValueError("Comment text cannot exceed 500 characters")
        return value


class CommentListSerializer(BaseModel):
    """Serializer for listing comments."""
    id: int = Field(..., description="Unique identifier of the comment")
    text: str = Field(..., description="Comment text")
    user: Dict[str, Optional[str]] = Field(..., description="User details")
    rate: float = Field(..., description="Rating")
    status: str = Field(..., description="Status of the comment")
    created_at: datetime = Field(..., description="Timestamp when the comment was created")

    class Config:
        from_attributes = True


class CommentDetailSerializer(BaseModel):
    """Serializer for detailed comment information."""
    id: int = Field(..., description="Unique identifier of the comment")
    text: str = Field(..., description="Comment text")
    user_id: int = Field(..., description="ID of the user who created the comment")
    rate: float = Field(..., description="Rating")
    status: str = Field(..., description="Status of the comment")
    created_at: datetime = Field(..., description="Timestamp when the comment was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the comment was last updated")

    class Config:
        from_attributes = True