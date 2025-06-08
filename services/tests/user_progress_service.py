from tortoise.functions import Max
from models.analyses import ListeningAnalyse, SpeakingAnalyse, WritingAnalyse
from models.tests import Reading

class UserProgressService:

    @staticmethod
    async def get_latest_analysis(user_id: int):
        latest_listening = await ListeningAnalyse.filter(user_id=user_id).order_by("-session__start_time").first()
        latest_speaking = await SpeakingAnalyse.filter(speaking__user_id=user_id).order_by("-speaking__start_time").first()
        latest_writing = await WritingAnalyse.filter(writing__user_id=user_id).order_by("-writing__start_time").first()
        latest_reading = await Reading.filter(user_id=user_id).order_by("-start_time").first()

        return {
            "listening": latest_listening.overall_score if latest_listening else None,
            "speaking": latest_speaking.overall_band_score if latest_speaking else None,
            "writing": latest_writing.overall_band_score if latest_writing else None,
            "reading": latest_reading.score if latest_reading else None,
        }

    @staticmethod
    async def get_highest_score(user_id: int):
        # Listening
        listening_scores = await ListeningAnalyse.filter(user_id=user_id).values_list("overall_score", flat=True)
        max_listening = max(listening_scores) if listening_scores else 0

        # Speaking
        speaking_scores = await SpeakingAnalyse.filter(speaking__user_id=user_id).values_list("overall_band_score", flat=True)
        max_speaking = max(speaking_scores) if speaking_scores else 0

        # Writing
        writing_scores = await WritingAnalyse.filter(writing__user_id=user_id).values_list("overall_band_score", flat=True)
        max_writing = max(writing_scores) if writing_scores else 0

        # Reading
        reading_scores = await Reading.filter(user_id=user_id).values_list("score", flat=True)
        max_reading = max(reading_scores) if reading_scores else 0

        max_scores = [
            max_listening or 0,
            max_speaking or 0,
            max_writing or 0,
            max_reading or 0,
        ]

        total = sum(max_scores) / 4
        return round(total * 2) / 2
