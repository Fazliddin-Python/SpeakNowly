import logging
from datetime import timedelta
from fastapi import HTTPException, status
from models.analyses import ReadingAnalyse
from models.tests.reading import Reading, Answer
from models.tests.constants import Constants

logger = logging.getLogger(__name__)

class ReadingAnalyseService:
    @staticmethod
    async def analyse_reading(reading_id: int) -> ReadingAnalyse:
        """
        Analyzes a reading session: counts correct answers, calculates score, timing, and feedback.
        """
        reading = await Reading.get_or_none(id=reading_id)
        if not reading or reading.status != Constants.ReadingStatus.COMPLETED:
            logger.warning("Reading %s not found or not completed", reading_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reading not found or not completed"
            )
        answers = await Answer.filter(
            user_id=reading.user_id,
            reading_id=reading_id
        ).all()
        correct_count = sum(1 for a in answers if a.is_correct)
        total = len(answers)
        score = round((correct_count / total) * 9, 1) if total else 0.0
        timing_delta = (
            reading.end_time - reading.start_time
            if reading.end_time and reading.start_time
            else timedelta()
        )
        feedback = f"Correct: {correct_count}/{total}. Score: {score}."

        analyse_obj, created = await ReadingAnalyse.get_or_create(
            reading_id=reading_id,
            defaults={
                "user_id": reading.user_id,
                "correct_answers": correct_count,
                "overall_score": score,
                "timing": timing_delta,
                "feedback": feedback,
            }
        )
        if not created:
            analyse_obj.correct_answers = correct_count
            analyse_obj.overall_score = score
            analyse_obj.timing = timing_delta
            analyse_obj.feedback = feedback
            await analyse_obj.save()
        logger.info("Reading analysis for reading %s completed", reading_id)
        return analyse_obj

    @staticmethod
    async def get_analysis(reading_id: int) -> dict:
        """
        Retrieve the analysis result for a reading session, including detailed responses.
        """
        analyse = await ReadingAnalyse.get_or_none(reading_id=reading_id)
        if not analyse:
            return {
                "reading_id": reading_id,
                "analyse": {},
                "responses": []
            }

        # Собираем ответы пользователя с подробностями
        answer_objs = await Answer.filter(reading_id=reading_id).all()
        responses = [
            {
                "id": a.id,
                "question_id": a.question_id,
                "user_answer": a.selected_option,
                "is_correct": a.is_correct,
                "correct_answer": a.correct_answer,
            }
            for a in answer_objs
        ]

        analyse_data = {
            "correct_answers": analyse.correct_answers,
            "overall_score": float(analyse.overall_score),
            "timing": str(analyse.timing),
            "feedback": analyse.feedback,
        }
        return {
            "reading_id": reading_id,
            "analyse": analyse_data,
            "responses": responses
        }
