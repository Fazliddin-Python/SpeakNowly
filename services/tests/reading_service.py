import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from models.tests.reading import Passage, Question, Variant, Reading, Answer as ReadingAnswer
from models.users import User
from utils.check_tokens import check_user_tokens  # if you have token logic
from services.analyses.reading_analyse_service import ReadingAnalyseService

logger = logging.getLogger(__name__)


class ReadingService:
    """
    Service layer for Reading: handles CRUD for passages, questions, variants, 
    plus business logic for starting/submitting/cancelling/restarting a reading session.
    """

    # -----------------------------
    #   Passage CRUD (admin)
    # -----------------------------

    @staticmethod
    async def list_passages(t: dict) -> List[Passage]:
        return await Passage.all()

    @staticmethod
    async def get_passage(passage_id: int, t: dict) -> Passage:
        passage = await Passage.get_or_none(id=passage_id)
        if not passage:
            logger.warning(f"Passage not found (id={passage_id})")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["passage_not_found"])
        return passage

    @staticmethod
    async def create_passage(data: Dict[str, Any], t: dict) -> Passage:
        # ensure number is unique
        exists = await Passage.filter(number=data["number"]).exists()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["passage_number_exists"]
            )
        new_passage = await Passage.create(**data)
        logger.info(f"Created Passage id={new_passage.id}")
        return new_passage

    @staticmethod
    async def update_passage(passage_id: int, data: Dict[str, Any], t: dict) -> Passage:
        if "number" in data:
            exists = await Passage.filter(number=data["number"]).exclude(id=passage_id).exists()
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=t["passage_number_exists"]
                )
        passage = await Passage.get_or_none(id=passage_id)
        if not passage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["passage_not_found"])
        for field, value in data.items():
            setattr(passage, field, value)
        await passage.save()
        logger.info(f"Updated Passage id={passage_id}")
        return passage

    @staticmethod
    async def delete_passage(passage_id: int, t: dict) -> None:
        deleted = await Passage.filter(id=passage_id).delete()
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["passage_not_found"])
        logger.info(f"Deleted Passage id={passage_id}")

    # -----------------------------
    #   Question CRUD (admin)
    # -----------------------------

    @staticmethod
    async def list_questions(t: dict) -> List[Question]:
        return await Question.all().prefetch_related("variants")

    @staticmethod
    async def get_question(question_id: int, t: dict) -> Question:
        question = await Question.get_or_none(id=question_id).prefetch_related("variants")
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["question_not_found"])
        return question

    @staticmethod
    async def create_question(data: Dict[str, Any], t: dict) -> Question:
        # ensure the parent passage exists
        passage = await Passage.get_or_none(id=data["passage_id"])
        if not passage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["passage_not_found"])
        new_question = await Question.create(**data)
        logger.info(f"Created Question id={new_question.id}")
        return new_question

    @staticmethod
    async def update_question(question_id: int, data: Dict[str, Any], t: dict) -> Question:
        question = await Question.get_or_none(id=question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["question_not_found"])
        for field, value in data.items():
            setattr(question, field, value)
        await question.save()
        logger.info(f"Updated Question id={question_id}")
        return question

    @staticmethod
    async def delete_question(question_id: int, t: dict) -> None:
        deleted = await Question.filter(id=question_id).delete()
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["question_not_found"])
        logger.info(f"Deleted Question id={question_id}")

    # -----------------------------
    #   Variant CRUD (admin)
    # -----------------------------

    @staticmethod
    async def list_variants(t: dict) -> List[Variant]:
        return await Variant.all()

    @staticmethod
    async def get_variant(variant_id: int, t: dict) -> Variant:
        variant = await Variant.get_or_none(id=variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["variant_not_found"])
        return variant

    @staticmethod
    async def create_variant(data: Dict[str, Any], t: dict) -> Variant:
        question = await Question.get_or_none(id=data["question_id"])
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["question_not_found"])
        new_variant = await Variant.create(**data)
        logger.info(f"Created Variant id={new_variant.id}")
        return new_variant

    @staticmethod
    async def update_variant(variant_id: int, data: Dict[str, Any], t: dict) -> Variant:
        variant = await Variant.get_or_none(id=variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["variant_not_found"])
        for field, value in data.items():
            setattr(variant, field, value)
        await variant.save()
        logger.info(f"Updated Variant id={variant_id}")
        return variant

    @staticmethod
    async def delete_variant(variant_id: int, t: dict) -> None:
        deleted = await Variant.filter(id=variant_id).delete()
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["variant_not_found"])
        logger.info(f"Deleted Variant id={variant_id}")

    # -----------------------------
    #   Reading session / user flow
    # -----------------------------

    @staticmethod
    async def start_reading(user_id: int) -> Tuple[Reading, Optional[str]]:
        passages = await Passage.all()
        if not passages:
            return None, "no_passages"
        new_session = await Reading.create(
            user_id=user_id,
            status="pending",
            start_time=datetime.utcnow(),
            score=0.0,
            duration=60,
        )
        await new_session.passages.add(*passages)
        return new_session, None

    @staticmethod
    async def get_reading(session_id: int) -> Optional[Reading]:
        return await Reading.get_or_none(id=session_id).prefetch_related("passages", "user")

    @staticmethod
    async def submit_answers(
        session_id: int, user_id: int, answers: List[Any]
    ) -> Tuple[float, Optional[str]]:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return 0.0, "session_not_found"
        if session.status == "completed":
            return 0.0, "already_completed"

        total_score = 0.0
        async with in_transaction():
            for ans in answers:
                question_id = ans.question_id
                raw_answer = ans.answer
                question = await Question.get_or_none(id=question_id)
                if not question:
                    return 0.0, f"question_{question_id}"

                correct_text = None
                correct_variant = await question.variants.filter(is_correct=True).first()
                if correct_variant:
                    correct_text = correct_variant.text

                is_correct = False
                if correct_text is not None and raw_answer == correct_text:
                    is_correct = True
                    total_score += question.score

                await ReadingAnswer.create(
                    user_id=user_id,
                    question_id=question_id,
                    reading_id=session_id,
                    text=raw_answer,
                    explanation=None,
                    is_correct=is_correct,
                    correct_answer=correct_text,
                    status="answered"
                )
            session.status = "completed"
            session.end_time = datetime.utcnow()
            session.score = total_score
            await session.save()

        try:
            await ReadingAnalyseService.analyse_reading(session_id)
        except Exception as e:
            logger.error(f"Failed to analyse reading session {session_id}: {e}")

        return total_score, None

    @staticmethod
    async def cancel_reading(session_id: int, user_id: int) -> bool:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return False
        session.status = "cancelled"
        session.end_time = datetime.utcnow()
        await session.save()
        return True

    @staticmethod
    async def restart_reading(session_id: int, user_id: int) -> Tuple[Optional[Reading], Optional[str]]:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return None, "session_not_found"
        if session.status != "completed":
            return None, "not_completed"
        await ReadingAnswer.filter(reading_id=session_id, user_id=user_id).delete()
        session.status = "pending"
        session.start_time = datetime.utcnow()
        session.end_time = None
        session.score = 0.0
        await session.save()
        return session, None

    @staticmethod
    async def list_readings_for_user(user_id: int) -> List[Reading]:
        return await Reading.filter(user_id=user_id).all()

    @staticmethod
    async def list_passages_in_reading(session_id: int) -> List[Passage]:
        session = await Reading.get_or_none(id=session_id).prefetch_related("passages")
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return await session.passages.all()

    @staticmethod
    async def analyse_reading(session_id: int, user_id: int) -> Dict[str, Any]:
        session = await Reading.get_or_none(id=session_id, user_id=user_id).prefetch_related("passages")
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        result = []
        for passage in await session.passages.all():
            questions_qs = await passage.questions.all()
            questions_data = []
            for question in questions_qs:
                ua = await ReadingAnswer.get_or_none(
                    question_id=question.id, user_id=user_id, reading_id=session_id
                )
                questions_data.append({
                    "id": question.id,
                    "text": question.text,
                    "type": question.type,
                    "answers": [
                        {"id": v.id, "text": v.text, "is_correct": v.is_correct}
                        for v in await question.variants.all()
                    ],
                    "user_answer": ua.text if ua and ua.text else (ua.variant_id if ua and ua.variant_id else None),
                    "is_correct": ua.is_correct if ua else False,
                    "correct_answer": ua.correct_answer if ua else None,
                })
            result.append({
                "id": passage.id,
                "title": passage.title,
                "text": passage.text,
                "questions": questions_data,
            })
        return {"results": result}