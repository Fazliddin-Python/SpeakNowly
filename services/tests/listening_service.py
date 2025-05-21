import random
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from models.tests.listening import (
    Listening, ListeningPart, ListeningSection, ListeningQuestion,
    UserListeningSession, UserResponse
)

logger = logging.getLogger(__name__)

class ListeningService:
    @staticmethod
    async def list_tests() -> List[Listening]:
        """
        Get all listening tests.
        """
        return await Listening.all()

    @staticmethod
    async def get_test(test_id: int) -> Optional[Listening]:
        """
        Get a listening test by ID.
        """
        return await Listening.get_or_none(id=test_id)

    @staticmethod
    async def create_test(data: dict) -> Listening:
        """
        Create a new listening test.
        """
        return await Listening.create(**data)

    @staticmethod
    async def delete_test(test_id: int) -> bool:
        """
        Delete a listening test by ID.
        """
        test = await Listening.get_or_none(id=test_id)
        if not test:
            logger.warning("Listening test %s not found for deletion", test_id)
            return False
        await test.delete()
        logger.info("Listening test %s deleted", test_id)
        return True

    @staticmethod
    async def start_session(user_id: int) -> Optional[UserListeningSession]:
        """
        Start a new listening session for a user.
        """
        logger.info("User %s is starting a listening session", user_id)
        tests = await Listening.all()
        if not tests:
            logger.warning("No listening tests available for user %s", user_id)
            return None
        selected = random.choice(tests)
        session = await UserListeningSession.create(
            user_id=user_id,
            exam_id=selected.id,
            start_time=datetime.now(timezone.utc),
            status="started",
        )
        logger.info("Listening session %s started for user %s", session.id, user_id)
        return session

    @staticmethod
    async def submit_answers(
        session_id: int,
        user_id: int,
        answers: List[dict]
    ) -> Tuple[int, Optional[str]]:
        """
        Submit answers for a listening session and calculate the score.
        """
        logger.info("User %s submits answers for session %s", user_id, session_id)
        session = await UserListeningSession.get_or_none(id=session_id)
        if not session:
            logger.warning("Session %s not found for user %s", session_id, user_id)
            return 0, "not_found"
        if session.user_id != user_id:
            logger.warning("User %s tried to submit answers for another user's session %s", user_id, session_id)
            return 0, "forbidden"
        if session.status == "completed":
            logger.info("Session %s already completed", session_id)
            return 0, "already_completed"

        total_score = 0
        answered_ids = set()
        for answer in answers:
            question = await ListeningQuestion.get_or_none(id=answer["question_id"])
            if not question:
                logger.warning("Question %s not found in session %s", answer["question_id"], session_id)
                return 0, f"question_{answer['question_id']}_not_found"
            is_correct = question.correct_answer == answer["user_answer"]
            score = 1 if is_correct else 0
            total_score += score
            await UserResponse.create(
                session_id=session_id,
                user_id=user_id,
                question_id=answer["question_id"],
                user_answer=answer["user_answer"],
                is_correct=is_correct,
                score=score,
            )
            answered_ids.add(answer["question_id"])

        # Mark unanswered questions as incorrect
        all_questions = await ListeningQuestion.filter(section__part__listening_id=session.exam_id).all()
        for q in all_questions:
            if q.id not in answered_ids:
                await UserResponse.create(
                    session_id=session_id,
                    user_id=user_id,
                    question_id=q.id,
                    user_answer=None,
                    is_correct=False,
                    score=0,
                )

        session.status = "completed"
        session.end_time = datetime.now(timezone.utc)
        await session.save()
        logger.info("Session %s completed for user %s, score: %d", session_id, user_id, total_score)
        return total_score, None

    @staticmethod
    async def get_session(session_id: int) -> Optional[UserListeningSession]:
        """
        Get a listening session by ID.
        """
        return await UserListeningSession.get_or_none(id=session_id)

    @staticmethod
    async def cancel_session(session_id: int, user_id: int) -> bool:
        """
        Cancel a listening session.
        """
        session = await UserListeningSession.get_or_none(id=session_id)
        if not session or session.user_id != user_id or session.status in ["completed", "cancelled"]:
            logger.warning("Cannot cancel session %s for user %s", session_id, user_id)
            return False
        session.status = "cancelled"
        await session.save()
        logger.info("Session %s cancelled for user %s", session_id, user_id)
        return True

    @staticmethod
    async def get_part(part_id: int) -> Optional[ListeningPart]:
        """
        Get a listening part by ID.
        """
        return await ListeningPart.get_or_none(id=part_id).prefetch_related("sections")

    @staticmethod
    async def list_sections() -> List[ListeningSection]:
        """
        Get all listening sections.
        """
        return await ListeningSection.all()

    @staticmethod
    async def get_section(section_id: int) -> Optional[ListeningSection]:
        """
        Get a listening section by ID.
        """
        return await ListeningSection.get_or_none(id=section_id)

    @staticmethod
    async def create_section(data: dict) -> ListeningSection:
        """
        Create a new listening section.
        """
        return await ListeningSection.create(**data)

    @staticmethod
    async def delete_section(section_id: int) -> bool:
        """
        Delete a listening section by ID.
        """
        section = await ListeningSection.get_or_none(id=section_id)
        if not section:
            logger.warning("Listening section %s not found for deletion", section_id)
            return False
        await section.delete()
        logger.info("Listening section %s deleted", section_id)
        return True

    @staticmethod
    async def list_questions() -> List[ListeningQuestion]:
        """
        Get all listening questions.
        """
        return await ListeningQuestion.all()

    @staticmethod
    async def get_question(question_id: int) -> Optional[ListeningQuestion]:
        """
        Get a listening question by ID.
        """
        return await ListeningQuestion.get_or_none(id=question_id)

    @staticmethod
    async def create_question(data: dict) -> ListeningQuestion:
        """
        Create a new listening question.
        """
        return await ListeningQuestion.create(**data)

    @staticmethod
    async def delete_question(question_id: int) -> bool:
        """
        Delete a listening question by ID.
        """
        question = await ListeningQuestion.get_or_none(id=question_id)
        if not question:
            logger.warning("Listening question %s not found for deletion", question_id)
            return False
        await question.delete()
        logger.info("Listening question %s deleted", question_id)
        return True