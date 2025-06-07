import json
from datetime import timedelta
from typing import Optional

from tortoise.transactions import in_transaction
from fastapi import HTTPException

from models.tests.speaking import Speaking, SpeakingAnswers
from models.analyses import SpeakingAnalyse
from services.chatgpt.integration import ChatGPTIntegration


class SpeakingAnalyseService:
    @staticmethod
    async def analyse(test_id: int, api_key: Optional[str]) -> SpeakingAnalyse:
        """
        Perform analysis of a completed Speaking test using ChatGPT and save the result.

        Steps:
        1. Retrieve Speaking with related questions/answers.
        2. Ensure status is "completed".
        3. Fetch three answers ordered by question part.
        4. Call ChatGPTIntegration.analyse_speaking(...) to get JSON.
        5. Parse JSON and extract scores/feedback.
        6. Compute duration and save SpeakingAnalyse.
        7. Return the SpeakingAnalyse instance.
        """
        # 1) Retrieve the Speaking test with its questions & answers
        test = await Speaking.get_or_none(id=test_id).prefetch_related("questions__answer")
        if not test:
            raise HTTPException(status_code=404, detail="Speaking test not found")

        # 2) Ensure test is completed
        if test.status != "completed":
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

        # 4) Invoke ChatGPT to analyze speaking
        chatgpt = ChatGPTIntegration(api_key)
        raw_json = await chatgpt.analyse_speaking(part1, part2, part3)

        # 5) Parse the JSON
        try:
            analysis_dict = json.loads(raw_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON from GPT")

        try:
            feedback = analysis_dict.get("feedback", "")
            overall = float(analysis_dict.get("overall_band_score", 0))

            flu_coh = analysis_dict.get("fluency_and_coherence", {})
            lex = analysis_dict.get("lexical_resource", {})
            gram = analysis_dict.get("grammatical_range_and_accuracy", {})
            pron = analysis_dict.get("pronunciation", {})

            f_score = float(flu_coh.get("score", 0))
            f_feedback = flu_coh.get("feedback", "")

            l_score = float(lex.get("score", 0))
            l_feedback = lex.get("feedback", "")

            g_score = float(gram.get("score", 0))
            g_feedback = gram.get("feedback", "")

            p_score = float(pron.get("score", 0))
            p_feedback = pron.get("feedback", "")
        except (ValueError, TypeError):
            raise HTTPException(status_code=500, detail="Unexpected analysis format")

        # 6) Compute duration
        if test.start_time and test.end_time:
            duration = test.end_time - test.start_time
        else:
            duration = timedelta()

        # 7) Save SpeakingAnalyse
        async with in_transaction():
            speaking_analyse = await SpeakingAnalyse.create(
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

        return speaking_analyse
