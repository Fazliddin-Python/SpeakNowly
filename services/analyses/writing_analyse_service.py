from fastapi import HTTPException, status
from datetime import timedelta
from services.chatgpt import ChatGPTWritingIntegration
from models.analyses import WritingAnalyse
from models.tests.writing import WritingSession, WritingTask, WritingAnswer, WritingStatus

class WritingAnalyseService:
    @staticmethod
    async def analyse(session_id: int) -> dict:
        session = await WritingSession.get_or_none(id=session_id).prefetch_related("test__tasks", "answers__task")
        if not session:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Writing session not found")
        if session.status != WritingStatus.COMPLETED.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Writing session is not completed")

        # Get tasks and answers
        tasks = {task.part: task for task in await WritingTask.filter(test=session.test)}
        answers = {ans.task.part: ans for ans in await WritingAnswer.filter(session=session).prefetch_related("task")}

        part1_task = tasks.get(1)
        part2_task = tasks.get(2)
        part1_answer = answers.get(1)
        part2_answer = answers.get(2)

        # Only send non-empty parts to GPT
        part1_data = part1_task if part1_task and part1_answer and part1_answer.answer.strip() else None
        part2_data = part2_task if part2_task and part2_answer and part2_answer.answer.strip() else None

        if not part1_data and not part2_data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No answers provided for analysis.")

        chatgpt = ChatGPTWritingIntegration()
        analysis = {}
        if part1_data and part2_data:
            analysis = await chatgpt.analyse_writing(part1_data, part2_data, lang_code="en")
        elif part1_data:
            fake_part2 = type("FakePart", (), {"content": "", "answer": ""})()
            analysis = await chatgpt.analyse_writing(part1_data, fake_part2, lang_code="en")
        elif part2_data:
            fake_part1 = type("FakePart", (), {"content": "", "answer": ""})()
            analysis = await chatgpt.analyse_writing(fake_part1, part2_data, lang_code="en")

        # Parse analysis for each part
        part1_analysis = analysis.get("Task1") or analysis.get("part1") or {}
        part2_analysis = analysis.get("Task2") or analysis.get("part2") or {}

        def get_criteria(part, *keys):
            for key in keys:
                if key in part:
                    return part[key]
            return {}

        # Task 1
        task_achievement = get_criteria(part1_analysis, "TaskAchievement", "Task Achievement")
        coherence = get_criteria(part1_analysis, "CoherenceAndCohesion", "Coherence and Cohesion")
        lexical = get_criteria(part1_analysis, "LexicalResource", "Lexical Resource")
        grammar = get_criteria(part1_analysis, "GrammaticalRangeAndAccuracy", "Grammatical Range and Accuracy")
        word_count = get_criteria(part1_analysis, "WordCount", "Word Count")
        timing = get_criteria(part1_analysis, "TimingFeedback", "Timing Feedback")

        # Task 2
        task_response = get_criteria(part2_analysis, "TaskResponse", "Task Response")
        coherence2 = get_criteria(part2_analysis, "CoherenceAndCohesion", "Coherence and Cohesion")
        lexical2 = get_criteria(part2_analysis, "LexicalResource", "Lexical Resource")
        grammar2 = get_criteria(part2_analysis, "GrammaticalRangeAndAccuracy", "Grammatical Range and Accuracy")
        word_count2 = get_criteria(part2_analysis, "WordCount", "Word Count")
        timing2 = get_criteria(part2_analysis, "TimingFeedback", "Timing Feedback")

        duration = (session.end_time - session.start_time) if (session.start_time and session.end_time) else timedelta(0)

        # Save separate analyses for each part if they exist
        result = {}
        if part1_data:
            result["part1"] = await WritingAnalyse.create(
                writing=session,
                part=1,
                task_achievement_score=task_achievement.get("Score", 0) or task_achievement.get("score", 0),
                task_achievement_feedback=task_achievement.get("Feedback", "") or task_achievement.get("feedback", ""),
                lexical_resource_score=lexical.get("Score", 0) or lexical.get("score", 0),
                lexical_resource_feedback=lexical.get("Feedback", "") or lexical.get("feedback", ""),
                coherence_and_cohesion_score=coherence.get("Score", 0) or coherence.get("score", 0),
                coherence_and_cohesion_feedback=coherence.get("Feedback", "") or coherence.get("feedback", ""),
                grammatical_range_and_accuracy_score=grammar.get("Score", 0) or grammar.get("score", 0),
                grammatical_range_and_accuracy_feedback=grammar.get("Feedback", "") or grammar.get("feedback", ""),
                word_count_score=word_count.get("Score", 0) or word_count.get("score", 0),
                word_count_feedback=word_count.get("Feedback", "") or word_count.get("feedback", ""),
                timing_feedback=timing.get("Feedback", "") or timing.get("feedback", ""),
                duration=duration,
            )
        if part2_data:
            result["part2"] = await WritingAnalyse.create(
                writing=session,
                part=2,
                task_achievement_score=task_response.get("Score", 0) or task_response.get("score", 0),
                task_achievement_feedback=task_response.get("Feedback", "") or task_response.get("feedback", ""),
                lexical_resource_score=lexical2.get("Score", 0) or lexical2.get("score", 0),
                lexical_resource_feedback=lexical2.get("Feedback", "") or lexical2.get("feedback", ""),
                coherence_and_cohesion_score=coherence2.get("Score", 0) or coherence2.get("score", 0),
                coherence_and_cohesion_feedback=coherence2.get("Feedback", "") or coherence2.get("feedback", ""),
                grammatical_range_and_accuracy_score=grammar2.get("Score", 0) or grammar2.get("score", 0),
                grammatical_range_and_accuracy_feedback=grammar2.get("Feedback", "") or grammar2.get("feedback", ""),
                word_count_score=word_count2.get("Score", 0) or word_count2.get("score", 0),
                word_count_feedback=word_count2.get("Feedback", "") or word_count2.get("feedback", ""),
                timing_feedback=timing2.get("Feedback", "") or timing2.get("feedback", ""),
                duration=duration,
            )
        return result