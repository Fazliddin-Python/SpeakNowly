import logging, os
from typing import Optional, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status, Request, UploadFile, File, Form
from tortoise.exceptions import DoesNotExist

from ...serializers.tests import SpeakingResponseType, Questions, QuestionPart, Analyse
from utils.auth.auth import get_current_user
from utils.i18n import get_translation
from utils.check_tokens import check_user_tokens
from services.chatgpt.integration import ChatGPTIntegration
from services.analyses.speaking_analyse_service import SpeakingAnalyseService

from models.tests.speaking import Speaking, SpeakingQuestions, SpeakingAnswers, SpeakingPart, SpeakingStatus
from models.tests.test_type import TestTypeEnum
from models.analyses import SpeakingAnalyse

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


@router.post("/", response_model=SpeakingResponseType, status_code=status.HTTP_201_CREATED)
async def create_speaking_test(
    request: Request,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("create_speaking_test")),
):
    # 1) Проверка и списание токенов
    await check_user_tokens(user, TestTypeEnum.SPEAKING_ENG, request, t)

    # 2) Создаём запись
    speaking = await Speaking.create(
        user_id=user.id,
        start_time=datetime.now(timezone.utc),
        status=SpeakingStatus.STARTED.value
    )

    # 3) Генерим вопросы через GPT
    chatgpt = ChatGPTIntegration(None)
    try:
        gen = await chatgpt.generate_speaking_questions()
    except HTTPException:
        raise HTTPException(status_code=500, detail=t["internal_error"])

    for part, title_key, q_key in [
        (SpeakingPart.PART_1, "part1_title", "part1_question"),
        (SpeakingPart.PART_2, "part2_title", "part2_question"),
        (SpeakingPart.PART_3, "part3_title", "part3_question"),
    ]:
        await SpeakingQuestions.create(
            speaking_id=speaking.id,
            part=part,
            title=gen[title_key],
            content=gen[q_key],
        )

    # 4) Собираем ответ
    qs = await SpeakingQuestions.filter(speaking_id=speaking.id)
    q_map = {
        f"part{q.part.name[-1].lower()}": QuestionPart(id=q.id, title=q.title, content=q.content)
        for q in qs
    }

    return SpeakingResponseType(
        id=speaking.id,
        start_time=speaking.start_time,
        end_time=None,
        created_at=speaking.created_at,
        updated_at=speaking.updated_at,
        status=speaking.status.value,
        questions=Questions(**q_map),
        analyse=None
    )


