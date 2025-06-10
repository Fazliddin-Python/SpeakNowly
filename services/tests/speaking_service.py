from models.tests.speaking import Speaking, SpeakingQuestions, SpeakingAnswers
from fastapi import HTTPException, UploadFile
from datetime import datetime, timezone
from typing import List, Optional
from services.analyses.speaking_analyse_service import SpeakingAnalyseService

class SpeakingService:
    @staticmethod
    async def get_speaking_tests(user_id: int):
        tests = await Speaking.filter(user_id=user_id).all()
        if not tests:
            raise HTTPException(status_code=404, detail="No speaking tests found for the user")
        return tests

    @staticmethod
    async def get_speaking_test(test_id: int):
        test = await Speaking.get_or_none(id=test_id).prefetch_related("questions")
        if not test:
            raise HTTPException(status_code=404, detail="Speaking test not found")
        return test

    @staticmethod
    async def create_speaking_test(user_id: int, start_time: Optional[datetime] = None):
        return await Speaking.create(
            user_id=user_id,
            start_time=start_time or datetime.now(timezone.utc),
            status="started",
        )

    @staticmethod
    async def submit_speaking_answer(
        test_id: int,
        question_id: int,
        audio_answer: Optional[UploadFile],
        text_answer: Optional[str]
    ):
        test = await Speaking.get_or_none(id=test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Speaking test not found")
        question = await SpeakingQuestions.get_or_none(id=question_id, speaking_id=test_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found for this test")
        audio_path = None
        if audio_answer:
            audio_path = f"audio_responses/{audio_answer.filename}"
            with open(audio_path, "wb") as f:
                f.write(await audio_answer.read())
            # Если нужно транскрибировать аудио, реализуй функцию в integration.py:
            # from services.chatgpt.integration import transcribe_audio
            # text_answer = await transcribe_audio(audio_path)
            # Пока просто сохраняем путь к аудио, а text_answer не меняем
        await SpeakingAnswers.create(
            question_id=question_id,
            text_answer=text_answer,
            audio_answer=audio_path,
        )
        return {"message": "Answer submitted successfully", "text_answer": text_answer}

    @staticmethod
    async def complete_speaking_test(test_id: int):
        test = await Speaking.get_or_none(id=test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Speaking test not found")
        if test.status == "completed":
            raise HTTPException(status_code=400, detail="Test is already completed")
        test.status = "completed"
        test.end_time = datetime.now(timezone.utc)
        await test.save()
        return {"message": "Speaking test completed successfully"}

    @staticmethod
    async def get_speaking_questions(test_id: int):
        questions = await SpeakingQuestions.filter(speaking_id=test_id).all()
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found for this test")
        return questions

    @staticmethod
    async def create_speaking_question(test_id: int, part: str, title: Optional[str], content: str):
        test = await Speaking.get_or_none(id=test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Speaking test not found")
        return await SpeakingQuestions.create(
            speaking_id=test_id,
            part=part,
            title=title,
            content=content,
        )

    @staticmethod
    async def get_speaking_answers(test_id: int):
        answers = await SpeakingAnswers.filter(question__speaking_id=test_id).all()
        if not answers:
            raise HTTPException(status_code=404, detail="No answers found for this test")
        return answers

    @staticmethod
    async def analyse_speaking(test_id: int):
        """
        Run analysis for a speaking test (can be called from Celery or directly).
        """
        return await SpeakingAnalyseService.analyse(test_id)