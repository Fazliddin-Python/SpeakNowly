import logging
import json
from datetime import timedelta
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from models.tests.reading import Reading, Answer
from models.analyses import ReadingAnalyse
from models.tests.constants import Constants

logger = logging.getLogger(__name__)

class ReadingAnalyseService:
    @staticmethod
    async def analyse_reading(reading_id: int, user_id: int) -> list[ReadingAnalyse]:
        reading = await Reading.get_or_none(id=reading_id)
        if not reading or reading.status != Constants.ReadingStatus.COMPLETED:
            logger.warning("Reading %s not found or not completed", reading_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Reading session not found or not completed")

        passages = await reading.passages.all()
        if not passages:
            logger.warning("No passages found for reading %s", reading_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No passages found for this reading session")

        answers = await Answer.filter(
            reading_id=reading_id,
            user_id=user_id
        ).prefetch_related("question")
        answers_by_passage = {}
        for ans in answers:
            answers_by_passage.setdefault(ans.passage_id, []).append(ans)

        if reading.start_time and reading.end_time:
            timing = reading.end_time - reading.start_time
            if not isinstance(timing, timedelta):
                timing = timedelta(seconds=float(timing))
        else:
            timing = timedelta(0)

        result = []

        async with in_transaction():
            for passage in passages:
                passage_answers = answers_by_passage.get(passage.id, [])
                total = len(passage_answers)
                correct = sum(1 for a in passage_answers if a.is_correct)
                band = round((correct / total) * 9, 1) if total else 0.0

                feedback = f"You answered {correct}/{total} correctly. Estimated band: {band}."

                obj, created = await ReadingAnalyse.get_or_create(
                    passage_id=passage.id,
                    user_id=user_id,
                    defaults={
                        "correct_answers": correct,
                        "overall_score": band,
                        "timing": timing,
                        "feedback": feedback,
                    }
                )
                if not created:
                    obj.correct_answers = correct
                    obj.overall_score = band
                    obj.timing = timing
                    obj.feedback = feedback
                    await obj.save()

                result.append(obj)
                logger.info("Finished analysis for passage %s (created=%s)", passage.id, created)

        return result

    @staticmethod
    async def get_analysis(reading_id: int, user_id: int) -> dict:
        reading = await Reading.get_or_none(id=reading_id)
        if not reading:
            return {
                "reading_id": reading_id,
                "analyse": [],
                "responses": []
            }

        passages = await reading.passages.all()
        if not passages:
            return {
                "reading_id": reading_id,
                "analyse": [],
                "responses": []
            }

        analyses = await ReadingAnalyse.filter(
            passage_id__in=[p.id for p in passages],
            user_id=user_id
        )

        analysis_data = []
        for analyse in analyses:
            analysis_data.append({
                "passage_id": analyse.passage_id,
                "correct_answers": analyse.correct_answers,
                "overall_score": float(analyse.overall_score),
                "timing": str(analyse.timing) if analyse.timing else None,
                "feedback": analyse.feedback,
            })

        answers = await Answer.filter(
            reading_id=reading_id,
            user_id=user_id
        ).prefetch_related("question")

        responses = []
        for a in answers:
            responses.append({
                "id": a.id,
                "question_id": a.question_id,
                "passage_id": a.question.passage_id,
                "user_answer": a.variant_id if a.variant_id else a.text,
                "is_correct": a.is_correct,
                "correct_answer": a.correct_answer,
            })

        return {
            "reading_id": reading_id,
            "analyse": {str(a["passage_id"]): a for a in analysis_data},
            "responses": responses
        }

    @staticmethod
    async def exists(reading_id: int, user_id: int) -> bool:
        reading = await Reading.get_or_none(id=reading_id)
        if not reading:
            return False
        passages = await reading.passages.all()
        if not passages:
            return False
        return await ReadingAnalyse.filter(
            passage_id__in=[p.id for p in passages],
            user_id=user_id
        ).exists()
