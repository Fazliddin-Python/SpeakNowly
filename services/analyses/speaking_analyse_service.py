from fastapi import HTTPException, status
from datetime import timedelta
from services.chatgpt import ChatGPTSpeakingIntegration
from models.analyses import SpeakingAnalyse
from models.tests.speaking import SpeakingSession, SpeakingAnswer, SpeakingStatus, SpeakingQuestion
from api.client_site.v1.serializers.tests.speaking import SpeakingAnalysisResponseSerializer

class SpeakingAnalyseService:
    @staticmethod
    async def analyse(session_id: int) -> dict:
        session = await SpeakingSession.get_or_none(id=session_id).prefetch_related("test", "answers__question")
        if not session:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Speaking session not found")
        if session.status != SpeakingStatus.COMPLETED.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Speaking session is not completed")

        # Собираем только заполненные ответы
        answers = await SpeakingAnswer.filter(session=session).select_related("question").order_by("question__part")
        parts = []
        for ans in answers:
            if ans.text_answer and ans.text_answer.strip():
                parts.append({
                    "part": ans.question.part,
                    "title": ans.question.title,
                    "question": ans.question.content,
                    "user_answer": ans.text_answer,
                })

        if not parts:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No answers provided for analysis.")

        chatgpt = ChatGPTSpeakingIntegration()
        analysis = await chatgpt.generate_ielts_speaking_analyse(parts)

        duration = (session.end_time - session.start_time) if (session.start_time and session.end_time) else timedelta(0)

        # Сохраняем анализ для каждого part из analysis["analysis"]
        analyse_list = []
        for part_result in analysis.get("analysis", []):
            idx = part_result.get("part")
            if not idx:
                continue
            analyse_obj = await SpeakingAnalyse.create(
                speaking=session,
                part=idx,
                fluency_and_coherence_score=part_result.get("fluency_and_coherence_score"),
                fluency_and_coherence_feedback=part_result.get("fluency_and_coherence_feedback"),
                lexical_resource_score=part_result.get("lexical_resource_score"),
                lexical_resource_feedback=part_result.get("lexical_resource_feedback"),
                grammatical_range_and_accuracy_score=part_result.get("grammatical_range_and_accuracy_score"),
                grammatical_range_and_accuracy_feedback=part_result.get("grammatical_range_and_accuracy_feedback"),
                pronunciation_score=part_result.get("pronunciation_score"),
                pronunciation_feedback=part_result.get("pronunciation_feedback"),
                duration=duration,
            )
            analyse_list.append(analyse_obj)

        return await SpeakingAnalysisResponseSerializer.from_orm_async(
            analyse_list,
            analysis.get("overall_band_score"),
            analysis.get("feedback")
        )