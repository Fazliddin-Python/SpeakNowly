import random
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

from fastapi import HTTPException
from tortoise.transactions import in_transaction

from models.tests.listening import (
    Listening,
    ListeningPart,
    ListeningSection,
    ListeningQuestion,
    UserListeningSession,
    UserResponse,
)

logger = logging.getLogger(__name__)

class ListeningService:
    """
    Service layer for handling listening test operations: managing tests, sessions,
    and user responses. Interacts with Tortoise ORM models and triggers background
    analysis tasks.
    """

    @staticmethod
    async def _get_session(session_id: int, user_id: int) -> UserListeningSession:
        """
        Retrieve a UserListeningSession by ID and verify ownership.

        :param session_id: ID of the listening session.
        :param user_id: ID of the user requesting the session.
        :return: UserListeningSession instance.
        :raises HTTPException: if session not found or user unauthorized.
        """
        session = await UserListeningSession.get_or_none(id=session_id)
        if not session or session.user_id != user_id:
            logger.warning(
                f"Session not found or forbidden: session_id={session_id}, user_id={user_id}"
            )
            raise HTTPException(status_code=404, detail="Listening session not found")
        return session

    @staticmethod
    async def list_tests() -> List[Listening]:
        """
        Fetch all listening tests along with their nested parts, sections, and questions.

        :return: List of Listening test instances.
        """
        logger.info("Fetching all listening tests")
        return await Listening.all().prefetch_related("parts__sections__questions")

    @staticmethod
    async def get_test(test_id: int) -> Listening:
        """
        Retrieve a single listening test by ID.

        :param test_id: ID of the listening test.
        :return: Listening instance.
        :raises HTTPException: if test not found.
        """
        logger.info(f"Fetching listening test id={test_id}")
        test = await Listening.get_or_none(id=test_id).prefetch_related(
            "parts__sections__questions"
        )
        if not test:
            logger.warning(f"Listening test not found: test_id={test_id}")
            raise HTTPException(status_code=404, detail="Listening test not found")
        return test

    @staticmethod
    async def create_test(data: Dict[str, Any]) -> Listening:
        """
        Create a new listening test.

        :param data: Dictionary containing test fields (title, description).
        :return: Newly created Listening instance.
        """
        logger.info(f"Creating listening test: {data}")
        return await Listening.create(**data)

    @staticmethod
    async def delete_test(test_id: int) -> None:
        """
        Delete an existing listening test by ID.

        :param test_id: ID of the test to delete.
        :raises HTTPException: if test not found.
        """
        logger.info(f"Deleting listening test id={test_id}")
        deleted_count = await Listening.filter(id=test_id).delete()
        if not deleted_count:
            logger.warning(f"Listening test not found for delete: test_id={test_id}")
            raise HTTPException(status_code=404, detail="Listening test not found")

    @staticmethod
    async def start_session(user_id: int) -> UserListeningSession:
        """
        Start a new listening session for a user by randomly selecting a test.

        :param user_id: ID of the user starting the session.
        :return: Newly created UserListeningSession instance.
        :raises HTTPException: if no tests available.
        """
        logger.info(f"Starting listening session for user_id={user_id}")
        tests = await Listening.all()
        if not tests:
            logger.warning("No listening tests available to start session")
            raise HTTPException(status_code=404, detail="No listening tests available")

        selected_test = random.choice(tests)
        session = await UserListeningSession.create(
            user_id=user_id,
            exam_id=selected_test.id,
            start_time=datetime.now(timezone.utc),
            status="started",
        )
        logger.info(
            f"Created session_id={session.id} for user_id={user_id}, exam_id={selected_test.id}"
        )
        return session

    @staticmethod
    async def submit_answers(
        session_id: int,
        user_id: int,
        answers: List[Dict[str, Any]],
    ) -> int:
        """
        Validate and record user answers for a listening session, compute score,
        fill in unanswered questions, mark session complete, and enqueue analysis.

        :param session_id: ID of the listening session.
        :param user_id: ID of the user submitting answers.
        :param answers: List of answer dicts with keys 'question' and 'user_answer'.
        :return: Total score achieved by the user.
        :raises HTTPException: on invalid session, forbidden, or re-submission.
        """
        logger.info(f"Submitting answers for session_id={session_id}, user_id={user_id}")
        async with in_transaction():
            session = await ListeningService._get_session(session_id, user_id)
            if session.status == "completed":
                logger.warning(f"Attempt to resubmit completed session_id={session_id}")
                raise HTTPException(status_code=400, detail="Session already completed")

            # remove old responses if any
            await UserResponse.filter(session_id=session_id, user_id=user_id).delete()

            total_score = 0
            answered_questions = set()

            # record provided answers
            for ans in answers:
                question_id = ans.get("question_id")
                user_answer = ans.get("user_answer")

                # Приводим user_answer к списку, если это не список
                if not isinstance(user_answer, list):
                    user_answer = [user_answer]

                question = await ListeningQuestion.get_or_none(id=question_id)
                if not question:
                    logger.warning(f"Invalid question_id={question_id} in submitted answers")
                    raise HTTPException(
                        status_code=404, detail=f"Question {question_id} not found"
                    )

                logger.info(f"user_answer={user_answer!r}, type={type(user_answer)}")

                correct = set(map(str, question.correct_answer)) == set(map(str, user_answer))
                score = 1 if correct else 0
                total_score += score

                await UserResponse.create(
                    session_id=session_id,
                    user_id=user_id,
                    question_id=question_id,
                    user_answer=user_answer,
                    is_correct=correct,
                    score=score,
                )
                answered_questions.add(question_id)

            # fill unanswered questions with zero scores
            unanswered = await ListeningQuestion.filter(
                section__part__listening_id=session.exam_id
            ).exclude(id__in=answered_questions).all()
            for q in unanswered:
                await UserResponse.create(
                    session_id=session_id,
                    user_id=user_id,
                    question_id=q.id,
                    user_answer=None,
                    is_correct=False,
                    score=0,
                )

            # finalize session
            session.status = "completed"
            session.end_time = datetime.now(timezone.utc)
            await session.save()

        # trigger background analysis
        from tasks.analyses.listening_tasks import analyse_listening_task
        analyse_listening_task.delay(session_id)
        logger.info(
            f"Session_id={session_id} completed, total_score={total_score}"
        )
        return total_score

    @staticmethod
    async def get_session(session_id: int, user_id: int) -> UserListeningSession:
        """
        Retrieve session details for a user.
        """
        return await ListeningService._get_session(session_id, user_id)

    @staticmethod
    async def cancel_session(session_id: int, user_id: int) -> None:
        """
        Cancel an ongoing session if not already completed or cancelled.

        :param session_id: ID of the session to cancel.
        :param user_id: ID of the user requesting cancellation.
        :raises HTTPException: if session cannot be cancelled.
        """
        session = await ListeningService._get_session(session_id, user_id)
        if session.status == "completed":
            logger.warning(
                f"Cancellation forbidden for session_id={session_id}, status={session.status}"
            )
            raise HTTPException(
                status_code=400, detail="Session cannot be cancelled"
            )
        if session.status == "cancelled":
            logger.info(f"Session_id={session_id} already cancelled")
            return  # Просто возвращаем успех
        session.status = "cancelled"
        await session.save()
        logger.info(f"Session_id={session_id} has been cancelled")

    @staticmethod
    async def get_session_data(session_id: int, user_id: int) -> Dict[str, Any]:
        session = await UserListeningSession.get(id=session_id, user_id=user_id).prefetch_related(
            "exam__parts__sections__questions"
        )
        exam = session.exam
        parts = await exam.parts.all().prefetch_related("sections__questions")
        part_list = []
        for part in parts:
            sections = await part.sections.all().prefetch_related("questions")
            section_list = []
            for section in sections:
                questions = await section.questions.all()
                question_list = []
                for q in questions:
                    question_list.append({
                        "id": q.id,
                        "section_id": q.section_id,
                        "index": q.index,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                    })
                section_list.append({
                    "id": section.id,
                    "part_id": section.part_id,
                    "section_number": section.section_number,
                    "start_index": section.start_index,
                    "end_index": section.end_index,
                    "question_type": section.question_type,
                    "question_text": section.question_text,
                    "options": section.options,
                    "questions": question_list,
                })
            part_list.append({
                "id": part.id,
                "listening_id": part.listening_id,
                "part_number": part.part_number,
                "audio_file": part.audio_file,
                "sections": section_list,
            })
        return {
            "id": session.id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "session_id": session.id,
            "start_time": session.start_time,
            "status": session.status,
            "exam": {
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
            },
            "parts": part_list,
        }

    @staticmethod
    async def submit_answers(session_id: int, user_id: int, data: Dict[str, Any]) -> None:
        session = await UserListeningSession.get(id=session_id, user_id=user_id)
        if session.status == "completed":
            raise HTTPException(status_code=400, detail="Session already completed")
        all_answers = []
        for part_answers in data["answers"].values():
            all_answers.extend([a.dict() if hasattr(a, "dict") else a for a in part_answers])
        async with in_transaction():
            await UserResponse.filter(session_id=session_id, user_id=user_id).delete()
            for ans in all_answers:
                question_id = ans["question_id"]
                answer = ans.get("answer", ans.get("user_answer"))

                if not isinstance(answer, list):
                    answer = [answer]

                question = await ListeningQuestion.get_or_none(id=question_id)
                if not question:
                    raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

                correct = set(map(str, question.correct_answer)) == set(map(str, answer))
                score = 1 if correct else 0

                await UserResponse.create(
                    session_id=session_id,
                    user_id=user_id,
                    question_id=question_id,
                    user_answer=answer,
                    is_correct=correct,
                    score=score,
                )
            session.status = "completed"
            session.end_time = datetime.now(timezone.utc)
            await session.save()
        # импорт внутри метода, чтобы избежать циклического импорта
        from tasks.analyses.listening_tasks import analyse_listening_task
        analyse_listening_task.delay(session_id)

    @staticmethod
    async def get_analysis(session_id: int, user_id: int) -> Dict[str, Any]:
        # Здесь должен быть вызов ListeningAnalyseService
        from services.analyses.listening_analyse_service import ListeningAnalyseService
        analyse_obj = await ListeningAnalyseService.get_analysis(session_id)
        responses = await UserResponse.filter(session_id=session_id, user_id=user_id).prefetch_related("question")
        resp_list = []
        for r in responses:
            resp_list.append({
                "id": r.id,
                "user_answer": r.user_answer,
                "is_correct": r.is_correct,
                "score": r.score,
                "correct_answer": [r.question.correct_answer] if r.question else [],
                "question_index": r.question.index if r.question else None,
            })
        return {
            "session_id": session_id,
            "analyse": {
                "correct_answers": analyse_obj.correct_answers,
                "overall_score": analyse_obj.overall_score,
                "timing": str(analyse_obj.timing),
                "feedback": analyse_obj.feedback,
            },
            "responses": resp_list,
        }

    @staticmethod
    async def get_part(part_id: int) -> ListeningPart:
        part = await ListeningPart.get_or_none(id=part_id).prefetch_related("sections__questions")
        if not part:
            raise HTTPException(status_code=404, detail="Listening part not found")
        return part

    @staticmethod
    async def create_part(data: Dict[str, Any]) -> ListeningPart:
        return await ListeningPart.create(**data)

    @staticmethod
    async def list_sections() -> ListeningSection:
        return await ListeningSection.all().prefetch_related("questions")

    @staticmethod
    async def get_section(section_id: int) -> ListeningSection:
        section = await ListeningSection.get_or_none(id=section_id).prefetch_related("questions")
        if not section:
            raise HTTPException(status_code=404, detail="Listening section not found")
        return section

    @staticmethod
    async def create_section(data: Dict[str, Any]) -> ListeningSection:
        return await ListeningSection.create(**data)

    @staticmethod
    async def delete_section(section_id: int) -> None:
        deleted = await ListeningSection.filter(id=section_id).delete()
        if not deleted:
            raise HTTPException(status_code=404, detail="Listening section not found")

    @staticmethod
    async def list_questions() -> ListeningQuestion:
        return await ListeningQuestion.all()

    @staticmethod
    async def get_question(question_id: int) -> ListeningQuestion:
        question = await ListeningQuestion.get_or_none(id=question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Listening question not found")
        return question

    @staticmethod
    async def create_question(data: Dict[str, Any]) -> ListeningQuestion:
        ca = data.get("correct_answer")
        if ca is not None and not isinstance(ca, list):
            data["correct_answer"] = [ca]
        return await ListeningQuestion.create(**data)

    @staticmethod
    async def delete_question(question_id: int) -> None:
        deleted = await ListeningQuestion.filter(id=question_id).delete()
        if not deleted:
            raise HTTPException(status_code=404, detail="Listening question not found")