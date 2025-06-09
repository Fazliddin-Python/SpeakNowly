import json
import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone

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
    async def start_reading(user_id: int) -> Tuple[Reading, Optional[List[Passage]]]:
        # 1. Determine next passage number (max + 1)
        numbers = await Passage.filter(number__not_isnull=True).order_by('-number').values_list('number', flat=True)
        max_number = numbers[0] if numbers else 0
        passage_number = max_number + 1

        # 2. Pick random difficulty level
        levels = [Constants.PassageLevel.EASY, Constants.PassageLevel.MEDIUM, Constants.PassageLevel.HARD]
        random_level = random.choice(levels).value

        # 3. Request new passage and questions from GPT
        chatgpt = ChatGPTIntegration()
        data = await chatgpt.generate_reading_data(passage_number=passage_number, random_level=random_level)

        passage_text = data.get("passage_text")
        questions_data = data.get("questions", [])

        if not passage_text or len(questions_data) != 3:
            return None, None  # or handle error accordingly

        async with in_transaction():
            # 4. Create Passage
            passage = await Passage.create(
                text=passage_text,
                title=data.get("passage_title", "Reading Passage"),
                number=data.get("passage_number", passage_number),
                skills=data.get("passage_skills", "reading"),
                level=data.get("passage_level", random_level),
            )

            # 5. Create Questions and Variants
            for qd in questions_data:
                question = await Question.create(
                    passage_id=passage.id,
                    text=qd["text"].strip(),
                    type=Constants.QuestionType.MULTIPLE_CHOICE,
                    score=1
                )
                for opt in qd["options"]:
                    label, _, content = opt.partition(")")
                    await Variant.create(
                        question_id=question.id,
                        text=content.strip(),
                        is_correct=(label.strip().upper() == qd["correct_option"].strip().upper())
                    )

            # 6. Create Reading session and link passage
            session = await Reading.create(
                user_id=user_id,
                status=Constants.ReadingStatus.STARTED,
                start_time=datetime.now(timezone.utc),
                score=0.0,
                duration=60
            )
            await session.passages.add(passage)

        return session, [passage]

    @staticmethod
    async def get_reading(session_id: int, user_id: int) -> Tuple[Optional[Reading], Optional[List[Passage]]]:
        reading = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not reading:
            return None, None
        passages = await reading.passages.all()
        return reading, passages

    @staticmethod
    async def submit_answers(session_id: int, user_id: int, answers: List[Any]) -> Tuple[float, Optional[str]]:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return 0, "session_not_found"
        if session.status in [Constants.ReadingStatus.COMPLETED, Constants.ReadingStatus.CANCELLED]:
            return 0, "session_already_closed"

        # Validate answers for duplicates and legitimacy
        question_ids = [ans.question_id if hasattr(ans, "question_id") else ans["question_id"] for ans in answers]
        if len(question_ids) != len(set(question_ids)):
            return 0, "duplicate_answers"

        session_passages = await session.passages.all()
        session_questions = []
        for passage in session_passages:
            session_questions.extend(await passage.questions.all())
        session_question_ids = {q.id for q in session_questions}
        if not set(question_ids).issubset(session_question_ids):
            return 0, "invalid_question"

        total_score = 0.0

        async with in_transaction():
            for ans in answers:
                question_id = ans.question_id if hasattr(ans, "question_id") else ans["question_id"]
                answer_text = ans.answer if hasattr(ans, "answer") else ans["answer"]

                question = await Question.get_or_none(id=question_id).prefetch_related("variants")
                if not question:
                    return 0, f"question_{question_id}"

                variants = await question.variants.all()
                correct_variant = next((v for v in variants if v.is_correct), None)
                selected_variant = next((v for v in variants if v.text.strip().upper() == answer_text.strip().upper()), None)

                is_correct = selected_variant.is_correct if selected_variant else False
                if is_correct:
                    total_score += question.score

                await Answer.create(
                    user_id=user_id,
                    reading_id=session_id,
                    question_id=question_id,
                    variant_id=selected_variant.id if selected_variant else None,
                    text=answer_text,
                    is_correct=is_correct,
                    correct_answer=correct_variant.text if correct_variant else "",
                    status=Answer.ANSWERED
                )

            session.status = Constants.ReadingStatus.COMPLETED
            session.end_time = datetime.now(timezone.utc)
            session.score = total_score
            await session.save()

        # Trigger async analysis (fire and forget)
        _ = ReadingAnalyseService.analyse_reading(session_id, user_id)

        return total_score, None

    @staticmethod
    async def finish_reading(reading_id: int, user_id: int) -> Tuple[Dict[str, Any], int]:
        reading = await Reading.get_or_none(id=reading_id, user_id=user_id).prefetch_related("passages__questions__variants")
        if not reading:
            return {"error": "Reading session not found"}, 400

        def minutes(dt_end: datetime, dt_start: datetime) -> float:
            return (dt_end - dt_start).total_seconds() / 60
        
        async def _save_or_update_overall_analysis(reading_id: int, user_id: int, correct: int, overall_score: float, timing: timedelta) -> Dict[str, Any]:
            obj, created = await ReadingAnalyseService.get_or_create(
                reading_id=reading_id,
                user_id=user_id,
                defaults={
                    "correct_answers": correct,
                    "overall_score": overall_score,
                    "timing": timing,
                    "feedback": f"You answered {correct} questions correctly. Your overall score is {overall_score}."
                }
            )
            if not created:
                obj.correct_answers = correct
                obj.overall_score = overall_score
                obj.timing = timing
                obj.feedback = f"You answered {correct} questions correctly. Your overall score is {overall_score}."
                await obj.save()
            return obj

        analysis_exists = await ReadingAnalyseService.exists(reading_id, user_id)
        if reading.status == Constants.ReadingStatus.COMPLETED and analysis_exists:
            analysis = await ReadingAnalyseService.get_or_create(reading_id, user_id)
            elapsed = minutes(reading.end_time, reading.start_time)
            correct_count = await Answer.filter(reading_id=reading_id, user_id=user_id, is_correct=True).count()
            total_questions = await Question.filter(passage__in=await reading.passages.all()).count()
            return {
                "score": round(analysis.overall_score, 2),
                "correct": f"{correct_count}/{total_questions}",
                "time": round(elapsed, 2),
            }, 200

        # Prepare data payload for GPT analysis
        prompt_data = []
        for passage in await reading.passages.all():
            passage_data = {"passage_id": passage.id, "passage": passage.text, "questions": []}
            for question in await passage.questions.all().prefetch_related("variants"):
                user_answer_obj = await Answer.get_or_none(reading_id=reading_id, user_id=user_id, question_id=question.id)
                user_answer_value = user_answer_obj.variant_id if user_answer_obj and user_answer_obj.variant_id else (user_answer_obj.text if user_answer_obj else "")
                passage_data["questions"].append({
                    "id": question.id,
                    "text": question.text,
                    "type": question.type,
                    "answers": [{"id": v.id, "text": v.text} for v in await question.variants.all()],
                    "user_answer": str(user_answer_value),
                })
            prompt_data.append(passage_data)

        if reading.status != Constants.ReadingStatus.COMPLETED:
            reading.status = Constants.ReadingStatus.COMPLETED
            reading.end_time = datetime.now(timezone.utc)
            await reading.save()

        chatgpt = ChatGPTIntegration()
        raw_response = await chatgpt.check_text_question_answer(json.dumps(prompt_data))
        cleaned_response = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            result = json.loads(cleaned_response)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from GPT"}, 500

        stats = next((item.get("stats") for item in result if "stats" in item), {})
        passages_analysis = next((item.get("passages") for item in result if "passages" in item), [])

        # Update answers with GPT analysis
        for passage in passages_analysis:
            for qa in passage.get("analysis", []):
                await Answer.update_or_create(
                    reading_id=reading_id,
                    user_id=user_id,
                    question_id=qa["question_id"],
                    defaults={
                        "is_correct": qa["is_correct"],
                        "explanation": qa.get("explanation", ""),
                        "correct_answer": qa.get("correct_answer", ""),
                        "status": Answer.ANSWERED if qa.get("user_answer") else Answer.NOT_ANSWERED,
                    }
                )

        # Save overall analysis summary
        overall_analysis = await _save_or_update_overall_analysis(
            reading_id=reading_id,
            user_id=user_id,
            correct=stats.get("total_correct", 0),
            overall_score=stats.get("overall_score", 0),
            timing=timedelta(minutes=minutes(reading.end_time, reading.start_time))
        )

        return {
            "score": round(stats.get("overall_score", 0), 2),
            "correct": f"{stats.get('total_correct', 0)}/{stats.get('total_questions', 0)}",
            "time": round(minutes(reading.end_time, reading.start_time), 2),
            "details": overall_analysis,
        }, 200

    @staticmethod
    async def cancel_reading(session_id: int, user_id: int) -> bool:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return False
        session.status = Constants.ReadingStatus.CANCELLED
        session.end_time = datetime.now(timezone.utc)
        await session.save(update_fields=["status", "end_time"])
        return True

    @staticmethod
    async def restart_reading(session_id: int, user_id: int) -> Tuple[Reading, Optional[str]]:
        session = await Reading.get_or_none(id=session_id, user_id=user_id)
        if not session:
            return None, "session_not_found"
        if session.status != Constants.ReadingStatus.COMPLETED:
            return None, "not_completed"

        # clear previous answers
        await Answer.filter(reading=session_id, user_id=user_id).delete()
        return await ReadingService.start_reading(user_id)

    @staticmethod
    async def analyse_reading(session_id: int, user_id: int) -> Dict[str, Any]:
        session = await Reading.get_or_none(id=session_id, user_id=user_id) \
                            .prefetch_related("passages__questions__variants")
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        passages = await session.passages.all()
        passages_result = []

        for passage in passages:
            questions = await passage.questions.all().prefetch_related("variants")
            questions_result = []

            for q in questions:
                ua = await Answer.get_or_none(question_id=q.id, user_id=user_id)
                variants = await q.variants.all()
                correct = next(v for v in variants if v.is_correct)

                questions_result.append({
                    "id": q.id,
                    "text": q.text,
                    "options": [{"text": v.text} for v in variants],
                    "user_answer": ua.text if ua and ua.text else None,
                    "is_correct": ua.is_correct if ua else False,
                    "correct_answer": correct.text,
                })

            passages_result.append({
                "passage_id": passage.id,
                "passage_text": passage.text,
                "questions": questions_result,
            })

        return {
            "passages": passages_result,
            "total_score": session.score,
            "duration": (session.end_time - session.start_time).total_seconds() / 60
                        if session.end_time else None
        }
