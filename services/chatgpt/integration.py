from openai import AsyncOpenAI
from typing import Dict
from config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class ChatGPTIntegration:
    """
    Class to integrate with OpenAI ChatGPT (GPT-4) for analyzing IELTS exam sections.
    """

    async def analyse_listening(self, system: str, user: str) -> str:
        """
        Analyze listening responses using ChatGPT.

        :param system: System-level instructions (e.g., "You are an IELTS examiner").
        :param user: The user's content to be analyzed (answers or input).
        :return: The model's textual response.
        """
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    async def analyse_writing(self, part1_answer: str, part2_answer: str) -> str:
        """
        Analyze IELTS Writing task answers.

        :param part1_answer: Answer for Task 1.
        :param part2_answer: Answer for Task 2.
        :return: Detailed feedback and scores.
        """
        prompt = f"""
        You are an IELTS examiner. Please evaluate the following writing answers:

        Part 1:
        {part1_answer}

        Part 2:
        {part2_answer}

        Provide feedback for:
        - Task Achievement
        - Coherence and Cohesion
        - Lexical Resource
        - Grammatical Range and Accuracy
        - Word Count

        Provide scores (0-9) and detailed feedback for each category.
        """
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
        )
        return response.choices[0].message.content

    async def analyse_speaking(self, part1_answer: str, part2_answer: str, part3_answer: str) -> str:
        """
        Analyze IELTS Speaking responses.

        :param part1_answer: Answer to Speaking Part 1.
        :param part2_answer: Answer to Speaking Part 2.
        :param part3_answer: Answer to Speaking Part 3.
        :return: Feedback and scores for each criterion.
        """
        prompt = f"""
        You are an IELTS examiner. Please evaluate the following speaking answers:

        Part 1:
        {part1_answer}

        Part 2:
        {part2_answer}

        Part 3:
        {part3_answer}

        Provide feedback for:
        - Fluency and Coherence
        - Lexical Resource
        - Grammatical Range and Accuracy
        - Pronunciation

        Provide scores (0-9) and detailed feedback for each category.
        """
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
        )
        return response.choices[0].message.content


async def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio using OpenAI's Whisper model.

    :param audio_path: Path to the audio file.
    :return: Transcribed text as a string.
    """
    with open(audio_path, "rb") as audio_file:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
    return transcript.text
