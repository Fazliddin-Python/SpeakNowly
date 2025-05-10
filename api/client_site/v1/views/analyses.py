from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from tortoise.exceptions import DoesNotExist

from models.analyses import (
    ListeningAnalyse,
    ReadingAnalyse,
    SpeakingAnalyse,
    WritingAnalyse,
)
from models.tests.writing import Writing, WritingPart1, WritingPart2
from models.tests.speaking import Speaking, SpeakingAnswers
from services.chatgpt.integration import ChatGPTIntegration
from ..serializers.analyses import (
    ListeningAnalyseSerializer,
    ReadingAnalyseSerializer,
    SpeakingAnalyseSerializer,
    WritingAnalyseSerializer,
)

router = APIRouter()


@router.get("/listening/{session_id}/analyse/", response_model=ListeningAnalyseSerializer)
async def analyse_listening(session_id: int):
    """
    Analyse a listening test session.
    """
    try:
        analysis = await ListeningAnalyse.get(session_id=session_id)
        return analysis
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Listening analysis not found")


@router.get("/reading/analysis/", response_model=List[ReadingAnalyseSerializer])
async def analyse_reading(user_id: int):
    """
    Analyse all reading tests for a user.
    """
    analyses = await ReadingAnalyse.filter(user_id=user_id).all()
    if not analyses:
        raise HTTPException(status_code=404, detail="No reading analyses found for the user")
    return analyses


@router.get("/speaking/{id}/analyse/", response_model=SpeakingAnalyseSerializer)
async def analyse_speaking(id: int):
    """
    Analyse a speaking test.
    """
    try:
        analysis = await SpeakingAnalyse.get(id=id)
        return analysis
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Speaking analysis not found")


@router.get("/writing/{id}/analyse/", response_model=WritingAnalyseSerializer)
async def analyse_writing(id: int):
    """
    Analyse a writing test.
    """
    try:
        analysis = await WritingAnalyse.get(id=id)
        return analysis
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Writing analysis not found")

# Do not really need this, but keeping for reference:
@router.post("/writing/{test_id}/analyse/", status_code=status.HTTP_201_CREATED)
async def analyse_writing_test(
    test_id: int,
    api_key: str = Depends(lambda: "your-chatgpt-api-key"),
):
    """
    Analyzes a Writing test using the ChatGPT API.
    """
    test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
    if not test:
        raise HTTPException(status_code=404, detail="Writing test not found")

    if test.status != "completed":
        raise HTTPException(status_code=400, detail="Test must be completed before analysis")

    if not test.part1 or not test.part2:
        raise HTTPException(status_code=400, detail="Test parts are missing")

    chatgpt = ChatGPTIntegration(api_key)
    analysis = await chatgpt.analyse_writing(test.part1.answer, test.part2.answer)

    # Пример обработки ответа от ChatGPT
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

    return {"message": "Analysis completed successfully", "analysis": analysis_data}


@router.post("/speaking/{test_id}/analyse/", status_code=status.HTTP_201_CREATED)
async def analyse_speaking_test(
    test_id: int,
    api_key: str = Depends(lambda: "your-chatgpt-api-key"),
):
    """
    Анализирует Speaking тест с использованием ChatGPT API.
    """
    test = await Speaking.get_or_none(id=test_id).prefetch_related("questions__answer")
    if not test:
        raise HTTPException(status_code=404, detail="Speaking test not found")

    if test.status != "completed":
        raise HTTPException(status_code=400, detail="Test must be completed before analysis")

    answers = await SpeakingAnswers.filter(question__speaking_id=test_id).all()
    if not answers:
        raise HTTPException(status_code=400, detail="No answers found for this test")

    # Формируем данные для анализа
    part1_answer = answers[0].text_answer if len(answers) > 0 else None
    part2_answer = answers[1].text_answer if len(answers) > 1 else None
    part3_answer = answers[2].text_answer if len(answers) > 2 else None

    chatgpt = ChatGPTIntegration(api_key)
    analysis = await chatgpt.analyse_speaking(part1_answer, part2_answer, part3_answer)

    # Пример обработки ответа от ChatGPT
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
        "duration": test.end_time - test.start_time if test.end_time and test.start_time else None,
    }

    speaking_analyse = await SpeakingAnalyse.create(
        speaking=test,
        **analysis_data,
    )

    return {"message": "Analysis completed successfully", "analysis": analysis_data}