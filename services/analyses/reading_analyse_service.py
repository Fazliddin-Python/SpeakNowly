from fastapi import HTTPException, status
from datetime import timedelta
from services.chatgpt import ChatGPTReadingIntegration
from models.analyses import ReadingAnalyse
from models.tests import Constants, Reading, ReadingAnswer
import asyncio

class ReadingAnalyseService:
    @staticmethod
    async def analyse(reading_id: int, user_id: int) -> list[ReadingAnalyse]:
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
        if not reading:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Reading session not found")
        
        if reading.status != Constants.ReadingStatus.COMPLETED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reading session is not completed")

        passages = await reading.passages.all()
        answers = await ReadingAnswer.filter(reading_id=reading_id, user_id=user_id).prefetch_related("question")
        answers_by_passage = {}
        for ans in answers:
            answers_by_passage.setdefault(ans.question.passage_id, []).append(ans)

        chatgpt = ChatGPTReadingIntegration()

        async def analyse_passage(passage):
            obj = await ReadingAnalyse.get_or_none(
                passage_id=passage.id,
                user_id=user_id
            )
            if obj:
                return obj

            passage_answers = answers_by_passage.get(passage.id, [])
            if not passage_answers:
                return None

            updated_ats = [a.updated_at for a in passage_answers if a.updated_at]
            if updated_ats:
                duration = max(updated_ats) - min(updated_ats)
            else:
                duration = timedelta(0)

            questions_data = []
            for ans in passage_answers:
                qtype = getattr(ans.question, "type", None)
                user_answer = ans.text or ""
                questions_data.append({
                    "question": ans.question.text,
                    "type": qtype,
                    "user_answer": user_answer,
                })
            try:
                analysis = await chatgpt.check_passage_answers(
                    text=passage.text,
                    questions=questions_data,
                    passage_id=passage.id
                )
            except Exception as e:
                raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"ChatGPT analysis failed: {e}")
            stats = None
            for item in analysis:
                if "stats" in item:
                    stats = item["stats"]
            if not stats:
                raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No stats in ChatGPT response")

            raw_score = stats.get("overall_score", 0.0)
            frac = raw_score - int(raw_score)
            if frac < 0.25:
                ielts_score = float(int(raw_score))
            elif frac < 0.75:
                ielts_score = float(int(raw_score)) + 0.5
            else:
                ielts_score = float(int(raw_score) + 1)

            obj = await ReadingAnalyse.create(
                passage_id=passage.id,
                user_id=user_id,
                correct_answers=stats.get("total_correct", 0),
                overall_score=ielts_score,
                duration=duration,
            )

            for question_result in analysis:
                qid = question_result.get("question_id")
                is_correct = question_result.get("is_correct")
                if is_correct is None:
                    is_correct = False
                correct_answer = question_result.get("correct_answer")
                await ReadingAnswer.filter(
                    user_id=user_id,
                    reading_id=reading_id,
                    question_id=qid
                ).update(
                    is_correct=is_correct,
                    correct_answer=correct_answer
                )

            return obj

        analyses = await asyncio.gather(*(analyse_passage(p) for p in passages))
        result = [a for a in analyses if a is not None]
        return result

    @staticmethod
    async def get_passage_analysis(passage_id: int, user_id: int):
        return await ReadingAnalyse.get_or_none(passage_id=passage_id, user_id=user_id)

    @staticmethod
    async def get_all_analyses(reading_id: int, user_id: int):
        reading = await Reading.get(id=reading_id).prefetch_related("passages")
        passage_ids = [p.id for p in await reading.passages.all()]
        return await ReadingAnalyse.filter(passage_id__in=passage_ids, user_id=user_id)