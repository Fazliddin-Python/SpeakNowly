from models.analyses import SpeakingAnalyse
from models.tests.speaking import Speaking, SpeakingAnswers
from services.chatgpt.integration import ChatGPTIntegration
from datetime import timedelta

class SpeakingAnalyseService:
    @staticmethod
    async def analyse(test_id: int, api_key: str) -> SpeakingAnalyse:
        """
        Analyse a Speaking test using ChatGPT and save the result.
        """
        test = await Speaking.get_or_none(id=test_id).prefetch_related("questions__answer")
        if not test:
            raise ValueError("Speaking test not found")
        if test.status != "completed":
            raise ValueError("Test must be completed before analysis")

        answers = await SpeakingAnswers.filter(question__speaking_id=test_id).order_by("question__part").all()
        if not answers or len(answers) < 3:
            raise ValueError("Not all answers found for this test")

        part1 = answers[0].text_answer if len(answers) > 0 else ""
        part2 = answers[1].text_answer if len(answers) > 1 else ""
        part3 = answers[2].text_answer if len(answers) > 2 else ""

        chatgpt = ChatGPTIntegration(api_key)
        analysis = await chatgpt.analyse_speaking(part1, part2, part3)

        # Пример обработки ответа от ChatGPT (ожидается dict)
        analysis_data = {
            "feedback": analysis.get("feedback"),
            "overall_band_score": analysis.get("overall_band_score"),
            "fluency_and_coherence_score": analysis.get("fluency_and_coherence", {}).get("score"),
            "fluency_and_coherence_feedback": analysis.get("fluency_and_coherence", {}).get("feedback"),
            "lexical_resource_score": analysis.get("lexical_resource", {}).get("score"),
            "lexical_resource_feedback": analysis.get("lexical_resource", {}).get("feedback"),
            "grammatical_range_and_accuracy_score": analysis.get("grammatical_range_and_accuracy", {}).get("score"),
            "grammatical_range_and_accuracy_feedback": analysis.get("grammatical_range_and_accuracy", {}).get("feedback"),
            "pronunciation_score": analysis.get("pronunciation", {}).get("score"),
            "pronunciation_feedback": analysis.get("pronunciation", {}).get("feedback"),
            "duration": (test.end_time - test.start_time) if test.end_time and test.start_time else timedelta(),
        }

        speaking_analyse = await SpeakingAnalyse.create(
            speaking=test,
            **analysis_data,
        )
        return speaking_analyse