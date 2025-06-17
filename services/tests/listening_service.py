from fastapi import HTTPException, status, Request
from typing import List, Dict, Any
from tortoise.transactions import in_transaction
from datetime import datetime, timezone
import random
from tortoise.exceptions import FieldError

from models.tests import (
    Listening,
    ListeningPart,
    ListeningSection,
    ListeningQuestion,
    ListeningSessionStatus,
    ListeningSession,
    ListeningAnswer,
)
from services.analyses import ListeningAnalyseService

class ListeningService:
    """
    Service for managing listening tests and sessions.
    """

    @staticmethod
    async def start_session(user, t: dict) -> Dict[str, Any]:
        """
        Start a new listening session for a user by selecting a random test.
        """
        tests = await Listening.all().prefetch_related("parts__sections__questions")
        if not tests:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["no_listening_tests"]
            )

        selected_test = random.choice(tests)
        session = await ListeningSession.create(
            user_id=user.id,
            exam_id=selected_test.id,
            start_time=datetime.now(timezone.utc),
            status=ListeningSessionStatus.STARTED.value,
        )

        parts = await ListeningPart.filter(listening_id=selected_test.id)

        return {
            "session_id": session.id,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "exam": selected_test,
            "parts": parts,
        }

    @staticmethod
    async def get_session_data(session_id: int, user_id: int, t: dict) -> Dict[str, Any]:
        """
        Get detail of a listening session.
        """
        session = await ListeningSession.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["session_not_found"]
            )
        exam = await Listening.get(id=session.exam_id)
        parts = await ListeningPart.filter(listening_id=exam.id)
        return {
            "session_id": session.id,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "exam": exam,
            "parts": parts,
        }

    @staticmethod
    async def get_part(part_id: int, t: dict):
        """
        Get detail of a listening part.
        """
        part = await ListeningPart.get_or_none(id=part_id)
        if not part:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_part_not_found"]
            )
        return part

    @staticmethod
    async def submit_answers(
        session_id: int, user_id: int, answers: List[Any], t: dict
    ) -> Dict[str, Any]:
        session = await ListeningSession.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["session_not_found"]
            )
        if session.status == ListeningSessionStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["session_already_completed"]
            )

        total_score = 0
        answered_question_ids = [answer.question_id for answer in answers]

        async with in_transaction():
            for answer in answers:
                question = await ListeningQuestion.get_or_none(id=answer.question_id)
                if not question:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=t["question_not_found"].format(question_id=answer.question_id)
                    )

                user_answer = answer.user_answer

                section = await ListeningSection.get(id=question.section_id)
                q_type = section.question_type

                if q_type in ["cloze_test", "form_completion", "sentence_completion"]:
                    if isinstance(question.correct_answer, list) and isinstance(user_answer, list):
                        is_correct = all(
                            str(a).strip().lower() == str(b).strip().lower()
                            for a, b in zip(user_answer, question.correct_answer)
                        )
                    else:
                        is_correct = str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
                elif q_type == "choice":
                    is_correct = str(user_answer) == str(question.correct_answer[0])
                elif q_type == "multiple_answers":
                    is_correct = set(map(str, question.correct_answer)) == set(map(str, user_answer))
                elif q_type == "matching":
                    is_correct = user_answer == question.correct_answer
                else:
                    is_correct = str(user_answer) == str(question.correct_answer)

                total_score += int(is_correct)

                ua = user_answer
                if isinstance(ua, bool):
                    norm_answer = None
                elif isinstance(ua, (str, int, float, list, dict)):
                    norm_answer = ua
                else:
                    norm_answer = None

                try:
                    await ListeningAnswer.create(
                        session_id=session_id,
                        user_id=user_id,
                        question_id=question.id,
                        user_answer=norm_answer,
                        is_correct=is_correct,
                        score=int(is_correct),
                    )
                except FieldError:
                    await ListeningAnswer.create(
                        session_id=session_id,
                        user_id=user_id,
                        question_id=question.id,
                        user_answer=None,
                        is_correct=is_correct,
                        score=int(is_correct),
                    )

            all_questions = await ListeningQuestion.filter(section__part__listening_id=session.exam_id)
            unanswered_questions = [q for q in all_questions if q.id not in answered_question_ids]

            for question in unanswered_questions:
                try:
                    await ListeningAnswer.create(
                        session_id=session_id,
                        user_id=user_id,
                        question_id=question.id,
                        user_answer=[],
                        is_correct=False,
                        score=0,
                    )
                except FieldError:
                    await ListeningAnswer.create(
                        session_id=session_id,
                        user_id=user_id,
                        question_id=question.id,
                        user_answer=None,
                        is_correct=False,
                        score=0,
                    )

            session.status = ListeningSessionStatus.COMPLETED.value
            session.end_time = datetime.now(timezone.utc)
            await session.save(update_fields=["status", "end_time"])

        return {"message": t["answers_submitted"], "total_score": total_score}

    @staticmethod
    async def cancel_session(session_id: int, user_id: int, t: dict) -> Dict[str, Any]:
        """
        Cancel a listening session.
        """
        session = await ListeningSession.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["session_not_found"]
            )

        if session.status in [ListeningSessionStatus.COMPLETED.value, ListeningSessionStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["cannot_cancel_session"]
            )

        session.status = ListeningSessionStatus.CANCELLED.value
        await session.save(update_fields=["status"])
        return {"message": t["session_cancelled"]}

    @staticmethod
    async def restart_session(session_id: int, user_id: int, t: dict) -> Dict[str, Any]:
        """
        Restart a listening session.
        """
        session = await ListeningSession.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["session_not_found"]
            )

        if session.status not in [ListeningSessionStatus.COMPLETED.value, ListeningSessionStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["cannot_restart_session"]
            )

        await ListeningAnswer.filter(session_id=session_id, user_id=user_id).delete()
        session.status = ListeningSessionStatus.STARTED.value
        session.start_time = datetime.now(timezone.utc)
        session.end_time = None
        await session.save(update_fields=["status", "start_time", "end_time"])
        return {"message": t["session_restarted"]}

    @staticmethod
    async def get_analysis(session_id: int, user_id: int, t: dict, request: Request = None) -> Dict[str, Any]:
        """
        Get or create analysis for a completed listening session.
        """
        session = await ListeningSession.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["session_not_found"]
            )
        if session.status != ListeningSessionStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["session_not_completed"]
            )
        analyse = await ListeningAnalyseService.analyse(session_id)
        responses = await ListeningAnswer.filter(session_id=session_id).prefetch_related("question")
        responses_data = []
        for r in responses:
            responses_data.append({
                "id": r.id,
                "user_answer": r.user_answer,
                "is_correct": r.is_correct,
                "score": float(r.score) if r.score is not None else None,
                "correct_answer": r.question.correct_answer if r.question else None,
                "question_index": r.question.index if r.question else None,
            })
        parts = await ListeningPart.filter(listening_id=session.exam_id)
        listening_parts = [
            {
                "part_number": part.part_number,
                "audio_file": part.audio_file,
            }
            for part in parts
        ]
        return {
            "session_id": session.id,
            "analysis": {
                "correct_answers": analyse.correct_answers,
                "overall_score": float(analyse.overall_score) if analyse.overall_score is not None else None,
                "timing": analyse.duration.total_seconds() if analyse.duration else None,
            },
            "responses": responses_data,
            "listening_parts": listening_parts,
        }