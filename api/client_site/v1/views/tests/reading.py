from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from tortoise.exceptions import DoesNotExist
from models.tests.reading import Reading, Passage, Question, Variant, Answer
from ...serializers.tests.reading import (
    ReadingSerializer,
    PassageSerializer,
    QuestionSerializer,
    VariantSerializer,
    AnswerSerializer,
)
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=List[ReadingSerializer])
async def get_reading_tests(user_id: int):
    """
    Retrieve all reading tests for a specific user.
    """
    readings = await Reading.filter(user_id=user_id).all()
    if not readings:
        raise HTTPException(status_code=404, detail="No reading tests found for the user")
    return readings


@router.get("/{reading_id}/", response_model=ReadingSerializer)
async def get_reading_test(reading_id: int):
    """
    Retrieve a specific reading test by ID.
    """
    reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
    if not reading:
        raise HTTPException(status_code=404, detail="Reading test not found")
    return reading


@router.post("/start/", response_model=ReadingSerializer, status_code=status.HTTP_201_CREATED)
async def start_reading_test(user_id: int):
    """
    Start a new reading test for a user.
    """
    passages = await Passage.all()
    if not passages:
        raise HTTPException(status_code=404, detail="No passages available for the test")

    reading = await Reading.create(
        user_id=user_id,
        start_time=datetime.utcnow(),
        status="started",
        duration=60,
    )
    await reading.passages.add(*passages[:3])  # Assign the first 3 passages to the test
    return reading


@router.post("/{reading_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_reading_answers(reading_id: int, answers: List[AnswerSerializer]):
    """
    Submit answers for a reading test.
    """
    reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages__questions")
    if not reading:
        raise HTTPException(status_code=404, detail="Reading test not found")

    if reading.status == "completed":
        raise HTTPException(status_code=400, detail="This test has already been completed")

    total_score = 0
    for answer_data in answers:
        question = await Question.get_or_none(id=answer_data.question_id)
        if not question:
            raise HTTPException(status_code=404, detail=f"Question {answer_data.question_id} not found")

        is_correct = question.correct_answer == answer_data.text
        score = question.score if is_correct else 0
        total_score += score

        await Answer.create(
            user_id=reading.user_id,
            question_id=answer_data.question_id,
            text=answer_data.text,
            is_correct=is_correct,
            correct_answer=question.correct_answer,
            explanation=answer_data.explanation,
        )

    reading.status = "completed"
    reading.end_time = datetime.utcnow()
    reading.score = total_score
    await reading.save()

    return {"message": "Answers submitted successfully", "total_score": total_score}


@router.get("/passage/{passage_id}/", response_model=PassageSerializer)
async def get_reading_passage(passage_id: int):
    """
    Retrieve a specific reading passage by ID.
    """
    passage = await Passage.get_or_none(id=passage_id).prefetch_related("questions")
    if not passage:
        raise HTTPException(status_code=404, detail="Passage not found")
    return passage


@router.post("/{reading_id}/cancel/", status_code=status.HTTP_200_OK)
async def cancel_reading_test(reading_id: int):
    """
    Cancel a reading test.
    """
    reading = await Reading.get_or_none(id=reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail="Reading test not found")

    if reading.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Test cannot be cancelled")

    reading.status = "cancelled"
    await reading.save()
    return {"message": "Reading test cancelled successfully"}


@router.post("/{reading_id}/restart/", response_model=ReadingSerializer)
async def restart_reading_test(reading_id: int):
    """
    Restart a reading test.
    """
    reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
    if not reading:
        raise HTTPException(status_code=404, detail="Reading test not found")

    if reading.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed tests can be restarted")

    reading.status = "started"
    reading.start_time = datetime.utcnow()
    reading.end_time = None
    reading.score = 0
    await reading.save()

    # Reset answers
    await Answer.filter(user_id=reading.user_id, question__in=[q.id for p in reading.passages for q in p.questions]).delete()

    return reading


@router.get("/{reading_id}/analysis/", response_model=List[PassageSerializer])
async def analyse_reading_test(reading_id: int):
    """
    Analyse a completed reading test.
    """
    reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages__questions__answers")
    if not reading:
        raise HTTPException(status_code=404, detail="Reading test not found")

    if reading.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed tests can be analysed")

    data = []
    for passage in reading.passages:
        passage_data = {
            "id": passage.id,
            "level": passage.level,
            "number": passage.number,
            "title": passage.title,
            "text": passage.text,
            "skills": passage.skills,
            "questions": [],
        }
        for question in passage.questions:
            user_answer = await Answer.get_or_none(question_id=question.id, user_id=reading.user_id)
            passage_data["questions"].append({
                "id": question.id,
                "text": question.text,
                "type": question.type,
                "score": question.score,
                "correct_answer": question.correct_answer,
                "user_answer": user_answer.text if user_answer else None,
                "is_correct": user_answer.is_correct if user_answer else False,
            })
        data.append(passage_data)

    return data


@router.get("/questions/", response_model=List[QuestionSerializer])
async def get_questions():
    """
    Retrieve all questions.
    """
    questions = await Question.all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found")
    return questions


@router.get("/questions/{question_id}/", response_model=QuestionSerializer)
async def get_question(question_id: int):
    """
    Retrieve a specific question by ID.
    """
    question = await Question.get_or_none(id=question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/questions/", response_model=QuestionSerializer, status_code=status.HTTP_201_CREATED)
async def create_question(data: QuestionSerializer):
    """
    Create a new question.
    """
    question = await Question.create(**data.dict())
    return question


@router.delete("/questions/{question_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int):
    """
    Delete a specific question by ID.
    """
    question = await Question.get_or_none(id=question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    await question.delete()
    return {"message": "Question deleted successfully"}


@router.get("/variants/", response_model=List[VariantSerializer])
async def get_variants():
    """
    Retrieve all variants.
    """
    variants = await Variant.all()
    if not variants:
        raise HTTPException(status_code=404, detail="No variants found")
    return variants


@router.get("/variants/{variant_id}/", response_model=VariantSerializer)
async def get_variant(variant_id: int):
    """
    Retrieve a specific variant by ID.
    """
    variant = await Variant.get_or_none(id=variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return variant


@router.post("/variants/", response_model=VariantSerializer, status_code=status.HTTP_201_CREATED)
async def create_variant(data: VariantSerializer):
    """
    Create a new variant.
    """
    variant = await Variant.create(**data.dict())
    return variant


@router.delete("/variants/{variant_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(variant_id: int):
    """
    Delete a specific variant by ID.
    """
    variant = await Variant.get_or_none(id=variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    await variant.delete()
    return {"message": "Variant deleted successfully"}