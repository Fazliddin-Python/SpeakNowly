import logging
from models.analyses import ReadingAnalyse
from models.tests.reading import Reading, Answer
from datetime import timedelta

logger = logging.getLogger(__name__)

class ReadingAnalyseService:
    @staticmethod
    async def analyse_reading(reading_id: int) -> ReadingAnalyse:
        """
        Analyzes a reading: counts correct answers, calculates score, time, and generates feedback.
        """
        reading = await Reading.get_or_none(id=reading_id)
        if not reading or reading.status != "completed":
            logger.warning("Reading %s not found or not completed", reading_id)
            raise ValueError("Reading not found or not completed")
        user = reading.user
        answers = await Answer.filter(
            user_id=user.id,
            reading_id=reading_id
        )
        correct = sum(1 for a in answers if a.is_correct)
        total = len(answers)
        score = round((correct / total) * 9, 1) if total else 0.0
        timing = reading.end_time - reading.start_time if reading.end_time and reading.start_time else timedelta()
        feedback = f"Correct: {correct}/{total}. Score: {score}."
        analyse, created = await ReadingAnalyse.get_or_create(
            reading=reading,
            defaults={
                "user": user,
                "correct_answers": correct,
                "overall_score": score,
                "timing": timing,
                "feedback": feedback,
            }
        )
        if not created:
            analyse.correct_answers = correct
            analyse.overall_score = score
            analyse.timing = timing
            analyse.feedback = feedback
            await analyse.save()
        logger.info("Reading analysis for reading %s completed", reading_id)
        return analyse

    @staticmethod
    async def get_analysis(reading_id: int) -> dict:
        analyse = await ReadingAnalyse.get_or_none(reading_id=reading_id)
        if not analyse:
            return {
                "reading_id": reading_id,
                "analyse": {},
                "responses": []
            }
        analyse_data = {
            "correct_answers": analyse.correct_answers,
            "overall_score": float(analyse.overall_score),
            "timing": str(analyse.timing),
            "feedback": analyse.feedback,
        }
        return {
            "reading_id": reading_id,
            "analyse": analyse_data,
            "responses": []
        }