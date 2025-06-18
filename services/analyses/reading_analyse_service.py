from fastapi import HTTPException, status
from datetime import timedelta
import asyncio
from services.chatgpt import ChatGPTReadingIntegration
from models.analyses import ReadingAnalyse
from models.tests import Reading, ReadingAnswer

class ReadingAnalyseService:
    @staticmethod
    async def analyse(reading_id: int, user_id: int) -> list[ReadingAnalyse]:
        # Fetch reading session and validate
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
        if not reading:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading session not found")

        # Collect answers grouped by passage
        answers = await ReadingAnswer.filter(reading_id=reading_id, user_id=user_id).select_related("question")
        answers_by_passage = {}
        for ans in answers:
            if ans.status == ReadingAnswer.ANSWERED:
                answers_by_passage.setdefault(ans.question.passage_id, []).append(ans)

        chatgpt = ChatGPTReadingIntegration()

        async def analyse_passage(passage_id, passage_text):
            # Skip if analysis already exists
            existing = await ReadingAnalyse.get_or_none(passage_id=passage_id, user_id=user_id)
            if existing:
                return existing

            passage_answers = answers_by_passage.get(passage_id, [])
            # If no submitted answers for this passage, skip
            if not passage_answers:
                return None

            # Compute duration between first and last answer
            times = [a.updated_at for a in passage_answers if a.updated_at]
            duration = (max(times) - min(times)) if times else timedelta(0)

            # Prepare payload for ChatGPT
            questions_payload = [
                {
                    "question_id": ans.question.id,
                    "question": ans.question.text,
                    "type": ans.question.type,
                    "user_answer": ans.text or ""
                } for ans in passage_answers
            ]

            # Call ChatGPT for analysis
            try:
                analysis_list = await chatgpt.check_passage_answers(
                    text=passage_text,
                    questions=questions_payload,
                    passage_id=passage_id
                )
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ChatGPT analysis failed: {e}")

            # Extract stats
            stats_item = next((item.get("stats") for item in analysis_list if isinstance(item, dict) and "stats" in item), None)
            if not stats_item:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No stats in ChatGPT response")

            # Compute IELTS score rounding to nearest half-band
            raw_score = stats_item.get("overall_score", 0.0)
            frac = raw_score - int(raw_score)
            if frac < 0.25:
                band = float(int(raw_score))
            elif frac < 0.75:
                band = float(int(raw_score)) + 0.5
            else:
                band = float(int(raw_score)) + 1.0

            # Persist ReadingAnalyse record
            analyse_obj = await ReadingAnalyse.create(
                passage_id=passage_id,
                user_id=user_id,
                correct_answers=stats_item.get("total_correct", 0),
                overall_score=band,
                duration=duration
            )

            # Update ReadingAnswer records with correctness and correct answer text
            for item in analysis_list:
                # Each item should be a question analysis dict
                if not isinstance(item, dict) or "question_id" not in item:
                    continue
                qid = item.get("question_id")
                is_corr = bool(item.get("is_correct", False))
                corr_ans = item.get("correct_answer", "")
                await ReadingAnswer.filter(
                    reading_id=reading_id,
                    user_id=user_id,
                    question_id=qid
                ).update(
                    is_correct=is_corr,
                    correct_answer=corr_ans
                )

            return analyse_obj

        # Only analyse passages with submitted answers
        # Build map of passage_id to text
        passages = await reading.passages.all()
        passage_map = {p.id: p.text for p in passages}
        to_analyse = [(pid, passage_map.get(pid)) for pid in answers_by_passage.keys() if pid in passage_map]

        # Run analysis for submitted passages concurrently
        results = await asyncio.gather(*(analyse_passage(pid, text) for pid, text in to_analyse))
        # Filter out None
        return [res for res in results if res]

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
