from fastapi import HTTPException, status
from datetime import timedelta
from services.chatgpt import ChatGPTWritingIntegration
from models.analyses import WritingAnalyse
from models.tests import Writing, WritingStatus

class WritingAnalyseService:
    @staticmethod
    async def analyse(test_id: int) -> WritingAnalyse:
        """
        Analyse a completed Writing test and save the result.
        """
        test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
        if not test:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Writing test not found")
        if test.status != WritingStatus.COMPLETED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Writing test is not completed")
        existing = await WritingAnalyse.get_or_none(writing_id=test.id)
        if existing:
            return existing
        if not test.part1 or not test.part2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Test parts are missing")

        chatgpt = ChatGPTWritingIntegration()
        analysis = await chatgpt.analyse_writing(test.part1, test.part2, lang_code="en")
        if not analysis:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to analyse writing test")

        duration = (test.end_time - test.start_time) if (test.start_time and test.end_time) else timedelta(0)

        def get_criteria(part, *keys, default=""):
            for key in keys:
                if key in part:
                    return part[key]
            return {}

        part1 = analysis.get("Task1") or analysis.get("part1") or {}
        part2 = analysis.get("Task2") or analysis.get("part2") or {}

        # Task 1 (part1)
        task_achievement = get_criteria(part1, "TaskAchievement", "Task Achievement")
        coherence = get_criteria(part1, "CoherenceAndCohesion", "Coherence and Cohesion")
        lexical = get_criteria(part1, "LexicalResource", "Lexical Resource")
        grammar = get_criteria(part1, "GrammaticalRangeAndAccuracy", "Grammatical Range and Accuracy")
        word_count = get_criteria(part1, "WordCount", "Word Count")
        timing = get_criteria(part1, "TimingFeedback", "Timing Feedback")

        # Task 2 (part2)
        task_response = get_criteria(part2, "TaskResponse", "Task Response")
        coherence2 = get_criteria(part2, "CoherenceAndCohesion", "Coherence and Cohesion")
        lexical2 = get_criteria(part2, "LexicalResource", "Lexical Resource")
        grammar2 = get_criteria(part2, "GrammaticalRangeAndAccuracy", "Grammatical Range and Accuracy")
        word_count2 = get_criteria(part2, "WordCount", "Word Count")
        timing2 = get_criteria(part2, "TimingFeedback", "Timing Feedback")

        # Считаем общий балл если не пришёл
        overall_band_score = analysis.get("overall_band_score")
        if overall_band_score is None:
            scores = []
            for crit in [task_achievement, coherence, lexical, grammar, word_count, task_response, coherence2, lexical2, grammar2, word_count2]:
                score = crit.get("Score") or crit.get("score")
                if isinstance(score, (int, float)):
                    scores.append(score)
            overall_band_score = round(sum(scores) / len(scores), 1) if scores else 0

        # Собираем общий фидбек (можно доработать под твой prompt)
        total_feedback = ""
        if "overall_feedback" in analysis:
            total_feedback = analysis["overall_feedback"]
        elif "total_feedback" in analysis:
            total_feedback = analysis["total_feedback"]
        else:
            # Собираем из двух частей
            total_feedback = (
                (task_achievement.get("Feedback") or task_achievement.get("feedback") or "") + "\n" +
                (task_response.get("Feedback") or task_response.get("feedback") or "")
            ).strip()

        writing_analyse = await WritingAnalyse.create(
            writing=test,
            # Task 1
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
            # Общие
            overall_band_score=overall_band_score,
            total_feedback=total_feedback,
            duration=duration,
        )
        return writing_analyse