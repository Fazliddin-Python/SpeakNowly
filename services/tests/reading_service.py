import json
import logging
import random
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from tortoise.transactions import in_transaction

from models.tests.reading import Passage, Question, Variant, Reading, Answer
from models.tests.constants import Constants
from models.tests.test_type import TestTypeEnum
from services.chatgpt.integration import ChatGPTIntegration
from services.analyses.reading_analyse_service import ReadingAnalyseService
from utils.get_actual_price import get_user_actual_test_price
from models.transactions import TokenTransaction, TransactionType
from models.users import User
from models.analyses import ReadingAnalyse

logger = logging.getLogger(__name__)


class ReadingService:
    # --- admin CRUD omitted for brevity ---

    @staticmethod
    async def list_passages(t: dict) -> List[Passage]:
        return await Passage.all()

    @staticmethod
    async def get_passage(passage_id: int, t: dict) -> Passage:
        p = await Passage.get_or_none(id=passage_id)
        if not p:
            raise HTTPException(status_code=404, detail=t["passage_not_found"])
        return p

    @staticmethod
    async def create_passage(data: Dict[str, Any], t: dict) -> Passage:
        if await Passage.filter(number=data["number"]).exists():
            raise HTTPException(status_code=400, detail=t["passage_number_exists"])
        return await Passage.create(**data)

    @staticmethod
    async def update_passage(passage_id: int, data: Dict[str, Any], t: dict) -> Passage:
        p = await Passage.get_or_none(id=passage_id)
        if not p:
            raise HTTPException(status_code=404, detail=t["passage_not_found"])
        if "number" in data:
            if await Passage.filter(number=data["number"]).exclude(id=passage_id).exists():
                raise HTTPException(status_code=400, detail=t["passage_number_exists"])
        for k,v in data.items():
            setattr(p, k, v)
        await p.save()
        return p

    @staticmethod
    async def delete_passage(passage_id: int, t: dict) -> None:
        if not await Passage.filter(id=passage_id).delete():
            raise HTTPException(status_code=404, detail=t["passage_not_found"])

    @staticmethod
    async def list_questions(t: dict) -> List[Question]:
        return await Question.all().prefetch_related("variants")

    @staticmethod
    async def get_question(question_id: int, t: dict) -> Question:
        q = await Question.get_or_none(id=question_id).prefetch_related("variants")
        if not q:
            raise HTTPException(status_code=404, detail=t["question_not_found"])
        return q

    @staticmethod
    async def create_question(data: Dict[str, Any], t: dict) -> Question:
        if not await Passage.filter(id=data["passage_id"]).exists():
            raise HTTPException(status_code=404, detail=t["passage_not_found"])
        return await Question.create(**data)

    @staticmethod
    async def update_question(question_id: int, data: Dict[str, Any], t: dict) -> Question:
        q = await Question.get_or_none(id=question_id)
        if not q:
            raise HTTPException(status_code=404, detail=t["question_not_found"])
        for k,v in data.items():
            setattr(q, k, v)
        await q.save()
        return q

    @staticmethod
    async def delete_question(question_id: int, t: dict) -> None:
        if not await Question.filter(id=question_id).delete():
            raise HTTPException(status_code=404, detail=t["question_not_found"])

    @staticmethod
    async def list_variants(t: dict) -> List[Variant]:
        return await Variant.all()

    @staticmethod
    async def get_variant(variant_id: int, t: dict) -> Variant:
        v = await Variant.get_or_none(id=variant_id)
        if not v:
            raise HTTPException(status_code=404, detail=t["variant_not_found"])
        return v

    @staticmethod
    async def create_variant(data: Dict[str, Any], t: dict) -> Variant:
        if not await Question.filter(id=data["question_id"]).exists():
            raise HTTPException(status_code=404, detail=t["question_not_found"])
        return await Variant.create(**data)

    @staticmethod
    async def update_variant(variant_id: int, data: Dict[str, Any], t: dict) -> Variant:
        v = await Variant.get_or_none(id=variant_id)
        if not v:
            raise HTTPException(status_code=404, detail=t["variant_not_found"])
        for k,vv in data.items():
            setattr(v, k, vv)
        await v.save()
        return v

    @staticmethod
    async def delete_variant(variant_id: int, t: dict) -> None:
        if not await Variant.filter(id=variant_id).delete():
            raise HTTPException(status_code=404, detail=t["variant_not_found"])

    @staticmethod
    async def start_reading(user_id: int) -> Tuple[Reading, List[Passage]]:
        # Load user
        user = await User.get_or_none(id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Token check
        price = await get_user_actual_test_price(user, TestTypeEnum.READING_ENG)
        if user.tokens < price:
            raise HTTPException(status_code=402, detail="Insufficient tokens")

        # --- GPT generation commented out ---
        # numbers = await Passage.filter(number__not_isnull=True).order_by('-number').values_list('number', flat=True)
        # start_number = numbers[0] + 1 if numbers else 1
        # chatgpt = ChatGPTIntegration()
        # try:
        #     test_data = await chatgpt.generate_reading_data(start_number)
        # except Exception as e:
        #     raise HTTPException(status_code=500, detail=f"Failed to generate reading passages: {str(e)}")
        # if not isinstance(test_data, list) or len(test_data) != 3:
        #     raise HTTPException(status_code=500, detail="GPT did not return 3 passages as expected.")
        # created_passages = []
        # async with in_transaction():
        #     ... # (create passage, questions, variants, as before)
        # return session, created_passages

        # --- Use only existing passages from the database ---
        # Filter only valid passages (all fields present and at least 1 question)
        passages = await Passage.filter(
            number__not_isnull=True,
            skills__not_isnull=True,
            title__not_isnull=True,
            text__not_isnull=True,
            level__not_isnull=True,
        ).all()
        # Keep only those with at least 1 question
        valid_passages = []
        for p in passages:
            if await p.questions.all().count() > 0:
                valid_passages.append(p)
        if len(valid_passages) < 3:
            raise HTTPException(status_code=400, detail="Not enough valid passages with all fields and questions")
        selected_passages = random.sample(valid_passages, 3)

        # Save session and relations
        async with in_transaction():
            user.tokens -= price
            await user.save()
            await TokenTransaction.create(
                user_id=user.id,
                transaction_type=TransactionType.TEST_READING,
                amount=price,
                balance_after_transaction=user.tokens,
                description=f"Reading Test | Deducted: {price} tokens.",
            )

            now = datetime.now(timezone.utc)
            session = await Reading.create(
                user_id=user.id,
                status=Constants.ReadingStatus.STARTED,
                start_time=now,
                end_time=now + timedelta(minutes=60),
                score=0.0,
                duration=60,
            )

            for passage in selected_passages:
                await session.passages.add(passage)
                qs = await passage.questions.all()
                answers = [
                    Answer(
                        user_id=user.id,
                        reading_id=session.id,
                        question_id=q.id,
                        status=Answer.NOT_ANSWERED,
                    )
                    for q in qs
                ]
                await Answer.bulk_create(answers)

        return session, selected_passages

    @staticmethod
    async def _select_random_passages(user_id: int) -> List[Passage]:
        # Retrieve last reading
        last = await Reading.filter(
            user_id=user_id,
            status__in=[
                Constants.ReadingStatus.STARTED,
                Constants.ReadingStatus.COMPLETED,
                Constants.ReadingStatus.PENDING,
                Constants.ReadingStatus.EXPIRED,
            ],
        ).order_by("-start_time").first()

        all_passages = await Passage.all()
        if not last:
            return random.sample(all_passages, min(3, len(all_passages)))

        used_ids = {p.id for p in await last.passages.all()}
        unused = [p for p in all_passages if p.id not in used_ids]
        if len(unused) >= 3:
            return random.sample(unused, 3)

        needed = 3 - len(unused)
        additional = random.sample([p for p in all_passages if p.id in used_ids], needed)
        return unused + additional

    @staticmethod
    async def submit_answers(
        session_id: int,
        user_id: int,
        passage_id: int,
        answers: List[Any]
    ) -> Tuple[float, Optional[str]]:
        # 1. Check if session exists
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return 0.0, "session_not_found"

        # 2. Check that passage_id actually belongs to this session
        if not await session.passages.filter(id=passage_id).exists():
            return 0.0, "invalid_passage"

        # 3. Check for duplicate questions
        question_ids = [getattr(ans, "question_id", None) for ans in answers]
        if len(question_ids) != len(set(question_ids)):
            return 0.0, "duplicate_answers"

        # 4. List of valid questions only from this passage
        valid_qs = {q.id for q in await Question.filter(passage_id=passage_id).all()}
        if not set(question_ids).issubset(valid_qs):
            return 0.0, "invalid_question"

        total_score = 0.0
        # 5. Save answers in transaction
        async with in_transaction():
            for ans in answers:
                qid = getattr(ans, "question_id", None)
                answer_text = getattr(ans, "answer", "").strip()
                question = await Question.get_or_none(id=qid).prefetch_related("variants")
                if not question:
                    return 0.0, f"question_{qid}"

                variants = await question.variants.all()
                correct_variant = next((v for v in variants if v.is_correct), None)
                selected = next(
                    (v for v in variants if v.text.strip().upper() == answer_text.upper()),
                    None
                )
                is_correct = selected.is_correct if selected else False
                if is_correct:
                    total_score += question.score

                existing = await Answer.filter(
                    user_id=user_id,
                    reading_id=session_id,
                    question_id=qid
                ).first()

                if existing:
                    existing.variant_id = selected.id if selected else None
                    existing.text = answer_text
                    existing.is_correct = is_correct
                    existing.correct_answer = correct_variant.text if correct_variant else ""
                    existing.status = Answer.ANSWERED
                    await existing.save()
                else:
                    await Answer.create(
                        user_id=user_id,
                        reading_id=session_id,
                        question_id=qid,
                        variant_id=selected.id if selected else None,
                        text=answer_text,
                        is_correct=is_correct,
                        correct_answer=correct_variant.text if correct_variant else "",
                        status=Answer.ANSWERED,
                    )

        return total_score, None

    @staticmethod
    async def finish_reading(
        session_id: int,
        user_id: int
    ) -> Tuple[Dict[str, Any], int]:
        # 1. Загрузить сессию
        reading = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not reading:
            return {"error": "Reading session not found"}, 404

        # 2. Закрыть сессию, если ещё не закрыта
        if reading.status != Constants.ReadingStatus.COMPLETED:
            reading.status = Constants.ReadingStatus.COMPLETED
            reading.end_time = datetime.now(timezone.utc)
            await reading.save(update_fields=["status", "end_time"])

        # 3. Подсчитать результаты
        answers = await Answer.filter(reading_id=session_id, user_id=user_id)
        total_questions = len(answers)
        correct = sum(1 for a in answers if a.is_correct)

        # 4. Перевести в IELTS band 0–9
        overall_band = round((correct / total_questions) * 9, 1) if total_questions else 0.0

        # 5. Время выполнения (в минутах)
        elapsed = None
        if reading.start_time and reading.end_time:
            elapsed = (reading.end_time - reading.start_time).total_seconds() / 60

        return {
            "score": overall_band,
            "correct": f"{correct}/{total_questions}",
            "time": round(elapsed, 2) if elapsed is not None else None
        }, 200
    
    @staticmethod
    async def cancel_reading(session_id: int, user_id: int) -> bool:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return False
        session.status = Constants.ReadingStatus.CANCELLED
        await session.save(update_fields=["status"])
        return True

    @staticmethod
    async def restart_reading(
        session_id: int,
        user_id: int
    ) -> Tuple[Optional[Reading], Optional[str]]:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return None, "session_not_found"
        # Only allow restart if not completed
        if session.status == Constants.ReadingStatus.COMPLETED:
            return None, "session_already_completed"

        # Extend session and reset state
        session.status = Constants.ReadingStatus.PENDING
        session.end_time = session.end_time + timedelta(minutes=20)
        await session.save()
        # Clear previous answers
        await Answer.filter(reading=session_id, user_id=user_id).delete()
        return session, None

