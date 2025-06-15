from datetime import timedelta
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from models.analyses import ReadingAnalyse
from models.tests import Constants, Reading, ReadingAnswer, ReadingPassage, ListeningQuestionType
from services.chatgpt.reading_integration import ChatGPTReadingIntegration

class ReadingAnalyseService:
    @staticmethod
    async def analyse(reading_id: int, user_id: int) -> list[ReadingAnalyse]:
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
        if not reading:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Reading session not found")
        
        if reading.status != Constants.ReadingStatus.COMPLETED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reading session is not completed")
        
        passages = reading.passages
        
        answers = await ReadingAnswer.filter(reading_id=reading_id, user_id=user_id).prefetch_related("question")
        answers_by_passage = {}
        for ans in answers:
            answers_by_passage.setdefault(ans.question.passage_id, []).append(ans)
        
        duration = (reading.end_time - reading.start_time) if (reading.start_time and reading.end_time) else timedelta(0)
        
        result = []
        chatgpt = ChatGPTReadingIntegration()
        async with in_transaction():
            for passage in passages:
                passage_answers = answers_by_passage.get(passage.id, [])
                if not passage_answers:
                    continue
                questions_data = []
                for ans in passage_answers:
                    qtype = getattr(ans.question, "type", None)
                    if qtype == ListeningQuestionType.MULTIPLE_CHOICE:
                        user_answer = ans.variant.text if getattr(ans, "variant", None) else (ans.text_answer or "")
                    else:
                        user_answer = ans.text_answer or ""
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
                obj, created = await ReadingAnalyse.get_or_create(
                    passage_id=passage.id,
                    user_id=user_id,
                    defaults={
                        "correct_answers": stats.get("total_correct", 0),
                        "overall_score": stats.get("overall_score", 0.0),
                        "duration": duration,
                    }
                )
                if not created:
                    obj.correct_answers = stats.get("total_correct", 0)
                    obj.overall_score = stats.get("overall_score", 0.0)
                    obj.duration = duration
                    await obj.save()
                result.append(obj)
        return result