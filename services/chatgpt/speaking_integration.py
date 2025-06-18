from fastapi import HTTPException, status, UploadFile
import json
import re
from openai import AuthenticationError, BadRequestError, OpenAIError, RateLimitError
from .base_integration import BaseChatGPTIntegration
from io import BytesIO

QUESTIONS_PROMPT = """
Generate a set of IELTS Speaking test questions in 3 parts.

Part 1: Always start with questions about full name, address, and work/education. Then add 2 different topics, each with 2-3 personal questions (likes/dislikes, free time, favorite things, etc).
Part 2: Give a descriptive question and three follow-up points. The topic should not overlap with Part 1.
Part 3: Give argumentative questions related to Part 2. Total 3-6 questions.

All "question" fields must be arrays of strings.

Return ONLY a valid JSON object. Do not include explanations, markdown, or text outside the JSON.

{
  "part1": {"title": "...", "question": ["...", "..."]},
  "part2": {"title": "...", "question": ["...", "..."]},
  "part3": {"title": "...", "question": ["...", "..."]}
}
"""

ANALYSE_PROMPT = """
You are an experienced IELTS examiner. Evaluate the following candidate's speaking responses based on the IELTS Speaking criteria:

Fluency and Coherence: Assess the flow of speech, logical structuring, and absence of unnatural pauses.
Lexical Resource: Evaluate the variety and appropriateness of vocabulary used.
Grammatical Range and Accuracy: Consider the grammatical structures used and their accuracy.
Pronunciation: Assess the clarity of pronunciation, stress, and intonation.

IMPORTANT:
- There may be less than three answers (some parts may be missing or empty).
- If a part is missing or empty, you MUST assign a score of 0 for all criteria for that part and provide feedback: "No answer".
- The overall band score must be the average of the available parts (including zeros for missing parts), as in the official IELTS scoring.

Please provide:

Individual scores (Band 1 to Band 9) for each criterion.
A detailed analysis explaining the strengths and weaknesses for each criterion.
A final overall band score (Band 1 to Band 9) based on the average of the individual scores (including zeros for missing parts).

Return ONLY a valid JSON object. Do not include any explanations, markdown, or text outside the JSON. If you understand, reply only with the JSON object.

{
  "fluency_and_coherence_score": ...,
  "fluency_and_coherence_feedback": "...",
  "lexical_resource_score": ...,
  "lexical_resource_feedback": "...",
  "grammatical_range_and_accuracy_score": ...,
  "grammatical_range_and_accuracy_feedback": "...",
  "pronunciation_score": ...,
  "pronunciation_feedback": "...",
  "overall_band_score": ...,
  "feedback": "...",
  "part1_score": ...,
  "part1_feedback": "...",
  "part2_score": ...,
  "part2_feedback": "...",
  "part3_score": ...,
  "part3_feedback": "..."
}
"""

class ChatGPTSpeakingIntegration(BaseChatGPTIntegration):
    """
    Asynchronous integration with OpenAI for generating and analyzing IELTS Speaking.
    """

    async def generate_ielts_speaking_questions(self) -> dict:
        """
        Generate IELTS Speaking questions using OpenAI.

        Returns:
            dict: Generated questions in JSON format.
        """
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": QUESTIONS_PROMPT}],
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)

    async def generate_ielts_speaking_analyse(self, part1, part2, part3) -> dict:
        """
        Analyse a completed Speaking test using OpenAI.

        Args:
            part1, part2, part3: SpeakingAnswers objects with .question.title, .question.content, .text_answer

        Returns:
            dict: Analysis result in JSON format.
        """
        data = [
            {"title": part1.question.title, "question": part1.question.content, "user_answer": part1.text_answer},
            {"title": part2.question.title, "question": part2.question.content, "user_answer": part2.text_answer},
            {"title": part3.question.title, "question": part3.question.content, "user_answer": part3.text_answer},
        ]
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ANALYSE_PROMPT},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
            ],
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        if not raw or not raw.strip():
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "OpenAI вернул пустой ответ для анализа.")

        # Удаляем markdown и ищем JSON
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"OpenAI вернул невалидный JSON:\n{raw}"
            )
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except Exception as e:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Ошибка парсинга ответа OpenAI: {e}\nRAW: {json_str}"
            )

    async def transcribe_audio_file_async(self, audio: UploadFile, lang="en") -> str:
        """
        Asynchronously transcribe audio using OpenAI Whisper.
        """
        try:
            content = await audio.read()
            file_like = BytesIO(content)
            file_like.name = audio.filename

            transcript = await self.async_client.audio.transcriptions.create(
                file=file_like,
                model="whisper-1",
                response_format="text",
                language=lang
            )
            return transcript
        except AuthenticationError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication with OpenAI failed. Check your API key.")
        except BadRequestError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
        except RateLimitError as e:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"Rate limit exceeded. {str(e)}")
        except OpenAIError as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"OpenAI API error: {str(e)}")