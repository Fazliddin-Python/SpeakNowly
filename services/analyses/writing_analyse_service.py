from models.analyses import WritingAnalyse
from models.tests.writing import Writing
from services.chatgpt.integration import ChatGPTIntegration

class WritingAnalyseService:
    @staticmethod
    async def analyse(test_id: int, api_key: str) -> WritingAnalyse:
        """
        Analyse a Writing test using ChatGPT and save the result.
        """
        test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
        if not test:
            raise ValueError("Writing test not found")
        if test.status != "completed":
            raise ValueError("Test must be completed before analysis")
        if not test.part1 or not test.part2:
            raise ValueError("Test parts are missing")

        chatgpt = ChatGPTIntegration(api_key)
        analysis = await chatgpt.analyse_writing(test.part1.answer, test.part2.answer)

        # Пример обработки ответа от ChatGPT (ожидается dict)
        analysis_data = {
            "task_achievement_feedback": analysis.get("Task Achievement", {}).get("feedback"),
            "task_achievement_score": analysis.get("Task Achievement", {}).get("score"),
            "lexical_resource_feedback": analysis.get("Lexical Resource", {}).get("feedback"),
            "lexical_resource_score": analysis.get("Lexical Resource", {}).get("score"),
            "coherence_and_cohesion_feedback": analysis.get("Coherence and Cohesion", {}).get("feedback"),
            "coherence_and_cohesion_score": analysis.get("Coherence and Cohesion", {}).get("score"),
            "grammatical_range_and_accuracy_feedback": analysis.get("Grammatical Range and Accuracy", {}).get("feedback"),
            "grammatical_range_and_accuracy_score": analysis.get("Grammatical Range and Accuracy", {}).get("score"),
            "word_count_feedback": analysis.get("Word Count", {}).get("feedback"),
            "word_count_score": analysis.get("Word Count", {}).get("score"),
            "overall_band_score": analysis.get("Overall Band Score"),
            "total_feedback": analysis.get("Total Feedback"),
        }

        writing_analyse = await WritingAnalyse.create(
            writing=test,
            **analysis_data,
        )
        return writing_analyse