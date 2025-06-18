from fastapi import HTTPException
import os
import json
import aiofiles
import re
import asyncio
from openai import OpenAIError
from .base_integration import BaseChatGPTIntegration

PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "prompts")

async def _load_prompt(prompt_file: str) -> str:
    prompt_path = os.path.join(PROMPTS_PATH, prompt_file)
    async with aiofiles.open(prompt_path, "r", encoding="utf-8") as f:
        return await f.read()

def extract_json_array(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    return text

class ChatGPTReadingIntegration(BaseChatGPTIntegration):
    """
    Async integration with OpenAI for IELTS Reading test generation and answer checking.
    """

    async def generate_reading_test(self, level: str, **kwargs) -> str:
        prompt_13 = await _load_prompt("reading_13.txt")
        prompt_14 = await _load_prompt("reading_14.txt")
        prompt_13 = prompt_13.replace("(level)", level)
        prompt_14 = prompt_14.replace("(level)", level)

        kwargs.setdefault("max_tokens", 128000)
        kwargs.setdefault("temperature", 0.2)

        resp_13, resp_14 = await asyncio.gather(
            self._generate_response(prompt_13, **kwargs),
            self._generate_response(prompt_14, **kwargs)
        )

        cleaned_13 = extract_json_array(resp_13.replace("```json", "").replace("```", "").strip())
        passages_13 = json.loads(cleaned_13)
        p1 = next((p for p in passages_13 if p.get("number") == 1), None)
        p3 = next((p for p in passages_13 if p.get("number") == 3), None)
        if not (p1 and p3):
            raise HTTPException(status_code=500, detail="Failed to get passages 1 and 3")

        cleaned_14 = extract_json_array(resp_14.replace("```json", "").replace("```", "").strip())
        passages_14 = json.loads(cleaned_14)
        p2 = next((p for p in passages_14 if p.get("number") == 2), None)
        if not p2:
            raise HTTPException(status_code=500, detail="Failed to get passage 2")

        all_passages = [p1, p2, p3]
        return json.dumps(all_passages, ensure_ascii=False)

    async def save_reading_tasks(self, level: str, **kwargs) -> tuple[str, str]:
        """
        Generate reading tasks and return both the response and the prompt used.
        """
        prompt = await _load_prompt("reading.txt")
        prompt = prompt.replace("(level)", level)
        kwargs.setdefault("max_tokens", 128000)
        kwargs.setdefault("temperature", 0.2)
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
        kwargs.setdefault("max_tokens", 128000)
        kwargs.setdefault("temperature", 0.2)
        response = await self._generate_response(prompt, **kwargs)
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            cleaned = extract_json_array(cleaned)
            return json.loads(cleaned)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to parse ChatGPT response: {e}")

    async def _generate_response(self, prompt: str, **kwargs) -> str:
        """
        Helper method to generate a response from OpenAI's chat completions.
        """
        try:
            kwargs.setdefault("max_tokens", 128000)
            kwargs.setdefault("temperature", 0.2)
            response = await self.async_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")