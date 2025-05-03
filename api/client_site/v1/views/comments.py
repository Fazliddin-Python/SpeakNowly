from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from tortoise.exceptions import DoesNotExist

from models.comments import Comment
from ..serializers.comments import (
    CommentSerializer,
    CommentCreateSerializer,
    CommentListSerializer,
)

router = APIRouter(prefix="/api/v1/comments", tags=["Comments"])


@router.get("/", response_model=List[CommentListSerializer])
async def get_comments(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1)):
    """
    Get a paginated list of comments.
    """
    offset = (page - 1) * page_size
    comments = await Comment.all().offset(offset).limit(page_size).prefetch_related("user")
    return [
        {
            "id": comment.id,
            "text": comment.text,
            "user": {
                "id": comment.user.id,
                "first_name": comment.user.first_name,
                "last_name": comment.user.last_name,
                "photo": comment.user.photo,
            },
            "rate": comment.rate,
            "status": comment.status,
        }
        for comment in comments
    ]


@router.post("/", response_model=CommentSerializer)
async def create_comment(comment_data: CommentCreateSerializer):
    """
    Create a new comment.
    """
    comment = await Comment.create(**comment_data.dict())
    return comment


@router.get("/{comment_id}/", response_model=CommentSerializer)
async def get_comment(comment_id: int):
    """
    Get a single comment by ID.
    """
    try:
        comment = await Comment.get(id=comment_id).prefetch_related("user")
        return {
            "id": comment.id,
            "text": comment.text,
            "user_id": comment.user.id,
            "rate": comment.rate,
            "status": comment.status,
        }
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")


@router.delete("/{comment_id}/", status_code=204)
async def delete_comment(comment_id: int):
    """
    Delete a comment by ID.
    """
    deleted_count = await Comment.filter(id=comment_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"message": "Comment deleted successfully"}