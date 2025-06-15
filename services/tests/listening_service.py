import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from uuid import uuid4
import random

from fastapi import HTTPException, status, UploadFile
from tortoise.transactions import in_transaction

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
from config import BASE_DIR


class ListeningService:
    """
    Service for managing listening tests and sessions.
    """

    # --- TEST OPERATIONS ---

    @staticmethod
    async def list_tests(t: dict) -> List[Listening]:
        """
        Retrieve all listening tests with nested parts, sections, and questions.
        """
        return await Listening.all().prefetch_related("parts__sections__questions")

    @staticmethod
    async def get_test(test_id: int, t: dict) -> Listening:
        """
        Retrieve a single listening test by ID. Raise 404 if not found.
        """
        test = await Listening.get_or_none(id=test_id).prefetch_related("parts__sections__questions")
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_test_not_found"]
            )
        return test

    @staticmethod
    async def create_test(data: Dict[str, Any], t: dict) -> Listening:
        """
        Create a new listening test. Validates unique title.
        """
        title = data["title"].strip()
        existing = await Listening.get_or_none(title=title)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["listening_test_already_exists"].format(title=title)
            )
        return await Listening.create(**data)

    @staticmethod
    async def delete_test(test_id: int, t: dict) -> None:
        """
        Delete a listening test by ID. Raise 404 if not found.
        """
        deleted_count = await Listening.filter(id=test_id).delete()
        if not deleted_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_test_not_found"]
            )

    # --- PART OPERATIONS ---

    @staticmethod
    async def create_part(
        listening_id: int,
        part_number: int,
        audio_file: UploadFile,
        t: dict,
    ) -> ListeningPart:
        """
        Create a ListeningPart and upload its audio file.
        """
        if audio_file.content_type not in ("audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["invalid_audio_type"]
            )

        # Use BASE_DIR for constructing the save directory
        save_dir = os.path.join(BASE_DIR, "media", "audios")
        os.makedirs(save_dir, exist_ok=True)
        file_ext = audio_file.filename.split('.')[-1]
        file_name = f"part_audio_{uuid4()}.{file_ext}"
        file_path = os.path.join(save_dir, file_name)

        # Save the audio file
        file_content = await audio_file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)

        audio_url = f"/media/audios/{file_name}"

        return await ListeningPart.create(
            listening_id=listening_id,
            part_number=part_number,
            audio_file=audio_url,
        )

    # --- SESSION OPERATIONS ---

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
    async def submit_answers(
        session_id: int, user_id: int, answers: List[Dict[str, Any]], t: dict
    ) -> Dict[str, Any]:
        """
        Submit user answers for a listening session and calculate the total score.
        """
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
        answered_question_ids = [answer["question_id"] for answer in answers]

        async with in_transaction():
            for answer in answers:
                question = await ListeningQuestion.get_or_none(id=answer["question_id"])
                if not question:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=t["question_not_found"].format(question_id=answer["question_id"])
                    )

                user_answer = answer["user_answer"]
                is_correct = set(map(str, question.correct_answer)) == set(map(str, user_answer))
                total_score += int(is_correct)

                await ListeningAnswer.create(
                    session_id=session_id,
                    user_id=user_id,
                    question_id=question.id,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    score=int(is_correct),
                )

            all_questions = await ListeningQuestion.filter(section__part__listening_id=session.exam_id)
            unanswered_questions = all_questions.exclude(id__in=answered_question_ids)

            for question in unanswered_questions:
                await ListeningAnswer.create(
                    session_id=session_id,
                    user_id=user_id,
                    question_id=question.id,
                    user_answer=[],
                    is_correct=False,
                    score=0,
                )

            await ListeningAnalyseService.analyse(session_id)

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
    async def get_analysis(session_id: int, user_id: int, t: dict) -> Dict[str, Any]:
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
        return {
            "analysis": {
                "correct_answers": analyse.correct_answers,
                "overall_score": float(analyse.overall_score) if analyse.overall_score is not None else None,
                "timing": analyse.duration.total_seconds() if analyse.duration else None,
            }
        }