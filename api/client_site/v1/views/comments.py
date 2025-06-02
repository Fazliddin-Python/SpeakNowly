import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict
from tortoise.exceptions import DoesNotExist

from models.comments import Comment
from ..serializers.comments import (
    CommentCreateSerializer,
    CommentUpdateSerializer,
    CommentListSerializer,
    CommentDetailSerializer,
)
from tasks.comments_tasks import notify_admin_about_comment
from utils.auth.auth import get_current_user
from utils.i18n import get_translation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[CommentListSerializer])
async def get_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1)
):
    """
    List comments in a paginated fashion.
    """
    offset = (page - 1) * page_size
    comments = (
        await Comment.all()
        .offset(offset)
        .limit(page_size)
        .prefetch_related("user")
    )
    logger.info("Fetched %d comments (page %d)", len(comments), page)

    result: List[Dict] = []
    for comment in comments:
        user = await comment.user
        result.append({
            "id": comment.id,
            "text": comment.text,
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "photo": user.photo,
            },
            "rate": comment.rate,
            "status": comment.status,
            "created_at": comment.created_at,
        })
    return result


@router.post(
    "/",
    response_model=CommentDetailSerializer,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment_data: CommentCreateSerializer,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """
    Create a new comment as the current user and notify admin.
    """
    data = comment_data.dict()
    data["user_id"] = user.id
    data["status"] = "active"
    comment = await Comment.create(**data)
    logger.info("User %s created comment %s", user.id, comment.id)
    notify_admin_about_comment.delay(comment.id)

    user_obj = await comment.user
    return {
        "id": comment.id,
        "text": comment.text,
        "user": {
            "id": user_obj.id,
            "first_name": user_obj.first_name,
            "last_name": user_obj.last_name,
            "photo": user_obj.photo,
        },
        "rate": comment.rate,
        "status": comment.status,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at if hasattr(comment, "updated_at") else None,
        "message": t.get("comment_created", "Comment created successfully"),
    }


@router.get("/{comment_id}/", response_model=CommentDetailSerializer)
async def get_comment(
    comment_id: int,
    t: dict = Depends(get_translation),
):
    """
    Retrieve a single comment by its ID.
    """
    try:
        comment = await Comment.get(id=comment_id).prefetch_related("user")
        logger.info("Fetched comment %s", comment_id)
        user = await comment.user
        return {
            "id": comment.id,
            "text": comment.text,
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "photo": user.photo,
            },
            "rate": comment.rate,
            "status": comment.status,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at if hasattr(comment, "updated_at") else None,
            "message": None,
        }
    except DoesNotExist:
        logger.warning("Comment %s not found", comment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t.get("comment_not_found", "Comment not found")
        )


@router.put("/{comment_id}/", response_model=CommentDetailSerializer)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdateSerializer,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """
    Update an existing comment. Only fields provided will be changed.
    """
    try:
        comment = await Comment.get(id=comment_id)
        if comment.user_id != user.id:
            logger.warning("User %s unauthorized to update comment %s", user.id, comment_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=t.get("permission_denied", "You do not have permission to modify this comment")
            )

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

        user_obj = await comment.user
        return {
            "id": comment.id,
            "text": comment.text,
            "user": {
                "id": user_obj.id,
                "first_name": user_obj.first_name,
                "last_name": user_obj.last_name,
                "photo": user_obj.photo,
            },
            "rate": comment.rate,
            "status": comment.status,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at if hasattr(comment, "updated_at") else None,
            "message": t.get("comment_updated", "Comment updated successfully"),
        }
    except DoesNotExist:
        logger.warning("Comment %s not found for update", comment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t.get("comment_not_found", "Comment not found")
        )


@router.delete("/{comment_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """
    Delete a comment by its ID. Only the author can delete.
    """
    try:
        comment = await Comment.get(id=comment_id)
        if comment.user_id != user.id:
            logger.warning("User %s unauthorized to delete comment %s", user.id, comment_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=t.get("permission_denied", "You do not have permission to delete this comment")
            )
        await comment.delete()
        logger.info("Comment %s deleted", comment_id)
    except DoesNotExist:
        logger.warning("Comment %s not found for deletion", comment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t.get("comment_not_found", "Comment not found")
        )
