import os
import json
from fastapi import HTTPException
from openai import OpenAIError
from .base_integration import BaseChatGPTIntegration

PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "prompts")

async def _load_prompt(prompt_file: str) -> str:
    prompt_path = os.path.join(PROMPTS_PATH, prompt_file)
    async with await open(prompt_path, "r") as f:
        return await f.read()

class ChatGPTReadingIntegration(BaseChatGPTIntegration):
    """
    Async integration with OpenAI for IELTS Reading test generation and answer checking.
    """

    async def generate_reading_test(self, level: str, **kwargs) -> str:
        """
        Generate a reading test based on the specified level.
        """
        prompt = await _load_prompt("reading.txt")
        prompt = prompt.replace("(level)", level)
        return await self._generate_response(prompt, **kwargs)

    async def save_reading_tasks(self, level: str, **kwargs) -> tuple[str, str]:
        """
        Generate reading tasks and return both the response and the prompt used.
        """
        prompt = await _load_prompt("reading.txt")
        prompt = prompt.replace("(level)", level)
        response = await self._generate_response(prompt, **kwargs)
        return response, prompt

    async def check_passage_answers(self, text: str, questions: list[dict], passage_id: int = None, **kwargs) -> dict:
        """
        Analyse all user answers for a passage using OpenAI.
        Args:
            text (str): Passage text.
            questions (list): List of dicts with keys: question, type, user_answer.
            passage_id (int, optional): Passage ID.
        Returns:
            dict: Analysis result from OpenAI (parsed JSON).
        """
        prompt_template = await _load_prompt("reading-question-answer.txt")
        data = [{
            "passage_id": passage_id,
            "text": text,
            "questions": [
                {
                    "question": q["question"],
                    "type": q["type"],
                    "user_answer": q["user_answer"]
                } for q in questions
            ]
        }]
        prompt = prompt_template.replace("(data)", json.dumps(data, ensure_ascii=False))
        response = await self._generate_response(prompt, **kwargs)
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to parse ChatGPT response: {e}")

    async def _generate_response(self, prompt: str, **kwargs) -> str:
        """
        Helper method to generate a response from OpenAI's chat completions.
        """
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")