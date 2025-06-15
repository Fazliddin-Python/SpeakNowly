import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status, Request, Form

from models import Writing, WritingPart1, WritingPart2, WritingAnalyse, TransactionType
from utils.check_tokens import check_user_tokens
from utils.auth.auth import get_current_user
from utils.i18n import get_translation
from services.chatgpt.integration import ChatGPTIntegration

router = APIRouter()


def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    return user


@router.post("/start/", status_code=status.HTTP_201_CREATED)
async def start_writing_test(
    request: Request,
    user=Depends(active_user),
    t=Depends(get_translation),
):
    # 1. Check tokens
    ok = await check_user_tokens(user, TransactionType.TEST_WRITING, request, t)
    if not ok:
        raise HTTPException(status_code=402, detail=t["insufficient_tokens"])

    # 2. Generate Task1 question + chart data
    chatgpt = ChatGPTIntegration()
    part1 = await chatgpt.generate_writing_part1_question()
    chart_type = part1["chart_type"]

    # 3. Create diagram via ChatGPTIntegration
    if chart_type == "bar":
        diagram_path = await chatgpt.create_bar_chart(
            categories=part1["categories"],
            year1=part1["year1"],
            year2=part1["year2"],
            data_year1=part1["data_year1"],
            data_year2=part1["data_year2"],
        )
    elif chart_type == "line":
        diagram_path = await chatgpt.create_line_chart(
            categories=part1["categories"],
            year1=part1["year1"],
            year2=part1["year2"],
            data_year1=part1["data_year1"],
            data_year2=part1["data_year2"],
        )
    elif chart_type == "pie":
        diagram_path = await chatgpt.create_pie_chart(
            categories=part1["categories"],
            year1=part1["year1"],
            year2=part1["year2"],
            data_year1=part1["data_year1"],
            data_year2=part1["data_year2"],
        )
    else:
        raise HTTPException(status_code=500, detail="Unknown chart type")

    # 4. Generate Task2 question
    part2 = await chatgpt.generate_writing_part2_question()

    # 5. Persist Writing and parts
    now = datetime.now(timezone.utc)
    writing = await Writing.create(user_id=user.id, status="started", start_time=now)
    await WritingPart1.create(
        writing_id=writing.id,
        content=part1["question"],
        diagram=diagram_path,
        diagram_data={
            "categories": part1["categories"],
            "year1": part1["year1"],
            "year2": part1["year2"],
            "data_year1": part1["data_year1"],
            "data_year2": part1["data_year2"],
        },
        answer="",
    )
    await WritingPart2.create(
        writing_id=writing.id,
        content=part2["task2_question"],
        answer="",
    )

    # 6. Return initial test payload
    return {
        "id": writing.id,
        "status": writing.status,
        "start_time": writing.start_time,
        "end_time": writing.end_time,
        "part1": {"content": part1["question"], "diagram": diagram_path},
        "part2": {"content": part2["task2_question"]},
    }


@router.post("/{session_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_writing(
    session_id: int,
    part1: Optional[str] = Form(None),
    part2: Optional[str] = Form(None),
    is_finished: bool = Form(True),
    is_cancelled: bool = Form(False),
    user=Depends(active_user),
    t=Depends(get_translation),
):
    # 1. Fetch and authorize
    writing = await Writing.get_or_none(id=session_id)
    if not writing or writing.user_id != user.id:
        raise HTTPException(status_code=404, detail=t["not_found"])

    # 2. Cancel
    if is_cancelled:
        writing.status = "cancelled"
        await writing.save(update_fields=["status"])
        return {"detail": "cancelled successfully"}

    # 3. Save answers
    p1 = await WritingPart1.get(writing_id=session_id)
    p2 = await WritingPart2.get(writing_id=session_id)
    if part1:
        p1.answer = part1
        await p1.save()
    if part2:
        p2.answer = part2
        await p2.save()

    # 4. Finish
    if is_finished:
        writing.status = "completed"
        writing.end_time = datetime.now(timezone.utc)
        await writing.save(update_fields=["status", "end_time"])
        return {"detail": "answers submitted successfully"}

    return {"detail": "answers saved successfully"}


