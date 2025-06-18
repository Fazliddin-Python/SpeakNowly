from fastapi import HTTPException
import os
import json
import aiofiles
import asyncio
from openai import OpenAIError
from .base_integration import BaseChatGPTIntegration

PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "prompts")

async def load_prompt(prompt_file: str) -> str:
    """
    Load a prompt template from a file in the prompts directory.
    """
    prompt_path = os.path.join(PROMPTS_PATH, prompt_file)
    async with aiofiles.open(prompt_path, "r", encoding="utf-8") as f:
        return await f.read()


def extract_json_array(text: str) -> str:
    """
    Extract the outermost JSON array from the given text, handling nested brackets.
    If no balanced array is found, return the original text.
    """
    start = text.find('[')
    if start == -1:
        return text
    stack = []
    for idx, ch in enumerate(text[start:], start):
        if ch == '[':
            stack.append(ch)
        elif ch == ']':
            stack.pop()
            if not stack:
                return text[start:idx+1]
    return text


class ChatGPTReadingIntegration(BaseChatGPTIntegration):
    """
    Asynchronous integration with OpenAI for generating IELTS reading tests
    and evaluating user answers via chat completions.
    """

    async def generate_reading_test(self, level: str, **kwargs) -> str:
        """
        Generate a three-passage reading test for the specified difficulty level.
        Returns JSON string of the test data.
        """
        prompt_part1 = await load_prompt("reading_13.txt")
        prompt_part2 = await load_prompt("reading_14.txt")
        prompt_part1 = prompt_part1.replace("(level)", level)
        prompt_part2 = prompt_part2.replace("(level)", level)

        kwargs.setdefault("max_tokens", 6000)
        kwargs.setdefault("temperature", 0.0)

        resp1, resp2 = await asyncio.gather(
            self._generate_response(prompt_part1, **kwargs),
            self._generate_response(prompt_part2, **kwargs)
        )

        # Clean and parse JSON arrays
        cleaned1 = extract_json_array(resp1.replace("```json", "").replace("```", "").strip())
        passages1 = json.loads(cleaned1)
        p1 = next((p for p in passages1 if p.get("number") == 1), None)
        p3 = next((p for p in passages1 if p.get("number") == 3), None)
        if not (p1 and p3):
            raise HTTPException(status_code=500, detail="Failed to extract passages 1 and 3")

        cleaned2 = extract_json_array(resp2.replace("```json", "").replace("```", "").strip())
        passages2 = json.loads(cleaned2)
        p2 = next((p for p in passages2 if p.get("number") == 2), None)
        if not p2:
            raise HTTPException(status_code=500, detail="Failed to extract passage 2")

        test_data = [p1, p2, p3]
        return json.dumps(test_data, ensure_ascii=False)

    async def save_reading_tasks(self, level: str, **kwargs) -> tuple[str, str]:
        """
        Generate reading tasks and return both the raw response and the prompt used.
        """
        prompt = await load_prompt("reading.txt")
        prompt = prompt.replace("(level)", level)
        kwargs.setdefault("max_tokens", 6000)
        kwargs.setdefault("temperature", 0.0)
        response = await self._generate_response(prompt, **kwargs)
        return response, prompt

    async def check_passage_answers(
        self, text: str, questions: list[dict], passage_id: int = None, **kwargs
    ) -> list[dict]:
        """
        Evaluate user answers for a passage.
        Returns a list of analysis objects for each passage.
        Each object contains 'passages' and 'stats' or is the flat structure.
        """
        prompt_template = await load_prompt("reading-question-answer.txt")
        payload = [{
            "passage_id": passage_id,
            "text": text,
            "questions": [
                {
                    "question_id": q["question_id"],
                    "question": q["question"],
                    "type": q.get("type"),
                    "user_answer": q["user_answer"],
                }
                for q in questions
            ]
        }]
        prompt = prompt_template.replace("(data)", json.dumps(payload, ensure_ascii=False))
        kwargs.setdefault("max_tokens", 6000)
        kwargs.setdefault("temperature", 0.0)

        raw_response = await self._generate_response(prompt, **kwargs)
        cleaned = raw_response.replace("```json", "").replace("```", "").strip()
        json_array_text = extract_json_array(cleaned)
        try:
            return json.loads(json_array_text)
        except json.JSONDecodeError as e:
            # Log the error and raw data for debugging
            print("JSON decode error:", e)
            print("Raw response:", raw_response)
            print("Extracted JSON:", json_array_text)
            raise HTTPException(status_code=502, detail="Failed to parse ChatGPT JSON response")

    async def _generate_response(self, prompt: str, **kwargs) -> str:
        """
        Internal helper to call OpenAI's chat completion endpoint.
        """
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error: {e}")
