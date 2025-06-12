from datetime import datetime, timezone
from models.analyses import WritingAnalyse
from models.tests.writing import Writing, WritingStatus
from services.chatgpt.integration import ChatGPTIntegration

class WritingAnalyseService:
    @staticmethod
    async def analyse(test_id: int) -> WritingAnalyse:
        """
        Analyse a Writing test using ChatGPT and save the result.
        """
        test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
        if not test:
            raise ValueError("Writing test not found")
        if test.status != WritingStatus.COMPLETED:
            raise ValueError("Test must be completed before analysis")
        if not test.part1 or not test.part2:
            raise ValueError("Test parts are missing")

        chatgpt = ChatGPTIntegration()
        # Используем асинхронный метод анализа!
        analysis = await chatgpt.analyse_writing(
            {
                "diagram_data": test.part1.diagram_data,
                "user_answer": test.part1.answer or ""
            },
            test.part2.answer or "",
            lang_code="en"
        )

        # Пример обработки ответа от ChatGPT (ожидается dict)
        analysis_data = {
            "task_achievement_feedback": analysis.get("task1", {}).get("task_achievement", {}).get("feedback"),
            "task_achievement_score": analysis.get("task1", {}).get("task_achievement", {}).get("score"),
            "lexical_resource_feedback": analysis.get("task1", {}).get("lexical_resource", {}).get("feedback"),
            "lexical_resource_score": analysis.get("task1", {}).get("lexical_resource", {}).get("score"),
            "coherence_and_cohesion_feedback": analysis.get("task1", {}).get("coherence_and_cohesion", {}).get("feedback"),
            "coherence_and_cohesion_score": analysis.get("task1", {}).get("coherence_and_cohesion", {}).get("score"),
            "grammatical_range_and_accuracy_feedback": analysis.get("task1", {}).get("grammatical_range_and_accuracy", {}).get("feedback"),
            "grammatical_range_and_accuracy_score": analysis.get("task1", {}).get("grammatical_range_and_accuracy", {}).get("score"),
            "word_count_feedback": analysis.get("task1", {}).get("word_count", {}).get("feedback"),
            "word_count_score": analysis.get("task1", {}).get("word_count", {}).get("score"),
            "overall_band_score": analysis.get("overall_band_score"),
            "total_feedback": analysis.get("task2", {}).get("task_response", {}).get("feedback"),
        }

        # Обновить статус и время
        test.status = WritingStatus.COMPLETED
        test.end_time = datetime.now(timezone.utc)
        await test.save()

        writing_analyse = await WritingAnalyse.create(
            writing=test,
            **analysis_data,
        )
        return writing_analyse