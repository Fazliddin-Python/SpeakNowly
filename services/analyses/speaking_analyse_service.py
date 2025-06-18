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

        # For missing parts, set 0 and feedback
        if not getattr(part1, "text_answer", None):
            analysis["part1_score"] = 0
            analysis["part1_feedback"] = t["no_answer_feedback"]
        if not getattr(part2, "text_answer", None):
            analysis["part2_score"] = 0
            analysis["part2_feedback"] = t["no_answer_feedback"]
        if not getattr(part3, "text_answer", None):
            analysis["part3_score"] = 0
            analysis["part3_feedback"] = t["no_answer_feedback"]

        # Calculate overall_band_score as average of all three (including zeros)
        scores = [
            analysis.get("part1_score", 0),
            analysis.get("part2_score", 0),
            analysis.get("part3_score", 0),
        ]
        analysis["overall_band_score"] = round(sum(scores) / 3, 1)

        duration = (test.end_time - test.start_time).total_seconds() if (test.start_time and test.end_time) else None
        analysis["timing"] = duration

        # Save analysis to DB if not exists
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
            duration=timedelta(seconds=analysis["timing"]) if analysis["timing"] is not None else None,
        )

        return analyse_to_dict(speaking_analyse)