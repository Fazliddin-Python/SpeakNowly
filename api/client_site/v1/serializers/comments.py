from email import message
from pydantic import Field, field_validator
from typing import Optional, Dict
from datetime import datetime

from .base import BaseSerializer, SafeSerializer


class CommentBaseSerializer(BaseSerializer):
    """
    Base serializer for a comment.
    """
    text: str = Field(..., description="Comment text")
    rate: float = Field(..., ge=1, le=5, description="Rating (1 to 5)")

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """
        Ensure that 'text' is not empty or whitespace-only, and does not exceed 500 characters.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("Comment text cannot be empty or whitespace")
        if len(stripped) > 500:
            raise ValueError("Comment text cannot exceed 500 characters")
        return stripped


class CommentCreateSerializer(CommentBaseSerializer):
    """
    Serializer for creating a comment.
    (Inherits all validations from CommentBaseSerializer.)
    """
    pass


class CommentUpdateSerializer(BaseSerializer):
    """
    Serializer for updating a comment.
    Both 'text' and 'rate' are optional, but if provided must satisfy base constraints.
    """
    text: Optional[str] = Field(None, description="Updated comment text")
    rate: Optional[float] = Field(None, ge=1, le=5, description="Updated rating (1 to 5)")

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, value: Optional[str]) -> Optional[str]:
        """
        If 'text' is provided, ensure it is not empty/whitespace-only and ≤ 500 characters.
        """
        if value is None:
            return None 
        stripped = value.strip()
        if not stripped:
            raise ValueError("Comment text cannot be empty or whitespace")
        if len(stripped) > 500:
            raise ValueError("Comment text cannot exceed 500 characters")
        return stripped

    @field_validator("rate")
    @classmethod
    def validate_rate(cls, value: Optional[float]) -> Optional[float]:
        """
        If 'rate' is provided, ensure it lies between 1 and 5.
        """
        if value is None:
            return None
        if not (1 <= value <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return value


class CommentListUserSerializer(BaseSerializer):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    photo: Optional[str]


class CommentListSerializer(SafeSerializer):
    """
    Serializer for listing comments.
    """
    text: str = Field(..., description="Comment text")
    user: CommentListUserSerializer
    rate: float = Field(..., description="Rating of the comment")
    status: str = Field(..., description="Status of the comment")


class CommentDetailSerializer(SafeSerializer):
    """
    Serializer for detailed comment information.
    """
    text: str = Field(..., description="Comment text")
    user: CommentListUserSerializer
    rate: float = Field(..., description="Rating of the comment")
    status: str = Field(..., description="Status of the comment")
    created_at: datetime = Field(..., description="When the comment was created")
    updated_at: Optional[datetime] = Field(None, description="When the comment was updated")
    message: Optional[str] = Field(None, description="Optional message for the comment")
