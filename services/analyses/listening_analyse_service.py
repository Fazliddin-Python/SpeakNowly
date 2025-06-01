import logging
import json
from datetime import timedelta

from fastapi import HTTPException, status
from tortoise.exceptions import DoesNotExist

from models.analyses import ListeningAnalyse
from models.tests.listening import UserListeningSession, UserResponse
from services.chatgpt.integration import ChatGPTIntegration

logger = logging.getLogger(__name__)


class ListeningAnalyseService:
    """
    Service to perform analysis on completed listening sessions via ChatGPT.
    """

    @staticmethod
    async def analyse(session_id: int) -> ListeningAnalyse:
        """
        Run analysis on a completed listening session:
          1. Fetch the session and verify it's completed.
          2. Collect user responses in order.
          3. Send prompt + answers to ChatGPTIntegration for scoring & feedback.
          4. Parse GPT's JSON response.
          5. Persist or update a ListeningAnalyse record.
        """
        # 1. Fetch session, ensure it exists and is completed
        try:
            session = await UserListeningSession.get(id=session_id)
        except DoesNotExist:
            logger.error(f"Listening session not found (id={session_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        if session.status != "completed":
            logger.error(f"Session {session_id} status is '{session.status}', not 'completed'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session not completed"
            )

        # 2. Collect ordered user answers
        responses = await UserResponse.filter(session_id=session_id).order_by("question_id")
        answers = [r.user_answer for r in responses]

        # Compute duration (safely handle missing timestamps)
        if session.start_time and session.end_time:
            duration = session.end_time - session.start_time
        else:
            duration = timedelta()

        # 3. Prepare ChatGPT prompt
        system_msg = (
            "You are an expert IELTS listening examiner. "
            "A test taker has completed up to 40 listening questions. "
            "You only have access to the user's answers (not the audio or questions themselves). "
            "Your tasks:\n"
            "- Count the number of correct answers (assume the answers are in order).\n"
            "- Estimate the IELTS listening band score based on correct answers (0-40).\n"
            "- Provide structured feedback in English on listening skills (strengths, weaknesses, suggestions).\n"
            "- Return ONLY a valid JSON object in this format WITHOUT extra text:\n"
            "{\n"
            '  "correct_answers": <int>,\n'
            '  "overall_score": <float>,\n'
            '  "feedback": {\n'
            '    "listening_skills": "<string>",\n'
            '    "concentration": "<string>",\n'
            '    "strategy_recommendations": "<string>"\n'
            "  }\n"
            "}"
        )
        user_msg = "\n".join(f"Question {i+1}: {ans}" for i, ans in enumerate(answers))

        # 4. Call ChatGPT API
        chatgpt = ChatGPTIntegration()
        raw_response = await chatgpt.analyse_listening(system_msg, user_msg)

        # 5. Parse GPT's JSON response
        try:
            result = json.loads(raw_response)
            correct_count = int(result["correct_answers"])
            band_score = float(result["overall_score"])
            feedback = result["feedback"]
        except Exception as exc:
            logger.error(f"Failed to parse ChatGPT response for session {session_id}: '{raw_response}' – {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from analysis service"
            )

        # 6. Persist or update ListeningAnalyse record
        analyse_obj, created = await ListeningAnalyse.get_or_create(
            session_id=session_id,
            defaults={
                "user_id": session.user_id,
                "correct_answers": correct_count,
                "overall_score": band_score,
                "timing": duration,
                "status": "ready",
                "feedback": feedback,
            }
        )
        if not created:
            analyse_obj.correct_answers = correct_count
            analyse_obj.overall_score = band_score
            analyse_obj.timing = duration
            analyse_obj.status = "ready"
            analyse_obj.feedback = feedback
            await analyse_obj.save()

        logger.info(f"Listening analysis saved for session {session_id} (created={created})")
        return analyse_obj

    @staticmethod
    async def get_analysis(session_id: int) -> dict:
        """
        Retrieve the analysis result for a listening session.
        Returns a dictionary with keys: session_id, analyse (nested dict), responses (empty list).
        """
        analyse = await ListeningAnalyse.get_or_none(session_id=session_id)
        if not analyse:
            # Return an empty-structured response if no analysis exists
            return {
                "session_id": session_id,
                "analyse": {},
                "responses": []
            }

        # Build the nested analyse dictionary
        analyse_data = {
            "correct_answers": analyse.correct_answers,
            "overall_score": float(analyse.overall_score),
            "timing": str(analyse.timing),
            "feedback": analyse.feedback,
        }

        # We don't include individual responses here; that can be fetched separately if needed
        return {
            "session_id": session_id,
            "analyse": analyse_data,
            "responses": []
        }
