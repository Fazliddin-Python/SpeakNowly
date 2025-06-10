import json
from datetime import timedelta
from typing import Optional

from tortoise.transactions import in_transaction
from fastapi import HTTPException

from models.tests.speaking import Speaking, SpeakingAnswers
from models.analyses import SpeakingAnalyse
from services.chatgpt.integration import ChatGPTIntegration
from models.tests.speaking import SpeakingStatus


class SpeakingAnalyseService:
    @staticmethod
    async def analyse(test_id: int) -> Optional[SpeakingAnalyse]:
        """
        Perform analysis of a completed Speaking test using ChatGPT and save the result.

        Steps:
        1. Retrieve Speaking and its answers.
        2. Ensure status is COMPLETED.
        3. Fetch three answers ordered by question.part.
        4. Call ChatGPTIntegration.analyse_speaking(...) to get a dict.
        5. Extract scores/feedback from the dict.
        6. Compute duration and save (or update) SpeakingAnalyse.
        7. Return the SpeakingAnalyse instance.
        """
        # 1) Retrieve the Speaking test
        test = await Speaking.get_or_none(id=test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Speaking test not found")

        # 2) Ensure test is completed
        if test.status != SpeakingStatus.COMPLETED.value:
            raise HTTPException(status_code=400, detail="Test must be completed before analysis")

        # 3) Fetch exactly three SpeakingAnswers, ordered by question.part
        answers = (
            await SpeakingAnswers
            .filter(question__speaking_id=test_id)
            .order_by("question__part")
            .all()
        )
        if len(answers) < 3:
            raise HTTPException(status_code=400, detail="Not all answers found for this test")

        part1 = answers[0].text_answer or ""
        part2 = answers[1].text_answer or ""
        part3 = answers[2].text_answer or ""

        # 4) Invoke ChatGPT to analyze speaking (returns dict)
        chatgpt = ChatGPTIntegration()
        analysis_dict = await chatgpt.analyse_speaking(part1, part2, part3)

        # 5) Extract scores & feedback
        try:
            feedback = analysis_dict["feedback"]
            overall = float(analysis_dict["overall_band_score"])

            f_score = float(analysis_dict["fluency_and_coherence_score"])
            f_feedback = analysis_dict["fluency_and_coherence_feedback"]

            l_score = float(analysis_dict["lexical_resource_score"])
            l_feedback = analysis_dict["lexical_resource_feedback"]

            g_score = float(analysis_dict["grammatical_range_and_accuracy_score"])
            g_feedback = analysis_dict["grammatical_range_and_accuracy_feedback"]

            p_score = float(analysis_dict["pronunciation_score"])
            p_feedback = analysis_dict["pronunciation_feedback"]
        except (KeyError, TypeError, ValueError):
            raise HTTPException(status_code=500, detail="Unexpected analysis format")

        # 6) Compute duration
        if test.start_time and test.end_time:
            duration = test.end_time - test.start_time
        else:
            duration = timedelta()

        # 7) Save or update SpeakingAnalyse
        async with in_transaction():
            existing = await SpeakingAnalyse.get_or_none(speaking_id=test.id)
            if existing:
                # update fields
                existing.feedback = feedback
                existing.overall_band_score = overall
                existing.fluency_and_coherence_score = f_score
                existing.fluency_and_coherence_feedback = f_feedback
                existing.lexical_resource_score = l_score
                existing.lexical_resource_feedback = l_feedback
                existing.grammatical_range_and_accuracy_score = g_score
                existing.grammatical_range_and_accuracy_feedback = g_feedback
                existing.pronunciation_score = p_score
                existing.pronunciation_feedback = p_feedback
                existing.duration = duration
                await existing.save()
                return existing
            else:
                return await SpeakingAnalyse.create(
                    speaking_id=test.id,
                    feedback=feedback,
                    overall_band_score=overall,
                    fluency_and_coherence_score=f_score,
                    fluency_and_coherence_feedback=f_feedback,
                    lexical_resource_score=l_score,
                    lexical_resource_feedback=l_feedback,
                    grammatical_range_and_accuracy_score=g_score,
                    grammatical_range_and_accuracy_feedback=g_feedback,
                    pronunciation_score=p_score,
                    pronunciation_feedback=p_feedback,
                    duration=duration,
                )
