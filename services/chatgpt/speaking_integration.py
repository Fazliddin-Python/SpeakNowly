from fastapi import HTTPException, status, UploadFile
import json
import re
from openai import AuthenticationError, BadRequestError, OpenAIError, RateLimitError
from .base_integration import BaseChatGPTIntegration
from io import BytesIO
import random
from datetime import datetime

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
You are an experienced IELTS examiner. Evaluate the following candidate's speaking responses based on the IELTS Speaking criteria.

For each provided answer, return an object with:
- part: the part number (1, 2, or 3)
- fluency_and_coherence_score (1-9)
- fluency_and_coherence_feedback
- lexical_resource_score (1-9)
- lexical_resource_feedback
- grammatical_range_and_accuracy_score (1-9)
- grammatical_range_and_accuracy_feedback
- pronunciation_score (1-9)
- pronunciation_feedback

STRICTNESS INSTRUCTIONS:
- Be strict and objective, as a real IELTS examiner.
- Do NOT award band 8.0 or higher unless the speaking is truly exceptional, nearly native-like, with very few errors, highly sophisticated vocabulary, and complex structures.
- If there are frequent errors, hesitation, lack of complexity, or awkward phrasing, do NOT give more than 7.0.
- Use the official IELTS band descriptors for each criterion.
- Most responses should receive scores between 5.0 and 7.0. Only outstanding, rare responses should get higher.

IMPORTANT:
- There may be less than three answers (some parts may be missing or empty).
- Only analyse and return results for the parts that are actually provided by the user (do not generate or fill missing parts).
- The overall band score must be the average of all scores for all provided parts (rounded to the nearest 0.5), as in the official IELTS scoring.

Please provide:

- "analysis": an array of objects (one per provided answer, in order)
- "overall_band_score": the average of all scores for all provided parts (rounded to the nearest 0.5)
- "feedback": a general summary for the candidate

Return ONLY a valid JSON object. Do not include explanations, markdown, or text outside the JSON.

Example:
{
  "analysis": [
    {
      "part": 1,
      "fluency_and_coherence_score": 6,
      "fluency_and_coherence_feedback": "...",
      "lexical_resource_score": 6,
      "lexical_resource_feedback": "...",
      "grammatical_range_and_accuracy_score": 6,
      "grammatical_range_and_accuracy_feedback": "...",
      "pronunciation_score": 6,
      "pronunciation_feedback": "..."
    }
    // ...more parts if provided
  ],
  "overall_band_score": 6.0,
  "feedback": "..."
}
"""

class ChatGPTSpeakingIntegration(BaseChatGPTIntegration):
    """
    Asynchronous integration with OpenAI for generating and analyzing IELTS Speaking.
    """

    async def generate_ielts_speaking_questions(self, user_id=None) -> dict:
        """
        Generate IELTS Speaking questions using OpenAI.

        Args:
            user_id (int): Unique identifier for the user.

        Returns:
            dict: Generated questions in JSON format.
        """
        seed = random.randint(1, 1_000_000)
        now = datetime.now().isoformat()
        prompt = (
            QUESTIONS_PROMPT
            + f"\n\n# Seed: {seed}\n"
            + f"# User ID: {user_id}\n"
            + f"# Date: {now}\n"
            + "Please use the above seed, user ID, and date to make the questions unique."
        )
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)

    async def generate_ielts_speaking_analyse(self, parts: list) -> dict:
        """
        Analyse a completed Speaking test using OpenAI.

        Args:
            parts: list of dicts with keys: part, title, question, user_answer

        Returns:
            dict: Analysis result in JSON format.
        """
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ANALYSE_PROMPT},
                {"role": "user", "content": json.dumps(parts, ensure_ascii=False)},
            ],
            temperature=0.3,
            max_tokens=6000
        )
        raw = response.choices[0].message.content
        if not raw or not raw.strip():
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "OpenAI returned an empty response for analysis.")

        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"OpenAI returned invalid JSON:\n{raw}"
            )
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except Exception as e:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Error parsing OpenAI response: {e}\nRAW: {json_str}"
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