@router.get("/{session_id}/analyse/", status_code=status.HTTP_200_OK)
async def get_writing_analysis(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation),
):
    # 1. Fetch and authorize
    writing = await Writing.get_or_none(id=session_id)
    if not writing or writing.user_id != user.id:
        raise HTTPException(status_code=404, detail=t["not_found"])
    if writing.status != "completed":
        raise HTTPException(status_code=400, detail="Test must be completed before analysis")

    # 2. Analyse via ChatGPTIntegration
    chatgpt = ChatGPTIntegration()
    part1 = await WritingPart1.get(writing_id=session_id)
    part2 = await WritingPart2.get(writing_id=session_id)
    result = await chatgpt.analyse_writing(
        part1_answer={
            "diagram_data": part1.diagram_data,
            "user_answer": part1.answer,
        },
        part2_answer=part2.answer,
        lang_code=t.get("lang_code", "en"),
    )

    # 3. Persist analysis
    await WritingAnalyse.create(
        writing_id=session_id,
        task_achievement_feedback=result["task1"]["task_achievement"]["feedback"],
        task_achievement_score=result["task1"]["task_achievement"]["score"],
        lexical_resource_feedback=result["task1"]["lexical_resource"]["feedback"],
        lexical_resource_score=result["task1"]["lexical_resource"]["score"],
        coherence_and_cohesion_feedback=result["task1"]["coherence_and_cohesion"]["feedback"],
        coherence_and_cohesion_score=result["task1"]["coherence_and_cohesion"]["score"],
        grammatical_range_and_accuracy_feedback=result["task1"]["grammatical_range_and_accuracy"]["feedback"],
        grammatical_range_and_accuracy_score=result["task1"]["grammatical_range_and_accuracy"]["score"],
        word_count_feedback=result["task1"]["word_count"]["feedback"],
        word_count_score=result["task1"]["word_count"]["score"],
        timing_feedback=result["task2"]["timing"]["feedback"],
        timing_time=writing.end_time - writing.start_time,
        overall_band_score=result["overall_band_score"],
        total_feedback=result["task2"]["task_response"]["feedback"],
    )

    return result


@router.get("/{session_id}/", status_code=status.HTTP_200_OK)
async def get_writing_detail(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation),
):
    writing = await Writing.get_or_none(id=session_id)
    if not writing or writing.user_id != user.id:
        raise HTTPException(status_code=404, detail=t["not_found"])

    p1 = await WritingPart1.get(writing_id=session_id)
    p2 = await WritingPart2.get(writing_id=session_id)
    analyse = await WritingAnalyse.get_or_none(writing_id=session_id)

    resp = {
        "id": writing.id,
        "status": writing.status,
        "start_time": writing.start_time,
        "end_time": writing.end_time,
        "part1": {"content": p1.content, "diagram": p1.diagram, "answer": p1.answer},
        "part2": {"content": p2.content, "answer": p2.answer},
        "analyse": None,
    }
    if analyse:
        resp["analyse"] = {
            "task_achievement_feedback": analyse.task_achievement_feedback,
            "task_achievement_score": analyse.task_achievement_score,
            "lexical_resource_feedback": analyse.lexical_resource_feedback,
            "lexical_resource_score": analyse.lexical_resource_score,
            "coherence_and_cohesion_feedback": analyse.coherence_and_cohesion_feedback,
            "coherence_and_cohesion_score": analyse.coherence_and_cohesion_score,
            "grammatical_range_and_accuracy_feedback": analyse.grammatical_range_and_accuracy_feedback,
            "grammatical_range_and_accuracy_score": analyse.grammatical_range_and_accuracy_score,
            "word_count_feedback": analyse.word_count_feedback,
            "word_count_score": analyse.word_count_score,
            "timing_feedback": analyse.timing_feedback,
            "timing_time": analyse.duration,
            "overall_band_score": analyse.overall_band_score,
            "total_feedback": analyse.total_feedback,
        }
    return resp
