import random
import logging
import os
from typing import List, Dict, Any
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status, UploadFile
from tortoise.transactions import in_transaction
from minio import Minio
from uuid import uuid4
from io import BytesIO

from models.tests.listening import (
    Listening,
    ListeningPart,
    ListeningSection,
    ListeningQuestion,
    ListeningSessionStatus,
    UserListeningSession,
    UserResponse,
)
from models.transactions import TransactionType
from utils.check_tokens import check_user_tokens

logger = logging.getLogger(__name__)


class ListeningService:
    """
    Service layer: handles CRUD operations and business logic for listening tests and sessions.
    """

    # --- TEST OPERATIONS ---

    @staticmethod
    async def list_tests() -> List[Listening]:
        """
        Retrieve all listening tests with nested parts, sections, and questions.
        """
        return await Listening.all().prefetch_related("parts__sections__questions")

    @staticmethod
    async def get_test(test_id: int, t: dict) -> Listening:
        """
        Get a single listening test by ID. Raise 404 if not found.
        """
        test = await Listening.get_or_none(id=test_id).prefetch_related("parts__sections__questions")
        if not test:
            logger.warning(f"Listening test not found (id={test_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_test_not_found"]
            )
        return test

    @staticmethod
    async def create_test(data: Dict[str, Any]) -> Listening:
        """
        Create a new listening test. Validates unique title.
        """
        title = data["title"].strip()
        existing = await Listening.get_or_none(title=title)
        if existing:
            logger.error(f"Duplicate listening test title: '{title}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Listening test with title '{title}' already exists"
            )
        data["title"] = title
        new_test = await Listening.create(**data)
        logger.info(f"Created listening test id={new_test.id}")
        return new_test

    @staticmethod
    async def delete_test(test_id: int, t: dict) -> None:
        """
        Delete a listening test by ID. Raise 404 if not found.
        """
        deleted_count = await Listening.filter(id=test_id).delete()
        if not deleted_count:
            logger.warning(f"Attempt to delete nonexistent listening test (id={test_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_test_not_found"]
            )
        logger.info(f"Deleted listening test id={test_id}")

    # --- PART OPERATIONS ---

    @staticmethod
    async def get_part(part_id: int, t: dict) -> ListeningPart:
        """
        Retrieve a listening part by its ID. Raise 404 if not found.
        """
        part = await ListeningPart.get_or_none(id=part_id).prefetch_related("sections__questions")
        if not part:
            logger.warning(f"Listening part not found (id={part_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_part_not_found"]
            )
        return part

    @staticmethod
    async def create_part(
        listening_id: int,
        part_number: int,
        audio_file: UploadFile,
        t: dict,
    ):
        """
        Create a ListeningPart and upload its audio file to media/audios folder.
        """
        # 1. Проверяем тип файла
        if audio_file.content_type not in ("audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"):
            logger.error("Invalid audio type: %s", audio_file.content_type)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("invalid_audio_type", "Invalid audio type")
            )

        # 2. Готовим путь для сохранения
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        save_dir = os.path.join(project_root, "media", "audios")
        os.makedirs(save_dir, exist_ok=True)
        file_ext = audio_file.filename.split('.')[-1]
        file_name = f"part_audio_{uuid4()}.{file_ext}"
        file_path = os.path.join(save_dir, file_name)

        # 3. Сохраняем файл на диск
        file_content = await audio_file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 4. Формируем ссылку для БД
        audio_url = f"/media/audios/{file_name}"

        # 5. Создаём запись ListeningPart
        part = await ListeningPart.create(
            listening_id=listening_id,
            part_number=part_number,
            audio_file=audio_url,
        )
        logger.info(f"Created ListeningPart id={part.id} for listening_id={listening_id}")
        return part

    # --- SECTION OPERATIONS ---

    @staticmethod
    async def list_sections() -> List[ListeningSection]:
        """
        Retrieve all listening sections with their questions.
        """
        return await ListeningSection.all().prefetch_related("questions")

    @staticmethod
    async def get_section(section_id: int, t: dict) -> ListeningSection:
        """
        Retrieve a listening section by ID. Raise 404 if not found.
        """
        section = await ListeningSection.get_or_none(id=section_id).prefetch_related("questions")
        if not section:
            logger.warning(f"Listening section not found (id={section_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_section_not_found"]
            )
        return section

    @staticmethod
    async def create_section(data: Dict[str, Any]) -> ListeningSection:
        """
        Create a new listening section. Ensures parent part exists and section_number is unique.
        """
        parent_part = await ListeningPart.get_or_none(id=data["part_id"])
        if not parent_part:
            logger.error(f"Parent listening part not found (id={data['part_id']})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent listening part not found"
            )

        exists = await ListeningSection.filter(
            part_id=data["part_id"], section_number=data["section_number"]
        ).exists()
        if exists:
            logger.error(f"Duplicate section_number {data['section_number']} for part_id={data['part_id']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Section number {data['section_number']} already exists for this part"
            )

        section = await ListeningSection.create(**data)
        logger.info(f"Created listening section id={section.id} under part_id={section.part_id}")
        return section

    @staticmethod
    async def delete_section(section_id: int, t: dict) -> None:
        """
        Delete a listening section by ID. Raise 404 if not found.
        """
        deleted = await ListeningSection.filter(id=section_id).delete()
        if not deleted:
            logger.warning(f"Attempt to delete nonexistent listening section (id={section_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_section_not_found"]
            )
        logger.info(f"Deleted listening section id={section_id}")

    # --- QUESTION OPERATIONS ---

    @staticmethod
    async def list_questions() -> List[ListeningQuestion]:
        """
        Retrieve all listening questions.
        """
        return await ListeningQuestion.all()

    @staticmethod
    async def get_question(question_id: int, t: dict) -> ListeningQuestion:
        """
        Retrieve a listening question by ID. Raise 404 if not found.
        """
        question = await ListeningQuestion.get_or_none(id=question_id)
        if not question:
            logger.warning(f"Listening question not found (id={question_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["question_not_found"]
            )
        return question

    @staticmethod
    async def create_question(data: Dict[str, Any]) -> ListeningQuestion:
        """
        Create a new listening question. Validates parent section and data consistency.
        """
        parent_section = (
            await ListeningSection.get_or_none(id=data["section_id"])
            .prefetch_related("part__listening")
        )
        if not parent_section:
            logger.error(f"Parent listening section not found (id={data['section_id']})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent listening section not found"
            )

        # Ensure index uniqueness within section
        exists = await ListeningQuestion.filter(
            section_id=data["section_id"], index=data["index"]
        ).exists()
        if exists:
            logger.error(f"Duplicate question index {data['index']} in section_id={data['section_id']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question index {data['index']} already exists in this section"
            )

        qtype = parent_section.question_type
        opts = data.get("options")
        ca = data.get("correct_answer")

        # Validate options and correct_answer consistency
        if qtype in ["choice", "multiple_answers", "matching"]:
            if not opts or not isinstance(opts, list):
                logger.error(f"Options missing or invalid for question_type='{qtype}'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Options are required for question_type '{qtype}' and must be a non-empty list"
                )

            if qtype == "choice":
                if isinstance(ca, list):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="correct_answer must be a single value (not list) for choice"
                    )
                if ca not in opts:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"correct_answer '{ca}' not in options"
                    )

            elif qtype == "multiple_answers":
                if not isinstance(ca, list) or not ca:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="correct_answer must be a non-empty list for multiple_answers"
                    )
                for ans in ca:
                    if ans not in opts:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Each correct_answer must be one of options; '{ans}' not found"
                        )

            elif qtype == "matching":
                if not isinstance(ca, dict) or not ca:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="correct_answer must be a non-empty dict for matching"
                    )
                for key, val in ca.items():
                    if key not in opts or val not in opts:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"For matching, both key '{key}' and value '{val}' must be in options"
                        )
        else:
            # For form_completion / sentence_completion / cloze_test, ignore options
            data["options"] = None
            if not isinstance(ca, str) or not ca.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"correct_answer must be a non-empty string for question_type '{qtype}'"
                )

        # Normalize correct_answer to list for storage
        if not isinstance(ca, list):
            data["correct_answer"] = [ca]
        else:
            data["correct_answer"] = ca

        question = await ListeningQuestion.create(**data)
        logger.info(f"Created listening question id={question.id} in section_id={question.section_id}")
        return question

    @staticmethod
    async def delete_question(question_id: int, t: dict) -> None:
        """
        Delete a listening question by ID. Raise 404 if not found.
        """
        deleted = await ListeningQuestion.filter(id=question_id).delete()
        if not deleted:
            logger.warning(f"Attempt to delete nonexistent listening question (id={question_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["question_not_found"]
            )
        logger.info(f"Deleted listening question id={question_id}")

    # --- SESSION OPERATIONS ---

    @staticmethod
    async def start_session(user, request: Request, t: dict) -> UserListeningSession:
        """
        Start a new listening session for a user by selecting a random test.
        Deduct tokens, raise 402 if insufficient.
        """
        tests = await Listening.all().prefetch_related("parts")
        tests = [t for t in tests if t.parts and len(t.parts) > 0]
        if not tests:
            raise HTTPException(404, detail=t["no_listening_tests"])
        selected = random.choice(tests)

        # token check
        await check_user_tokens(user, TransactionType.TEST_LISTENING, request, t)

        session = await UserListeningSession.create(
            user_id=user.id,
            exam_id=selected.id,
            start_time=datetime.now(timezone.utc),
            status=ListeningSessionStatus.STARTED.value,
        )
        return session

    @staticmethod
    async def get_session(session_id: int, user_id: int, t: dict) -> UserListeningSession:
        """
        Retrieve a listening session by ID, ensure it belongs to the user.
        """
        return await ListeningService._get_session(session_id, user_id, t)

    @staticmethod
    async def cancel_session(session_id: int, user_id: int, t: dict) -> None:
        """
        Cancel an ongoing session if not already completed.
        """
        session = await UserListeningSession.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(404, detail=t["session_not_found"])
        if session.status == ListeningSessionStatus.COMPLETED.value:
            raise HTTPException(400, detail=t["session_already_completed"])
        session.status = ListeningSessionStatus.CANCELLED.value
        session.end_time = datetime.now(timezone.utc)
        await session.save(update_fields=["status", "end_time"])

    @staticmethod
    async def get_session_data(session_id: int, user_id: int, t: dict) -> Dict[str, Any]:
        """
        Retrieve full data (exam, parts, sections, questions) for a given session.
        """
        session = (
            await UserListeningSession.get_or_none(id=session_id, user_id=user_id)
            .prefetch_related("exam__parts__sections__questions")
        )
        if not session:
            logger.warning(f"Listening session not found or unauthorized (session_id={session_id}, user_id={user_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_session_not_found"]
            )

        exam = session.exam

        parts_data = []
        for part in sorted(exam.parts, key=lambda p: p.part_number):
            sections_data = []
            for section in sorted(part.sections, key=lambda s: s.section_number):
                questions_data = []
                for q in sorted(section.questions, key=lambda q: q.index):
                    questions_data.append({
                        "id": q.id,
                        "section_id": q.section_id,
                        "index": q.index,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "created_at": q.created_at,
                        "updated_at": q.updated_at,
                    })
                sections_data.append({
                    "id": section.id,
                    "part_id": section.part_id,
                    "section_number": section.section_number,
                    "start_index": section.start_index,
                    "end_index": section.end_index,
                    "question_type": section.question_type,
                    "question_text": section.question_text,
                    "options": section.options,
                    "questions": questions_data,
                    "created_at": section.created_at,
                    "updated_at": section.updated_at,
                })
            parts_data.append({
                "id": part.id,
                "listening_id": part.listening_id,
                "part_number": part.part_number,
                "audio_file": part.audio_file,
                "sections": sections_data,
                "created_at": part.created_at,
                "updated_at": part.updated_at,
            })

        logger.info(f"Retrieved session data for session_id={session_id}")
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
                "created_at": exam.created_at,
                "updated_at": exam.updated_at,
            },
            "parts": parts_data,
        }

    @staticmethod
    async def submit_answers(
        session_id: int, user_id: int, payload: Dict[str,Any], t: Dict[str,str]
    ) -> int:   
        """
        payload = {"test_id": int, "answers": { section_id: [ { "question_id": int, "answer": str|list } ] } }
        """
        test_id = payload.get("test_id")
        answers_dict = payload.get("answers")
        if test_id is None or answers_dict is None:
            raise HTTPException(422, detail=t["invalid_payload"])

        session = await UserListeningSession.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(404, detail=t["session_not_found"])
        if session.status == ListeningSessionStatus.COMPLETED.value:
            raise HTTPException(400, detail=t["session_already_completed"])

        exam = await Listening.get_or_none(id=session.exam_id).prefetch_related("parts")
        if not exam or not exam.parts or len(exam.parts) == 0:
            raise HTTPException(
                status_code=400,
                detail=t.get("no_listening_parts", "No parts found for this listening test")
            )

        # clear old
        await UserResponse.filter(session_id=session_id, user_id=user_id).delete()

        total_correct = 0
        # iterate answers
        for sec_key, ans_list in answers_dict.items():
            try:
                section_id = int(sec_key)
            except:
                raise HTTPException(422, detail=t["invalid_section_key"])

            for ans in ans_list:
                q = await ListeningQuestion.get_or_none(
                    id=ans["question_id"], section_id=section_id
                )
                if not q:
                    raise HTTPException(404, detail=t["question_not_found"])

                user_ans = ans["answer"]
                # normalize to list of strings
                if not isinstance(user_ans, list):
                    user_ans = [user_ans]
                correct_set = set(map(str, q.correct_answer))
                user_set = set(map(str, user_ans))
                is_correct = (correct_set == user_set)
                if is_correct:
                    total_correct += 1

                await UserResponse.create(
                    session_id=session_id,
                    user_id=user_id,
                    question_id=q.id,
                    user_answer=user_ans,
                    is_correct=is_correct,
                    score=1 if is_correct else 0,
                )

        # finish session
        session.status = ListeningSessionStatus.COMPLETED.value
        session.end_time = datetime.now(timezone.utc)
        await session.save(update_fields=["status", "end_time"])

        # kick off async analysis task (feedback only)
        from tasks.analyses.listening_tasks import analyse_listening_task
        analyse_listening_task.delay(session_id)

        return total_correct

    @staticmethod
    async def get_analysis(session_id: int, user_id: int, t: Dict[str, str]) -> Dict[str, Any]:
        from services.analyses.listening_analyse_service import ListeningAnalyseService

        session = await UserListeningSession.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(404, detail=t["session_not_found"])

        analyse = await ListeningAnalyseService.get_analysis(session_id)

        responses = await UserResponse.filter(
            session_id=session_id, user_id=user_id
        ).prefetch_related("question").all()

        resp_list = []
        for r in responses:
            resp_list.append({
                "id": r.id,
                "user_answer": r.user_answer,
                "is_correct": r.is_correct,
                "score": r.score,
                "correct_answer": r.question.correct_answer if r.question else None,
                "question_index": r.question.index if r.question else None,
            })

        return {
            "session_id": session_id,
            "analyse": analyse["analyse"],
            "responses": resp_list,
        }

    @staticmethod
    async def _get_session(session_id: int, user_id: int, t: dict) -> UserListeningSession:
        """
        Helper: retrieve a UserListeningSession and verify ownership.
        Raise 404 if not found or not owned by user.
        """
        session = await UserListeningSession.get_or_none(id=session_id)
        if not session or session.user_id != user_id:
            logger.warning(f"Session not found or unauthorized (session_id={session_id}, user_id={user_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["listening_session_not_found"]
            )
        return session
