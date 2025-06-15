from datetime import timedelta
from fastapi import HTTPException, status
from typing import Optional
from tortoise.transactions import in_transaction
from models.analyses import SpeakingAnalyse
from models.tests import Speaking, SpeakingAnswer, SpeakingStatus
from services.chatgpt.speaking_integration import ChatGPTSpeakingIntegration

class SpeakingAnalyseService:
    @staticmethod
    async def analyse(test_id: int) -> SpeakingAnalyse:
        test = await Speaking.get_or_none(id=test_id)
        if not test:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Speaking test not found")
        
        if test.status != SpeakingStatus.COMPLETED.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Speaking test is not completed")
        
        existing = await SpeakingAnalyse.get_or_none(speaking_id=test.id)
        if existing:
            return existing
        
        answers = await SpeakingAnswer.filter(question__speaking_id=test_id).order_by("question__part").all()
        if len(answers) < 3:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not all answers found for this test")
        
        part1, part2, part3 = answers[0], answers[1], answers[2]
        
        chatgpt = ChatGPTSpeakingIntegration()
        analysis = await chatgpt.generate_ielts_speaking_analyse(part1, part2, part3)
        if not analysis:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to analyse speaking test")
        
        duration = (test.end_time - test.start_time) if (test.start_time and test.end_time) else None
        
        speaking_analyse = await SpeakingAnalyse.create(
            speaking_id=test.id,
            feedback=analysis.get("feedback"),
            overall_band_score=analysis.get("overall_band_score"),
            fluency_and_coherence_score=analysis.get("fluency_and_coherence_score"),
            fluency_and_coherence_feedback=analysis.get("fluency_and_coherence_feedback"),
            lexical_resource_score=analysis.get("lexical_resource_score"),
            lexical_resource_feedback=analysis.get("lexical_resource_feedback"),
            grammatical_range_and_accuracy_score=analysis.get("grammatical_range_and_accuracy_score"),
            grammatical_range_and_accuracy_feedback=analysis.get("grammatical_range_and_accuracy_feedback"),
            pronunciation_score=analysis.get("pronunciation_score"),
            pronunciation_feedback=analysis.get("pronunciation_feedback"),
            duration=duration,
        )
        
        return speaking_analyse