import logging
from models.analyses import ListeningAnalyse
from models.tests.listening import UserListeningSession, UserResponse
from datetime import timedelta

logger = logging.getLogger(__name__)

class ListeningAnalyseService:
    @staticmethod
    async def analyse_session(session_id: int) -> ListeningAnalyse:
        """
        Analyse a listening session: calculate correct answers, score, timing.
        """
        session = await UserListeningSession.get_or_none(id=session_id)
        if not session or session.status != "completed":
            logger.warning("Session %s not found or not completed", session_id)
            raise ValueError("Session not found or not completed")
        user = session.user
        responses = await UserResponse.filter(session_id=session_id)
        correct = sum(1 for r in responses if r.is_correct)
        total = len(responses)
        score = round((correct / total) * 9, 1) if total else 0.0
        timing = session.end_time - session.start_time if session.end_time and session.start_time else timedelta()
        analyse, created = await ListeningAnalyse.get_or_create(
            session=session,
            defaults={
                "user": user,
                "correct_answers": correct,
                "overall_score": score,
                "timing": timing,
            }
        )
        if not created:
            analyse.correct_answers = correct
            analyse.overall_score = score
            analyse.timing = timing
            await analyse.save()
        logger.info("Listening analysis for session %s completed", session_id)
        return analyse