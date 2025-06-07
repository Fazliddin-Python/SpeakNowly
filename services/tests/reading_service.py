# services/tests/reading_service.py

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from models.tests.reading import Passage, Question, Variant, Reading, Answer
from services.chatgpt.integration import ChatGPTIntegration
from services.analyses.reading_analyse_service import ReadingAnalyseService
from models.tests.constants import Constants

logger = logging.getLogger(__name__)


class ReadingService:
    # --- admin CRUD omitted for brevity (same as in router calls) ---

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
    async def start_reading(user_id: int) -> Tuple[Reading, Optional[str]]:
        chatgpt = ChatGPTIntegration(None)
        data = await chatgpt.generate_reading_data()
        passage_text = data.get("passage_text")
        questions_data = data.get("questions", [])
        if not passage_text or len(questions_data) != 3:
            return None, "invalid_gpt_output"

        async with in_transaction():
            passage = await Passage.create(text=passage_text)
            for qd in questions_data:
                q = await Question.create(
                    passage_id=passage.id,
                    text=qd["text"].strip(),
                    type=Constants.QuestionType.MULTIPLE_CHOICE,
                    score=1
                )
                for opt in qd["options"]:
                    label, _, content = opt.partition(")")
                    await Variant.create(
                        question_id=q.id,
                        label=label.strip(),
                        text=content.strip(),
                        is_correct=(label.strip() == qd["correct_option"].strip().upper())
                    )
            session = await Reading.create(
                user_id=user_id,
                passage_id=passage.id,
                status=Constants.ReadingStatus.STARTED,
                start_time=datetime.now(timezone.utc),
                score=0.0,
                duration=60
            )
        return session, None

    @staticmethod
    async def get_reading(session_id: int) -> Optional[Reading]:
        return (
            await Reading.get_or_none(id=session_id)
            .prefetch_related("passage__questions__variants")
        )

    @staticmethod
    async def submit_answers(
        session_id: int, user_id: int, answers: List[Dict[str, Any]]
    ) -> Tuple[float, Optional[str]]:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return 0, "session_not_found"
        if session.status == Constants.ReadingStatus.COMPLETED:
            return 0, "already_completed"

        total = 0.0
        async with in_transaction():
            for ans in answers:
                q = await Question.get_or_none(id=ans["question_id"]).prefetch_related("variants")
                if not q:
                    return 0, f"question_{ans['question_id']}"
                correct = next(v for v in await q.variants if v.is_correct)
                is_correct = (ans["answer"].strip().upper() == correct.label)
                if is_correct:
                    total += q.score
                await Answer.create(
                    user_id=user_id,
                    question_id=q.id,
                    reading_id=session_id,
                    selected_option=ans["answer"].strip().upper(),
                    is_correct=is_correct,
                    correct_answer=correct.label,
                    status="answered"
                )
            session.status = Constants.ReadingStatus.COMPLETED
            session.end_time = datetime.now(timezone.utc)
            session.score = total
            await session.save()
        # не блокировать пользователя на анализ
        _ = ReadingAnalyseService.analyse_reading(session_id, user_id)
        return total, None

    @staticmethod
    async def cancel_reading(session_id: int, user_id: int) -> bool:
        s = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not s:
            return False
        s.status = Constants.ReadingStatus.CANCELLED
        s.end_time = datetime.now(timezone.utc)
        await s.save(update_fields=["status", "end_time"])
        return True

    @staticmethod
    async def restart_reading(session_id: int, user_id: int) -> Tuple[Reading, Optional[str]]:
        s = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not s:
            return None, "session_not_found"
        if s.status != Constants.ReadingStatus.COMPLETED:
            return None, "not_completed"
        await Answer.filter(reading_id=session_id, user_id=user_id).delete()
        return await ReadingService.start_reading(user_id)

    @staticmethod
    async def analyse_reading(session_id: int, user_id: int) -> Dict[str, Any]:
        session = (
            await Reading.get_or_none(id=session_id, user_id=user_id)
            .prefetch_related("passage__questions__variants", "answers")
        )
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        questions = await session.passage.questions.all().prefetch_related("variants")
        result = []
        for q in questions:
            ua = await Answer.get_or_none(question_id=q.id, user_id=user_id)
            correct = next(v for v in await q.variants if v.is_correct)
            result.append({
                "id": q.id,
                "text": q.text,
                "options": [{"label": v.label, "text": v.text} for v in await q.variants],
                "user_answer": ua.selected_option if ua else None,
                "is_correct": ua.is_correct if ua else False,
                "correct_answer": correct.label,
            })

        return {
            "passage_id": session.passage_id,
            "passage_text": session.passage.text,
            "questions": result,
            "total_score": session.score,
            "duration": (session.end_time - session.start_time).total_seconds() / 60 if session.end_time else None
        }
