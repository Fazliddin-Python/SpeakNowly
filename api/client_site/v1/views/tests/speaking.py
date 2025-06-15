# app/api/client_site/v1/views/tests/speaking.py

import logging
import os
import aiofiles
import uuid
from typing import Optional, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status, Request, UploadFile, File, Form
from tortoise.exceptions import DoesNotExist

from models.transactions import TransactionType
from ...serializers.tests import SpeakingResponseType, Questions, QuestionPart, Analyse
from utils.auth.auth import get_current_user
from utils.i18n import get_translation
from utils.check_tokens import check_user_tokens
from services.chatgpt.integration import ChatGPTIntegration
from services.analyses.speaking_analyse_service import SpeakingAnalyseService

from models.tests.speaking import (
    Speaking,
    SpeakingQuestion,
    SpeakingAnswer,
    SpeakingPart,
    SpeakingStatus,
)
from models.analyses import SpeakingAnalyse
from config import BASE_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


def audit_action(action: str):
    def wrapper(request: Request, user=Depends(get_current_user)):
        logger.info(f"User {user.id} action={action} path={request.url.path}")
        return user
    return wrapper


def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    return user


async def build_speaking_response(test: Speaking) -> SpeakingResponseType:
    qs = await SpeakingQuestion.filter(speaking_id=test.id)
    q_map = {
        f"part{q.part.name[-1].lower()}": QuestionPart(id=q.id, title=q.title, content=q.content)
        for q in qs
    }

    analyse_obj: Optional[Analyse] = None
    # Analyse only if already COMPLETED
    if test.status == SpeakingStatus.COMPLETED.value:
        rec = await SpeakingAnalyse.get_or_none(speaking_id=test.id)
        if rec:
            analyse_obj = Analyse(
                id=rec.id,
                speaking=rec.speaking_id,
                feedback=rec.feedback or "",
                overall_band_score=str(rec.overall_band_score or ""),
                fluency_and_coherence_score=str(rec.fluency_and_coherence_score or ""),
                fluency_and_coherence_feedback=rec.fluency_and_coherence_feedback or "",
                lexical_resource_score=str(rec.lexical_resource_score or ""),
                lexical_resource_feedback=rec.lexical_resource_feedback or "",
                grammatical_range_and_accuracy_score=str(rec.grammatical_range_and_accuracy_score or ""),
                grammatical_range_and_accuracy_feedback=rec.grammatical_range_and_accuracy_feedback or "",
                pronunciation_score=str(rec.pronunciation_score or ""),
                pronunciation_feedback=rec.pronunciation_feedback or "",
            )

    return SpeakingResponseType(
        id=test.id,
        start_time=test.start_time,
        end_time=test.end_time,
        created_at=test.created_at,
        updated_at=test.updated_at,
        status=test.status,
        questions=Questions(**q_map),
        analyse=analyse_obj,
    )


@router.post(
    "/start/",
    response_model=SpeakingResponseType,
    status_code=status.HTTP_201_CREATED,
)
async def create_speaking_test(
    request: Request,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("create_speaking_test")),
):
    try:
        await check_user_tokens(user, TransactionType.TEST_SPEAKING, request, t)
        speaking = await Speaking.create(
            user_id=user.id,
            start_time=datetime.now(timezone.utc),
            status=SpeakingStatus.STARTED.value,
        )

        chatgpt = ChatGPTIntegration()
        gen = await chatgpt.generate_speaking_questions()
        for part, title_key, q_key in [
            (SpeakingPart.PART_1, "part1_title", "part1_question"),
            (SpeakingPart.PART_2, "part2_title", "part2_question"),
            (SpeakingPart.PART_3, "part3_title", "part3_question"),
        ]:
            if title_key not in gen or q_key not in gen:
                logger.error("Missing keys in generated questions: %s", gen)
                raise HTTPException(status_code=500, detail=t["internal_error"])
            await SpeakingQuestion.create(
                speaking_id=speaking.id,
                part=part,
                title=gen[title_key],
                content=gen[q_key],
            )
        return await build_speaking_response(speaking)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error in create_speaking_test")
        raise HTTPException(status_code=500, detail=t["internal_error"])


@router.post(
    "/{session_id}/answers/",
    response_model=SpeakingResponseType,
    status_code=status.HTTP_201_CREATED,
)
async def submit_speaking_answers(
    session_id: int,
    part1_audio: UploadFile = File(None),
    part2_audio: UploadFile = File(None),
    part3_audio: UploadFile = File(None),
    is_finished: bool = Form(True),
    is_cancelled: bool = Form(False),
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("submit_speaking_answers")),
):
    # Check test and ownership
    try:
        test = await Speaking.get(id=session_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail=t["not_found"])
    if test.user_id != user.id:
        raise HTTPException(status_code=403, detail=t["permission_denied"])

    qs = await SpeakingQuestion.filter(speaking_id=session_id)
    if not qs:
        raise HTTPException(status_code=400, detail="No questions found for this speaking session")

    # Cancel
    if is_cancelled:
        test.status = SpeakingStatus.CANCELLED.value
        await test.save(update_fields=["status"])
        return await build_speaking_response(test)

    # Block repeated submission
    already = await SpeakingAnswer.filter(question__speaking_id=session_id).exists()
    if already:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted your answers for this speaking test."
        )

    # Prepare folder and GPT
    upload_dir = os.path.join(BASE_DIR, "media", "user_answers")
    os.makedirs(upload_dir, exist_ok=True)
    chatgpt = ChatGPTIntegration()

    # Save audio, transcribe and save answers
    for upload_file, part_enum in [
        (part1_audio, SpeakingPart.PART_1),
        (part2_audio, SpeakingPart.PART_2),
        (part3_audio, SpeakingPart.PART_3),
    ]:
        if not upload_file or not upload_file.filename:
            continue

        if upload_file.content_type not in ("audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"):
            raise HTTPException(status_code=400, detail=t["invalid_audio_type"])

        ext = os.path.splitext(upload_file.filename)[1]
        filename = f"speaking_{session_id}_{part_enum.name}_{uuid.uuid4()}{ext}"
        dest_path = os.path.join(upload_dir, filename)

        content = await upload_file.read()
        async with aiofiles.open(dest_path, "wb") as out_f:
            await out_f.write(content)

        audio_url = f"/media/user_answers/{filename}"
        try:
            text = await chatgpt.transcribe_audio(dest_path)
        except Exception:
            logger.exception("Transcription failed for %s part %s", session_id, part_enum)
            text = ""

        question_obj = await SpeakingQuestion.get(speaking_id=session_id, part=part_enum)
        await SpeakingAnswer.create(
            question_id=question_obj.id,
            audio_answer=audio_url,
            text_answer=text,
        )

    # Complete the test
    test.status = SpeakingStatus.COMPLETED.value
    test.end_time = datetime.now(timezone.utc)
    await test.save(update_fields=["status", "end_time"])

    # Run analysis
    await SpeakingAnalyseService.analyse(session_id)

    return await build_speaking_response(test)


@router.get(
    "/{session_id}/",
    response_model=SpeakingResponseType,
)
async def retrieve_speaking_detail(
    session_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("retrieve_speaking_detail")),
):
    try:
        test = await Speaking.get(id=session_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail=t["not_found"])
    if test.user_id != user.id:
        raise HTTPException(status_code=403, detail=t["permission_denied"])
    return await build_speaking_response(test)

