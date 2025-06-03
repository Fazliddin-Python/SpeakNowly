import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from models.tests.reading import Passage, Question, Variant, Reading, Answer as ReadingAnswer, User
from utils.check_tokens import check_user_tokens  # if you have token logic

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
    async def list_passages() -> List[Passage]:
        return await Passage.all()

    @staticmethod
    async def get_passage(passage_id: int) -> Passage:
        passage = await Passage.get_or_none(id=passage_id)
        if not passage:
            logger.warning(f"Passage not found (id={passage_id})")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passage not found")
        return passage

    @staticmethod
    async def create_passage(data: Dict[str, Any]) -> Passage:
        # ensure number is unique
        exists = await Passage.get_or_none(number=data["number"])
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Passage with number {data['number']} already exists"
            )
        new_passage = await Passage.create(**data)
        logger.info(f"Created Passage id={new_passage.id}")
        return new_passage

    @staticmethod
    async def update_passage(passage_id: int, data: Dict[str, Any]) -> Passage:
        passage = await Passage.get_or_none(id=passage_id)
        if not passage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passage not found")
        for field, value in data.items():
            setattr(passage, field, value)
        await passage.save()
        logger.info(f"Updated Passage id={passage_id}")
        return passage

    @staticmethod
    async def delete_passage(passage_id: int) -> None:
        deleted = await Passage.filter(id=passage_id).delete()
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passage not found")
        logger.info(f"Deleted Passage id={passage_id}")

    # -----------------------------
    #   Question CRUD (admin)
    # -----------------------------

    @staticmethod
    async def list_questions() -> List[Question]:
        return await Question.all().prefetch_related("variants")

    @staticmethod
    async def get_question(question_id: int) -> Question:
        question = await Question.get_or_none(id=question_id).prefetch_related("variants")
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        return question

    @staticmethod
    async def create_question(data: Dict[str, Any]) -> Question:
        # ensure the parent passage exists
        passage = await Passage.get_or_none(id=data["passage_id"])
        if not passage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passage not found")
        new_question = await Question.create(**data)
        logger.info(f"Created Question id={new_question.id}")
        return new_question

    @staticmethod
    async def update_question(question_id: int, data: Dict[str, Any]) -> Question:
        question = await Question.get_or_none(id=question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        for field, value in data.items():
            setattr(question, field, value)
        await question.save()
        logger.info(f"Updated Question id={question_id}")
        return question

    @staticmethod
    async def delete_question(question_id: int) -> None:
        deleted = await Question.filter(id=question_id).delete()
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        logger.info(f"Deleted Question id={question_id}")

    # -----------------------------
    #   Variant CRUD (admin)
    # -----------------------------

    @staticmethod
    async def list_variants() -> List[Variant]:
        return await Variant.all()

    @staticmethod
    async def get_variant(variant_id: int) -> Variant:
        variant = await Variant.get_or_none(id=variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
        return variant

    @staticmethod
    async def create_variant(data: Dict[str, Any]) -> Variant:
        question = await Question.get_or_none(id=data["question_id"])
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        new_variant = await Variant.create(**data)
        logger.info(f"Created Variant id={new_variant.id}")
        return new_variant

    @staticmethod
    async def update_variant(variant_id: int, data: Dict[str, Any]) -> Variant:
        variant = await Variant.get_or_none(id=variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
        for field, value in data.items():
            setattr(variant, field, value)
        await variant.save()
        logger.info(f"Updated Variant id={variant_id}")
        return variant

    @staticmethod
    async def delete_variant(variant_id: int) -> None:
        deleted = await Variant.filter(id=variant_id).delete()
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
        logger.info(f"Deleted Variant id={variant_id}")

    # -----------------------------
    #   Reading session / user flow
    # -----------------------------

    @staticmethod
    async def start_reading(user_id: int) -> Tuple[Reading, Optional[str]]:
        # create a new Reading record, attach all passages by some logic
        # e.g., pick passages in order:
        passages = await Passage.all()
        if not passages:
            return None, "no_passages"
        new_reading = await Reading.create(
            user_id=user_id,
            status="pending",
            start_time=datetime.utcnow(),
            score=0.0,
            duration=60,
        )
        # associate all passages (m2m) in sorted order
        await new_reading.passages.add(*[p.id for p in passages])
        return new_reading, None

    @staticmethod
    async def get_reading(reading_id: int) -> Optional[Reading]:
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages", "user")
        return reading

    @staticmethod
    async def submit_answers(
        reading_id: int, user_id: int, answers: List[Dict[str, Any]]
    ) -> Tuple[float, Optional[str]]:
        # ensure reading exists and belongs to user
        reading = await Reading.get_or_none(id=reading_id, user_id=user_id)
        if not reading:
            return 0.0, "not_found"

        # if completed, return error
        if reading.status == "completed":
            return 0.0, "already_completed"

        total_score = 0.0
        async with in_transaction():
            for ans in answers:
                question_id = ans["question_id"]
                raw_answer = ans["answer"]
                question = await Question.get_or_none(id=question_id)
                if not question:
                    return 0.0, f"question_{question_id}"
                # check correctness
                is_correct = False
                correct_text = question.correct_answer or ""
                if raw_answer == correct_text:
                    is_correct = True
                    total_score += question.score

                # save Answer record
                await ReadingAnswer.create(
                    user_id=user_id,
                    question_id=question_id,
                    reading_id=reading_id,
                    text=raw_answer,
                    explanation=None,
                    is_correct=is_correct,
                    correct_answer=correct_text,
                    status="answered"
                )
            # mark reading as completed
            reading.status = "completed"
            reading.end_time = datetime.utcnow()
            reading.score = total_score
            await reading.save()

        return total_score, None

    @staticmethod
    async def cancel_reading(reading_id: int, user_id: int) -> bool:
        deleted = await Reading.filter(id=reading_id, user_id=user_id).delete()
        return bool(deleted)

    @staticmethod
    async def restart_reading(reading_id: int, user_id: int) -> Tuple[Optional[Reading], Optional[str]]:
        reading = await Reading.get_or_none(id=reading_id, user_id=user_id)
        if not reading:
            return None, "not_found"
        if reading.status != "completed":
            return None, "not_completed"
        # delete old user answers
        await ReadingAnswer.filter(reading_id=reading_id, user_id=user_id).delete()
        reading.status = "pending"
        reading.start_time = datetime.utcnow()
        reading.end_time = None
        reading.score = 0.0
        await reading.save()
        return reading, None

    @staticmethod
    async def list_readings_for_user(user_id: int) -> List[Reading]:
        return await Reading.filter(user_id=user_id).all()

    @staticmethod
    async def list_passages_in_reading(reading_id: int) -> List[Passage]:
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
        if not reading:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found")
        return await reading.passages.all()

    @staticmethod
    async def analyse_reading(reading_id: int, user_id: int) -> Dict[str, Any]:
        reading = await Reading.get_or_none(id=reading_id, user_id=user_id).prefetch_related("passages")
        if not reading:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found")
        # assemble analysis result per passage
        result = []
        for passage in await reading.passages.all():
            # load all questions for this passage
            questions_qs = await passage.questions.all()
            questions_data = []
            for question in questions_qs:
                # get the user answer
                ua = await ReadingAnswer.get_or_none(
                    question_id=question.id, user_id=user_id, reading_id=reading_id
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
        # also include pagination or score/time info if needed
        return {"results": result}


