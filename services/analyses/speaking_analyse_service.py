from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from datetime import timedelta
from services.chatgpt import ChatGPTSpeakingIntegration
from models.analyses import SpeakingAnalyse
from models.tests import Speaking, SpeakingAnswer, SpeakingStatus

def analyse_to_dict(analyse: SpeakingAnalyse) -> dict:
    return {
        "feedback": analyse.feedback,
        "overall_band_score": float(analyse.overall_band_score) if analyse.overall_band_score is not None else None,
        "fluency_and_coherence_score": float(analyse.fluency_and_coherence_score) if analyse.fluency_and_coherence_score is not None else None,
        "fluency_and_coherence_feedback": analyse.fluency_and_coherence_feedback,
        "lexical_resource_score": float(analyse.lexical_resource_score) if analyse.lexical_resource_score is not None else None,
        "lexical_resource_feedback": analyse.lexical_resource_feedback,
        "grammatical_range_and_accuracy_score": float(analyse.grammatical_range_and_accuracy_score) if analyse.grammatical_range_and_accuracy_score is not None else None,
        "grammatical_range_and_accuracy_feedback": analyse.grammatical_range_and_accuracy_feedback,
        "pronunciation_score": float(analyse.pronunciation_score) if analyse.pronunciation_score is not None else None,
        "pronunciation_feedback": analyse.pronunciation_feedback,
        "timing": analyse.duration.total_seconds() if analyse.duration else None,
    }

class SpeakingAnalyseService:
    @staticmethod
    async def analyse(test_id: int) -> dict:
        t = {
            "no_answer_feedback": "No answer",
            "not_all_audio_uploaded": "Not all audio uploaded"
        }
        test = await Speaking.get_or_none(id=test_id)
        if not test:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Speaking test not found")
        if test.status != SpeakingStatus.COMPLETED.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Speaking test is not completed")
        existing = await SpeakingAnalyse.get_or_none(speaking_id=test.id)
        if existing:
            return analyse_to_dict(existing)

        answers = await SpeakingAnswer.filter(question__speaking_id=test_id).order_by("question__part").prefetch_related("question")
        # Always prepare part1, part2, part3 (use fake if missing)
        fake_answer = type("FakeAnswer", (), {"question": type("Q", (), {"title": "", "content": ""})(), "text_answer": ""})
        part1 = answers[0] if len(answers) > 0 else fake_answer
        part2 = answers[1] if len(answers) > 1 else fake_answer
        part3 = answers[2] if len(answers) > 2 else fake_answer

        chatgpt = ChatGPTSpeakingIntegration()
        analysis = await chatgpt.generate_ielts_speaking_analyse(part1, part2, part3)

        # Add 0 and feedback for missing parts
        if len(answers) < 3:
            if len(answers) < 1:
                analysis["part1_score"] = 0
                analysis["part1_feedback"] = t["no_answer_feedback"]
            if len(answers) < 2:
                analysis["part2_score"] = 0
                analysis["part2_feedback"] = t["no_answer_feedback"]
            if len(answers) < 3:
                analysis["part3_score"] = 0
                analysis["part3_feedback"] = t["no_answer_feedback"]

        duration = (test.end_time - test.start_time).total_seconds() if (test.start_time and test.end_time) else None
        analysis["timing"] = duration
        return analysis

    @staticmethod
    async def analyse_partial(test_id: int, answers: dict, t: dict) -> dict:
        parts = ["part1", "part2", "part3"]
        answer_objs = []
        for part in parts:
            answer_objs.append(answers.get(part))

        chatgpt = ChatGPTSpeakingIntegration()

        if not any(answer_objs):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, t["not_all_audio_uploaded"])

        fake_answer = type("FakeAnswer", (), {"question": type("Q", (), {"title": "", "content": ""})(), "text_answer": ""})
        part1 = answer_objs[0] or fake_answer
        part2 = answer_objs[1] or fake_answer
        part3 = answer_objs[2] or fake_answer

        analysis = await chatgpt.generate_ielts_speaking_analyse(part1, part2, part3)

        for idx, part in enumerate(parts, 1):
            if not answer_objs[idx-1]:
                analysis[f"{part}_score"] = 0
                analysis[f"{part}_feedback"] = t.get("no_answer_feedback", "")

        # duration
        test = await Speaking.get(id=test_id)
        duration = (test.end_time - test.start_time).total_seconds() if (test.start_time and test.end_time) else None
        analysis["timing"] = duration
        return analysis