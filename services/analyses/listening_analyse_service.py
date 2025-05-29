import logging
import json
from datetime import timedelta
from tortoise.exceptions import DoesNotExist

from models.analyses import ListeningAnalyse
from models.tests.listening import UserListeningSession, UserResponse
from services.chatgpt.integration import ChatGPTIntegration

logger = logging.getLogger(__name__)

class ListeningAnalyseService:
    """Service to perform analysis on completed listening sessions via ChatGPT."""

    @staticmethod
    async def analyse(session_id: int) -> ListeningAnalyse:
        """
        Fetch a completed session, gather user responses, send to ChatGPT for
        quantitative scoring and qualitative feedback, then persist results.
        """
        # Load session
        try:
            session = await UserListeningSession.get(id=session_id)
        except DoesNotExist:
            logger.error(f"Session {session_id} not found.")
            raise

        if session.status != "completed":
            msg = f"Session {session_id} not completed: status={session.status}"
            logger.error(msg)
            raise ValueError(msg)

        # Collect ordered answers
        responses = await UserResponse.filter(session_id=session_id).order_by("question_id")
        answers = [r.user_answer for r in responses]
        duration = (session.end_time - session.start_time) or timedelta()

        # Integrate GPT for scoring and feedback
        chatgpt = ChatGPTIntegration()
        system_msg = (
            "You are an expert IELTS listening examiner. A test taker has completed 40 listening questions. "
            "Your task is to evaluate their answers and return structured feedback **strictly in JSON format**. "
            "Do not include any explanation or text outside the JSON block.\n\n"
            "Use the following format:\n\n"
            "{\n"
            '  "correct_answers": <int: number of correct answers out of 40>,\n'
            '  "overall_score": <float: IELTS band score from 0.0 to 9.0>,\n'
            '  "feedback": {\n'
            '    "listening_skills": "<str: feedback on gist, detail, inference, etc.>",\n'
            '    "concentration": "<str: comment on consistency and focus>",\n'
            '    "strategy_recommendations": "<str: advice on note-taking, predicting, etc.>"\n'
            "}\n"
            "}\n\n"
            "Example:\n"
            "{\n"
            '  "correct_answers": 32,\n'
            '  "overall_score": 7.5,\n'
            '  "feedback": {\n'
            '    "listening_skills": "Generally strong at identifying key ideas, but missed some inferences.",\n'
            '    "concentration": "Slight loss of focus during section 3.",\n'
            '    "strategy_recommendations": "Practice identifying speaker attitudes and using prediction techniques."\n'
            "  }\n"
            "}\n\n"
            "ONLY RETURN VALID JSON WITH NO EXTRA TEXT."
        )
        user_msg = "\n".join(f"Question {i+1}: {ans}" for i, ans in enumerate(answers))
        
        raw = await chatgpt.analyse_listening(system_msg, user_msg)

        try:
            result = json.loads(raw)
            correct_count = int(result["correct_answers"])
            band_score = float(result["overall_score"])
            feedback = result["feedback"]
        except Exception:
            logger.error(f"Invalid GPT response: {raw}")
            raise ValueError("Invalid response from analysis service")

        # Persist or update analysis record
        analyse_obj, created = await ListeningAnalyse.get_or_create(
            session=session,
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
            logger.info(f"Updated analysis for session {session_id}")
        else:
            logger.info(f"Created analysis for session {session_id}")

        return analyse_obj

    @staticmethod
    async def get_analysis(session_id: int):
        from api.client_site.v1.serializers.analyses import ListeningAnalyseSerializer
        analyse = await ListeningAnalyse.get_or_none(session_id=session_id)
        if not analyse:
            return ListeningAnalyseSerializer(
                session_id=session_id,
                user_id=None,
                correct_answers=0,
                overall_score=0.0,
                timing=None,
                status="pending",
                feedback=None
            )
        return ListeningAnalyseSerializer(
            session_id=analyse.session_id,
            user_id=analyse.user_id,
            correct_answers=analyse.correct_answers,
            overall_score=float(analyse.overall_score),
            timing=analyse.timing,
            status=getattr(analyse, "status", "ready")
        )