from models.tests.reading import Reading, Passage, Question, Variant, Answer
from tortoise.exceptions import DoesNotExist
from datetime import datetime, timezone
from typing import List, Optional

class ReadingService:
    @staticmethod
    async def get_readings_for_user(user_id: int):
        return await Reading.filter(user_id=user_id).all()

    @staticmethod
    async def get_reading(reading_id: int):
        return await Reading.get_or_none(id=reading_id).prefetch_related("passages")

    @staticmethod
    async def start_reading(user_id: int, passages_count: int = 3):
        passages = await Passage.all()
        if not passages:
            return None, "no_passages"
        reading = await Reading.create(
            user_id=user_id,
            start_time=datetime.now(timezone.utc),
            status="started",
            duration=60,
        )
        await reading.passages.add(*passages[:passages_count])
        return reading, None

    @staticmethod
    async def submit_answers(reading_id: int, user_id: int, answers: List[dict]):
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages__questions")
        if not reading:
            return None, "not_found"
        if reading.status == "completed":
            return None, "already_completed"
        total_score = 0
        for answer_data in answers:
            question = await Question.get_or_none(id=answer_data["question_id"])
            if not question:
                return None, f"question_{answer_data['question_id']}_not_found"
            is_correct = question.correct_answer == answer_data["text"]
            score = question.score if is_correct else 0
            total_score += score
            await Answer.create(
                user_id=user_id,
                question_id=answer_data["question_id"],
                text=answer_data["text"],
                is_correct=is_correct,
                correct_answer=question.correct_answer,
                explanation=answer_data.get("explanation"),
            )
        reading.status = "completed"
        reading.end_time = datetime.now(timezone.utc)
        reading.score = total_score
        await reading.save()
        return total_score, None