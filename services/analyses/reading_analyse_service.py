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
    async def analyse_reading(reading_id: int, user_id: int) -> ReadingAnalyse:
        reading = await Reading.get_or_none(id=reading_id)
        if not reading or reading.status != Constants.ReadingStatus.COMPLETED:
            logger.warning("Reading %s not found or not completed", reading_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Reading session not found or not completed")

        # Получаем passage (предполагается, что passages всегда есть)
        passages = await reading.passages.all()
        if not passages:
            logger.warning("No passages found for reading %s", reading_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No passage found for this reading session")
        passage = passages[0]

        answers = await Answer.filter(reading_id=reading_id).all()
        total = len(answers)
        correct = sum(1 for a in answers if a.is_correct)
        band = round((correct / total) * 9, 1) if total else 0.0

        if reading.start_time and reading.end_time:
            timing = reading.end_time - reading.start_time
            timing = timedelta(seconds=timing.total_seconds())
        else:
            timing = timedelta(seconds=0)

        feedback = f"You answered {correct}/{total} correctly. Estimated band: {band}."

        async with in_transaction():
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

        logger.info("Finished analysis for passage %s (created=%s)", passage.id, created)
        return obj

    @staticmethod
    async def get_analysis(reading_id: int, user_id: int) -> dict:
        reading = await Reading.get_or_none(id=reading_id)
        if not reading:
            return {"reading_id": reading_id, "analyse": {}, "responses": []}
        passages = await reading.passages.all()
        if not passages:
            return {"reading_id": reading_id, "analyse": {}, "responses": []}
        passage = passages[0]

        analyse = await ReadingAnalyse.get_or_none(passage_id=passage.id, user_id=user_id)
        if not analyse:
            return {"reading_id": reading_id, "analyse": {}, "responses": []}

        answers = await Answer.filter(reading_id=reading_id).all()
        resp = []
        for a in answers:
            resp.append({
                "id": a.id,
                "question_id": a.question_id,
                "user_answer": a.variant_id or a.text,
                "is_correct": a.is_correct,
                "correct_answer": a.correct_answer,
            })

        return {
            "reading_id": reading_id,
            "analyse": {
                "correct_answers": analyse.correct_answers,
                "overall_score": float(analyse.overall_score),
                "timing": str(analyse.timing),
                "feedback": analyse.feedback,
            },
            "responses": resp
        }
