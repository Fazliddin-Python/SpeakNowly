from models.tests.writing import Writing, WritingPart1, WritingPart2
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import List, Optional
from services.analyses.writing_analyse_service import WritingAnalyseService

class WritingService:
    @staticmethod
    async def get_writing_tests(user_id: int):
        tests = await Writing.filter(user_id=user_id).all()
        if not tests:
            raise HTTPException(status_code=404, detail="No writing tests found for the user")
        return tests

    @staticmethod
    async def get_writing_test(test_id: int):
        test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
        if not test:
            raise HTTPException(status_code=404, detail="Writing test not found")
        return test

    @staticmethod
    async def create_writing_test(user_id: int, start_time: Optional[datetime] = None):
        test = await Writing.create(
            user_id=user_id,
            start_time=start_time or datetime.now(timezone.utc),
            status="started",
        )
        await WritingPart1.create(writing_id=test.id, content="Part 1 content")
        await WritingPart2.create(writing_id=test.id, content="Part 2 content")
        return test

    @staticmethod
    async def submit_writing_test(test_id: int, part1_answer: Optional[str], part2_answer: Optional[str]):
        test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
        if not test:
            raise HTTPException(status_code=404, detail="Writing test not found")
        if test.status == "completed":
            raise HTTPException(status_code=400, detail="This test has already been completed")
        if test.part1:
            test.part1.answer = part1_answer
            await test.part1.save()
        if test.part2:
            test.part2.answer = part2_answer
            await test.part2.save()
        test.status = "completed"
        test.end_time = datetime.now(timezone.utc)
        await test.save()
        return {"message": "Writing test submitted successfully"}

    @staticmethod
    async def cancel_writing_test(test_id: int):
        test = await Writing.get_or_none(id=test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Writing test not found")
        if test.status in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Test cannot be cancelled")
        test.status = "cancelled"
        await test.save()
        return {"message": "Writing test cancelled successfully"}

    @staticmethod
    async def get_writing_part1(part1_id: int):
        part1 = await WritingPart1.get_or_none(id=part1_id)
        if not part1:
            raise HTTPException(status_code=404, detail="Writing part 1 not found")
        return part1

    @staticmethod
    async def get_writing_part2(part2_id: int):
        part2 = await WritingPart2.get_or_none(id=part2_id)
        if not part2:
            raise HTTPException(status_code=404, detail="Writing part 2 not found")
        return part2

    @staticmethod
    async def analyse_writing(test_id: int, api_key: str):
        """
        Run analysis for a writing test (can be called from Celery or directly).
        """
        return await WritingAnalyseService.analyse(test_id, api_key)