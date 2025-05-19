import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from tortoise.exceptions import DoesNotExist

from models.comments import Comment
from ..serializers.comments import (
    CommentCreateSerializer,
    CommentUpdateSerializer,
    CommentListSerializer,
    CommentDetailSerializer,
)
from tasks.comments_tasks import notify_admin_about_comment
from utils.i18n import get_translation

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CommentListSerializer])
async def get_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1)
):
    """
    Get a paginated list of comments.
    """
    offset = (page - 1) * page_size
    comments = await Comment.all().offset(offset).limit(page_size).prefetch_related("user")
    logger.info("Fetched %d comments (page %d)", len(comments), page)
    return [
        {
            "id": comment.id,
            "text": comment.text,
            "user": {
                "id": comment.user.id,
                "first_name": getattr(comment.user, "first_name", None),
                "last_name": getattr(comment.user, "last_name", None),
                "photo": getattr(comment.user, "photo", None),
            },
            "rate": comment.rate,
            "status": comment.status,
            "created_at": comment.created_at,
        }
        for comment in comments
    ]


@router.post("/", response_model=CommentDetailSerializer, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreateSerializer,
    t: dict = Depends(get_translation)
):
    """
    Create a new comment and notify admin asynchronously.
    """
    comment = await Comment.create(**comment_data.dict())
    logger.info("User %s created comment %s", comment.user_id, comment.id)
    notify_admin_about_comment.delay(comment.id)
    return {
        "id": comment.id,
        "text": comment.text,
        "user_id": comment.user_id,
        "rate": comment.rate,
        "status": comment.status,
        "created_at": comment.created_at,
        "message": t.get("comment_created", "Comment created successfully"),
    }


@router.get("/{comment_id}/", response_model=CommentDetailSerializer)
async def get_comment(
    comment_id: int,
    t: dict = Depends(get_translation)
):
    """
    Get a single comment by ID.
    """
    try:
        comment = await Comment.get(id=comment_id).prefetch_related("user")
        logger.info("Fetched comment %s", comment_id)
        return {
            "id": comment.id,
            "text": comment.text,
            "user_id": comment.user.id,
            "rate": comment.rate,
            "status": comment.status,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
        }
    except DoesNotExist:
        logger.warning("Comment %s not found", comment_id)
        raise HTTPException(status_code=404, detail=t.get("comment_not_found", "Comment not found"))


@router.put("/{comment_id}/", response_model=CommentDetailSerializer)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdateSerializer,
    t: dict = Depends(get_translation)
):
    """
    Update an existing comment.
    """
    try:
        comment = await Comment.get(id=comment_id)
        updated = False
        if comment_data.text is not None:
            comment.text = comment_data.text
            updated = True
        if comment_data.rate is not None:
            comment.rate = comment_data.rate
            updated = True
        if updated:
            await comment.save()
            logger.info("Comment %s updated", comment_id)
        return {
            "id": comment.id,
            "text": comment.text,
            "user_id": comment.user_id,
            "rate": comment.rate,
            "status": comment.status,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "message": t.get("comment_updated", "Comment updated successfully"),
        }
    except DoesNotExist:
        logger.warning("Comment %s not found for update", comment_id)
        raise HTTPException(status_code=404, detail=t.get("comment_not_found", "Comment not found"))


@router.delete("/{comment_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    t: dict = Depends(get_translation)
):
    """
    Delete a comment by ID.
    """
    deleted_count = await Comment.filter(id=comment_id).delete()
    if not deleted_count:
        logger.warning("Comment %s not found for deletion", comment_id)
        raise HTTPException(status_code=404, detail=t.get("comment_not_found", "Comment not found"))
    logger.info("Comment %s deleted", comment_id)
    return {"message": t.get("comment_deleted", "Comment deleted successfully")}