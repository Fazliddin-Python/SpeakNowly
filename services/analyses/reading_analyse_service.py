from fastapi import HTTPException, status
from datetime import timedelta
import asyncio
from models.tests.constants import Constants
from services.chatgpt import ChatGPTReadingIntegration
from models.analyses import ReadingAnalyse
from models.tests import Reading, ReadingAnswer

class ReadingAnalyseService:
    @staticmethod
    async def analyse(reading_id: int, user_id: int) -> list[ReadingAnalyse]:
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
        if not reading:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Reading session not found")
        if reading.status != Constants.ReadingStatus.COMPLETED.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Reading session not completed")

        all_answers = await ReadingAnswer.filter(
            reading_id=reading_id, user_id=user_id
        ).select_related("question")
        answers_by_passage = {}
        for a in all_answers:
            if a.status == ReadingAnswer.ANSWERED:
                answers_by_passage.setdefault(a.question.passage_id, []).append(a)

        chatgpt = ChatGPTReadingIntegration()

        async def analyse_passage(passage_id: int, passage_text: str):
            if await ReadingAnalyse.get_or_none(passage_id=passage_id, user_id=user_id):
                return None

            submitted = answers_by_passage.get(passage_id, [])
            if not submitted:
                return None

            non_empty = [a for a in submitted if (a.text or "").strip()]
            empty_qs  = [a for a in submitted if not (a.text or "").strip()]

            if not non_empty:
                obj = await ReadingAnalyse.create(
                    passage_id=passage_id, user_id=user_id,
                    correct_answers=0, overall_score=0.0,
                    duration=timedelta(0)
                )
                for a in submitted:
                    await ReadingAnswer.filter(
                        reading_id=reading_id, user_id=user_id,
                        question_id=a.question.id
                    ).update(is_correct=False, correct_answer="", explanation="")
                return obj

            times = [a.updated_at for a in non_empty if a.updated_at]
            duration = (max(times) - min(times)) if times else timedelta(0)

            questions_payload = [
                {
                    "question_id": a.question.id,
                    "question": a.question.text,
                    "type": a.question.type,
                    "user_answer": a.text or ""
                } for a in non_empty
            ]

            result = await chatgpt.check_passage_answers(
                text=passage_text,
                questions=questions_payload,
                passage_id=passage_id
            )
            analysis_items = result["analysis"]
            stats = result["stats"]

            raw = stats.get("overall_score", 0.0)
            frac = raw - int(raw)
            if frac < 0.25:
                band = float(int(raw))
            elif frac < 0.75:
                band = float(int(raw)) + 0.5
            else:
                band = float(int(raw)) + 1.0

            obj = await ReadingAnalyse.create(
                passage_id=passage_id, user_id=user_id,
                correct_answers=stats.get("total_correct", 0),
                overall_score=band, duration=duration
            )

            for a in empty_qs:
                await ReadingAnswer.filter(
                    reading_id=reading_id, user_id=user_id,
                    question_id=a.question.id
                ).update(is_correct=False, correct_answer="", explanation="")

            for qi in analysis_items:
                qid = qi["question_id"]
                await ReadingAnswer.filter(
                    reading_id=reading_id, user_id=user_id,
                    question_id=qid
                ).update(
                    is_correct=bool(qi.get("is_correct", False)),
                    correct_answer=qi.get("correct_answer", ""),
                    explanation=qi.get("explanation", "")
                )

            return obj

        passages = await reading.passages.all()
        text_map = {p.id: p.text for p in passages}
        tasks = [analyse_passage(pid, text_map[pid]) for pid in answers_by_passage]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    @staticmethod
    async def get_passage_analysis(passage_id: int, user_id: int):
        return await ReadingAnalyse.get_or_none(passage_id=passage_id, user_id=user_id)

    @staticmethod
    async def get_all_analyses(reading_id: int, user_id: int):
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
        if not reading:
            return []
        pids = [p.id for p in await reading.passages.all()]
        return await ReadingAnalyse.filter(passage_id__in=pids, user_id=user_id)