@router.post("/{speaking_id}/answers", response_model=SpeakingResponseType, status_code=status.HTTP_201_CREATED)
async def submit_speaking_answers(
    speaking_id: int,
    request: Request,
    part1_audio: Optional[UploadFile] = File(None),
    part2_audio: Optional[UploadFile] = File(None),
    part3_audio: Optional[UploadFile] = File(None),
    is_finished: bool = Form(True),
    is_cancelled: bool = Form(False),
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("submit_speaking_answers")),
):
    # Проверяем существование и авторство...
    try:
        test = await Speaking.get(id=speaking_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail=t["not_found"])
    if test.user_id != user.id:
        raise HTTPException(status_code=403, detail=t["permission_denied"])

    qs = await SpeakingQuestions.filter(speaking_id=speaking_id)
    if is_cancelled:
        # просто отмена
        test.status = SpeakingStatus.CANCELLED.value
        await test.save(update_fields=["status"])
        q_map = {
            f"part{q.part.name[-1].lower()}": QuestionPart(id=q.id, title=q.title, content=q.content)
            for q in qs
        }
        return SpeakingResponseType(
            id=test.id, start_time=test.start_time, end_time=test.end_time,
            created_at=test.created_at, updated_at=test.updated_at,
            status=test.status.value, questions=Questions(**q_map), analyse=None
        )

    # Сохраняем и транскрибируем аудио
    upload_dir = "uploads/speaking"
    os.makedirs(upload_dir, exist_ok=True)
    chatgpt = ChatGPTIntegration(None)
    for part_audio, part_enum in [
        (part1_audio, SpeakingPart.PART_1),
        (part2_audio, SpeakingPart.PART_2),
        (part3_audio, SpeakingPart.PART_3),
    ]:
        if part_audio:
            path = f"{upload_dir}/{speaking_id}_{part_enum.name}_{part_audio.filename}"
            async with open(path, "wb") as f:
                f.write(await part_audio.read())
            text = await chatgpt.transcribe_audio(path)
            await SpeakingAnswers.create(
                question_id=(await SpeakingQuestions.get(part=part_enum, speaking_id=speaking_id)).id,
                audio_answer=path,
                text_answer=text
            )

    # Завершаем тест
    test.status = SpeakingStatus.COMPLETED.value
    test.end_time = datetime.now(timezone.utc)
    await test.save(update_fields=["status", "end_time"])

    # Запускаем анализ
    analyse_rec = await SpeakingAnalyseService.analyse(speaking_id, None)

    # Собираем итоговый response
    q_map = {
        f"part{q.part.name[-1].lower()}": QuestionPart(id=q.id, title=q.title, content=q.content)
        for q in qs
    }
    analyse_obj = Analyse(
        id=analyse_rec.id,
        speaking=analyse_rec.speaking_id,
        feedback=analyse_rec.feedback,
        overall_band_score=str(analyse_rec.overall_band_score),
        fluency_and_coherence_score=str(analyse_rec.fluency_and_coherence_score),
        fluency_and_coherence_feedback=analyse_rec.fluency_and_coherence_feedback,
        lexical_resource_score=str(analyse_rec.lexical_resource_score),
        lexical_resource_feedback=analyse_rec.lexical_resource_feedback,
        grammatical_range_and_accuracy_score=str(analyse_rec.grammatical_range_and_accuracy_score),
        grammatical_range_and_accuracy_feedback=analyse_rec.grammatical_range_and_accuracy_feedback,
        pronunciation_score=str(analyse_rec.pronunciation_score),
        pronunciation_feedback=analyse_rec.pronunciation_feedback,
    )

    return SpeakingResponseType(
        id=test.id,
        start_time=test.start_time,
        end_time=test.end_time,
        created_at=test.created_at,
        updated_at=test.updated_at,
        status=test.status.value,
        questions=Questions(**q_map),
        analyse=analyse_obj
    )


@router.get("/{speaking_id}", response_model=SpeakingResponseType)
async def retrieve_speaking_detail(
    speaking_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("retrieve_speaking_detail")),
):
    try:
        test = await Speaking.get(id=speaking_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail=t["not_found"])
    if test.user_id != user.id:
        raise HTTPException(status_code=403, detail=t["permission_denied"])

    qs = await SpeakingQuestions.filter(speaking_id=speaking_id)
    q_map = {
        f"part{q.part.name[-1].lower()}": QuestionPart(id=q.id, title=q.title, content=q.content)
        for q in qs
    }

    analyse_obj = None
    rec = await SpeakingAnalyse.get_or_none(speaking_id=speaking_id)
    if rec:
        analyse_obj = Analyse(
            id=rec.id,
            speaking=rec.speaking_id,
            feedback=rec.feedback,
            overall_band_score=str(rec.overall_band_score),
            fluency_and_coherence_score=str(rec.fluency_and_coherence_score),
            fluency_and_coherence_feedback=rec.fluency_and_coherence_feedback,
            lexical_resource_score=str(rec.lexical_resource_score),
            lexical_resource_feedback=rec.lexical_resource_feedback,
            grammatical_range_and_accuracy_score=str(rec.grammatical_range_and_accuracy_score),
            grammatical_range_and_accuracy_feedback=rec.grammatical_range_and_accuracy_feedback,
            pronunciation_score=str(rec.pronunciation_score),
            pronunciation_feedback=rec.pronunciation_feedback,
        )

    return SpeakingResponseType(
        id=test.id,
        start_time=test.start_time,
        end_time=test.end_time,
        created_at=test.created_at,
        updated_at=test.updated_at,
        status=test.status.value,
        questions=Questions(**q_map),
        analyse=analyse_obj
    )
