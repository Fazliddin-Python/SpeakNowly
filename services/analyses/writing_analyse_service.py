from datetime import datetime, timezone
from fastapi import HTTPException, status
from models.analyses import WritingAnalyse
from models.tests.writing import Writing, WritingStatus, WritingPart1, WritingPart2
from services.chatgpt.writing_integration import ChatGPTWritingIntegration

class WritingAnalyseService:
    @staticmethod
    async def analyse(test_id: int) -> WritingAnalyse:
        """
        Analyse a completed Writing test and save the result.
        """
        test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
        if not test:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Writing test not found")
        
        if test.status != WritingStatus.COMPLETED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Writing test is not completed")
        
        existing = await WritingAnalyse.get_or_none(writing_id=test.id)
        if existing:
            return existing
        
        if not test.part1 or not test.part2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Test parts are missing")
        
        chatgpt = ChatGPTWritingIntegration()
        analysis = await chatgpt.analyse_writing(test.part1, test.part2, lang_code="en")
        if not analysis:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to analyse writing test")
        
        duration = (test.end_time - test.start_time) if (test.start_time and test.end_time) else None

        writing_analyse = await WritingAnalyse.create(
            writing=test,
            task_achievement_feedback=analysis.get("task1", {}).get("task_achievement", {}).get("feedback"),
            task_achievement_score=analysis.get("task1", {}).get("task_achievement", {}).get("score"),
            lexical_resource_feedback=analysis.get("task1", {}).get("lexical_resource", {}).get("feedback"),
            lexical_resource_score=analysis.get("task1", {}).get("lexical_resource", {}).get("score"),
            coherence_and_cohesion_feedback=analysis.get("task1", {}).get("coherence_and_cohesion", {}).get("feedback"),
            coherence_and_cohesion_score=analysis.get("task1", {}).get("coherence_and_cohesion", {}).get("score"),
            grammatical_range_and_accuracy_feedback=analysis.get("task1", {}).get("grammatical_range_and_accuracy", {}).get("feedback"),
            grammatical_range_and_accuracy_score=analysis.get("task1", {}).get("grammatical_range_and_accuracy", {}).get("score"),
            word_count_feedback=analysis.get("task1", {}).get("word_count", {}).get("feedback"),
            word_count_score=analysis.get("task1", {}).get("word_count", {}).get("score"),
            overall_band_score=analysis.get("overall_band_score"),
            total_feedback=analysis.get("task2", {}).get("task_response", {}).get("feedback"),
            duration=duration,
        )
        
        return writing_analyse