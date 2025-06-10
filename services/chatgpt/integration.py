import asyncio
import json
import os
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import HTTPException
import openai

from config import OPENAI_API_KEY

# -------------------------------------------------
# ChatGPTIntegration: Speaking + Reading + Writing
# -------------------------------------------------

class ChatGPTIntegration:
    """
    Integration with OpenAI ChatGPT (GPT-4) to:
      1) Generate three-part IELTS Speaking questions.
      2) Analyze transcribed speaking answers and return scores/feedback.
      3) Generate an IELTS-style reading passage + multiple-choice questions.
      4) Analyze submitted reading answers (optional).
      5) Generate IELTS Writing Task 1/Task 2 questions and (optional) analyse writing.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize both AsyncOpenAI and sync OpenAI clients.
        If api_key is not provided, fallback to OPENAI_API_KEY from config.
        """
        key = api_key or OPENAI_API_KEY
        if not key:
            raise HTTPException(status_code=500, detail="OpenAI API key not provided")
        self.async_client = openai.AsyncOpenAI(api_key=key)
        openai.api_key = key  # for synchronous endpoints (writing generation)

    
    async def analyse_listening(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"ChatGPT API error: {str(e)}")


    # -----------------------
    #    Speaking Methods
    # -----------------------

    async def generate_speaking_questions(self) -> Dict[str, str]:
        """
        Generate a set of IELTS Speaking test questions divided into three parts.
        Returns a dict with keys:
          part1_title, part1_question,
          part2_title, part2_question,
          part3_title, part3_question.
        """
        prompt = """
You are a system that generates IELTS Speaking test questions in JSON format.
Divide the questions into three parts (PART_1, PART_2, PART_3). 
For PART_1, ask for full name, address, work/education, then 2-4 personal questions.
For PART_2, create a descriptive question with 3 bullet sub-questions.
For PART_3, create 3-5 argumentative questions related to PART_2.

Return exactly the following JSON structure without extra commentary:
{
  "part1_title": "<string>",
  "part1_question": "<string>",
  "part2_title": "<string>",
  "part2_question": "<string>",
  "part3_title": "<string>",
  "part3_question": "<string>"
}
"""
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs valid JSON."},
                    {"role": "user", "content": prompt.strip()},
                ],
                temperature=0.0,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error (generate speaking questions): {e}")

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON returned from GPT for speaking questions")

    async def analyse_speaking(self, part1_answer: str, part2_answer: str, part3_answer: str) -> Dict:
        """
        Analyze three parts of a candidate's speaking responses.
        Returns a dict with the following structure:
        {
          "feedback": "<overall feedback>",
          "overall_band_score": <number 0-9, may be .5>,
          "fluency_and_coherence": {"score": <0-9>, "feedback": "<string>"},
          "lexical_resource": {"score": <0-9>, "feedback": "<string>"},
          "grammatical_range_and_accuracy": {"score": <0-9>, "feedback": "<string>"},
          "pronunciation": {"score": <0-9>, "feedback": "<string>"}
        }
        """
        prompt = f"""
You are an IELTS examiner. Evaluate the following speaking answers and output valid JSON:

Part 1 Answer:
\"\"\"{part1_answer}\"\"\"

Part 2 Answer:
\"\"\"{part2_answer}\"\"\"

Part 3 Answer:
\"\"\"{part3_answer}\"\"\"

Return JSON with keys:
- "feedback": overall feedback string
- "overall_band_score": number (0-9, can include .5)
- "fluency_and_coherence": {{"score": <0-9>, "feedback": "<string>"}}
- "lexical_resource": {{"score": <0-9>, "feedback": "<string>"}}
- "grammatical_range_and_accuracy": {{"score": <0-9>, "feedback": "<string>"}}
- "pronunciation": {{"score": <0-9>, "feedback": "<string>"}}
"""
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs valid JSON."},
                    {"role": "user", "content": prompt.strip()},
                ],
                temperature=0.0,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error (analyse speaking): {e}")

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON returned from GPT for speaking analysis")

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe a local audio file using OpenAI's Whisper model.
        Returns the transcribed text.
        """
        import aiofiles # type: ignore

        try:
            async with aiofiles.open(audio_path, "rb") as audio_file:
                transcript_response = await self.async_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI Whisper transcription error: {e}")

        if isinstance(transcript_response, str):
            return transcript_response
        else:
            raise HTTPException(status_code=500, detail="Unexpected response format from Whisper transcription")


    # -----------------------
    #    Reading Methods
    # -----------------------

    async def generate_reading_data(self, passage_number: int) -> List[Dict]:
        """
        Generate a full IELTS Reading test (3 passages, 40 questions) with detailed structure.
        """
        PROMPT_TEMPLATE = f"""
Create a full IELTS Reading test with the following criteria:

Generate **three passages** in a single test. Each passage must have:
- a unique topic
- a distinct reading skill
- and a different level: one easy, one medium, and one hard

All three passages must be returned in a **single JSON array** (not wrapped in any dictionary or object).

Test ID / Starting Passage Number: {passage_number}

Level:
Each passage must have a different level of difficulty and must include a "level" field:
Passage 1: level = "easy"
Passage 2: level = "medium"
Passage 3: level = "hard"

Structure:
The test must consist of three unique passages, each representing a different and distinctive theme or subject.
The total number of questions must be 40:
Passage 1: 13 questions.
Passage 2: 14 questions.
Passage 3: 13 questions.
Ensure a balanced mix of question types (MULTIPLE_CHOICE and TEXT) for each passage:
Each passage should include 50-70% multiple-choice questions and 30-50% free-text questions.

Skills:
Each passage should assess a specific reading skill, such as:
Skimming, Scanning, Understanding Details, or Inference.
Include a "skill" field for each passage indicating the primary skill being tested.

Scoring:
Each question should have a "score" field specifying the points awarded for a correct answer.
MULTIPLE_CHOICE questions should be worth 1-2 points.
TEXT questions should be worth 2-4 points depending on complexity.

Timing:
The entire test must be solvable within 60 minutes.

Word Count for Passages:
Each passage must contain between 500 and 800 words.
The word count and complexity of the passages should align with the level (easy, medium, or hard).

Themes:
Each passage must have a unique, culturally diverse or academic theme.

Return only a JSON array with exactly this format:

```json
[
  {{
    "number": 1,
    "level": "easy",
    "skill": "Skimming",
    "title": "The Rise of Eco-Tourism",
    "passage": "Full passage text here between 500–800 words.",
    "questions": [
      {{
        "text": "What is the main goal of eco-tourism?",
        "type": "MULTIPLE_CHOICE",
        "score": 1,
        "answers": [
          {{"text": "To promote sustainable travel", "is_correct": true}},
          {{"text": "To lower travel costs", "is_correct": false}},
          {{"text": "To avoid cultural experiences", "is_correct": false}}
        ]
      }},
      {{
        "text": "List two benefits of eco-tourism mentioned in the text.",
        "type": "TEXT",
        "score": 3,
        "answers": []
      }}
    ]
  }},
  ...
]
"""
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that returns only valid JSON."},
                    {"role": "user", "content": PROMPT_TEMPLATE.strip()},
                ],
                temperature=0.7,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI error (reading generation): {str(e)}")

        content = response.choices[0].message.content
        try:
            print(f"Generated reading data: {content}")
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON from GPT (reading generation)")

    async def check_text_question_answer(self, payload: str) -> str:
        """
        Analyze submitted answers and return correctness, correct answers, explanations, and overall band score (0-9).
        """
        PROMPT_TEMPLATE = """
You are evaluating a reading comprehension test. For each question in the provided payload, determine:
- is_correct (true/false)
- correct_answer (option ID or full text)
- explanation (short, only if incorrect)
Also compute:
- total_correct
- total_questions
- accuracy (percentage)
- overall_score (0-9 IELTS band)

Return ONLY valid JSON in the format:

{
    "passages": {
      "passage_id": <id>,
      "analysis": [
        {
          "question_id": <id>,
          "correct_answer": "<id or text>",
          "explanation": "<reason>",
          "is_correct": <true/false>
        }
      ]
    }
  },
  {
    "stats": {
      "total_correct": <int>,
      "total_questions": <int>,
      "accuracy": <float>,
      "overall_score": <int>
    }
}
"""

        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Return only valid JSON."},
                    {"role": "user", "content": PROMPT_TEMPLATE.strip() + "\n" + payload.strip()},
                ],
                temperature=0.3,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI error (answer check): {e}")

        return response.choices[0].message.content


    # -----------------------
    #    Writing Methods
    # -----------------------

    async def generate_writing_part1_question(self) -> Dict:
        """
        Generate an IELTS Writing Task 1 question with chart data in JSON format.
        Uses sync OpenAI client (openai).
        Expects JSON response matching WritingTask1Data schema.
        """
        prompt1 = """
Create a line or bar or pie chart based on an IELTS Writing Task 1 question comparing five categories in two different years on a given topic.
The data for the chart is in JSON format with the keys question, categories, years, and:
question, categories, year1, year2, data_year1, data_year2.
Return the JSON using keys:
- "question": <string>
- "categories": [<string>, ...]
- "year1": <integer>
- "year2": <integer>
- "data_year1": [<numbers>]
- "data_year2": [<numbers>]
"""
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs valid JSON."},
                    {"role": "user", "content": prompt1.strip()},
                ],
                temperature=0.0,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error (generate writing part1): {e}")

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON returned from GPT for writing part1")

    async def create_writing_part1_diagram(
        self,
        question: str,
        categories: List[str],
        data_year1: List[float],
        data_year2: List[float],
        year1: int,
        year2: int
    ) -> str:
        """
        Create a bar chart (.png) comparing data_year1 vs data_year2 across categories.
        Saves under media/writing/diagrams and returns file path.
        """
        import matplotlib.pyplot as plt  # type: ignore
        import os

        output_dir = "media/writing/diagrams"
        os.makedirs(output_dir, exist_ok=True)

        def plot_and_save():
            fig, ax = plt.subplots(figsize=(8, 6))
            bar_width = 0.35
            x = range(len(categories))

            ax.bar(x, data_year1, width=bar_width, label=str(year1), alpha=0.7)
            ax.bar([i + bar_width for i in x], data_year2, width=bar_width, label=str(year2), alpha=0.7)

            ax.set_xlabel("Categories", fontsize=12)
            ax.set_ylabel("Value", fontsize=12)
            ax.set_title(f"Comparison by Category ({year1} vs {year2})", fontsize=14)
            ax.set_xticks([i + bar_width / 2 for i in x])
            ax.set_xticklabels(categories, fontsize=10)
            ax.legend()

            filename = os.path.join(output_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
            plt.savefig(filename)
            plt.close()
            return filename

        loop = asyncio.get_running_loop()
        filename = await loop.run_in_executor(None, plot_and_save)
        return filename

    async def create_line_chart(self, categories: List[str], year1: int, year2: int,
                          data_year1: List[float], data_year2: List[float]) -> str:
        """
        Create a line chart (.png) showing trends of data_year1 vs data_year2.
        """
        import matplotlib.pyplot as plt # type: ignore

        output_dir = "media/writing/diagrams"
        os.makedirs(output_dir, exist_ok=True)

        plt.figure(figsize=(8, 6))
        plt.plot(categories, data_year1, marker="o", label=str(year1))
        plt.plot(categories, data_year2, marker="o", label=str(year2))

        plt.xlabel("Categories")
        plt.ylabel("Value")
        plt.title(f"Trend Comparison ({year1} vs {year2})")
        plt.legend()

        filename = os.path.join(output_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(filename)
        plt.close()

        return filename

    async def create_pie_chart(self, categories: List[str], year1: int, year2: int,
                         data_year1: List[float], data_year2: List[float]) -> str:
        """
        Create side-by-side pie charts for data_year1 and data_year2.
        """
        import matplotlib.pyplot as plt # type: ignore

        output_dir = "media/writing/diagrams"
        os.makedirs(output_dir, exist_ok=True)

        fig, axs = plt.subplots(1, 2, figsize=(12, 6))

        axs[0].pie(data_year1, labels=categories, autopct="%1.1f%%", startangle=140)
        axs[0].set_title(f"Distribution ({year1})")

        axs[1].pie(data_year2, labels=categories, autopct="%1.1f%%", startangle=140)
        axs[1].set_title(f"Distribution ({year2})")

        filename = os.path.join(output_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        plt.savefig(filename)
        plt.close()

        return filename

    async def generate_writing_part2_question(self) -> Dict:
        """
        Generate an IELTS Writing Task 2 question on common essay topics.
        Returns JSON with key: "task2_question": <string>.
        """
        prompt2 = """
Create an IELTS Writing Task 2 question. The question should be based on common essay topics
such as education, technology, the environment, healthcare, and other social issues.
Make a clear, thought-provoking statement requiring the test taker to discuss both sides of an argument and express their opinion.

Return exactly:
{ "task2_question": "<the question>" }
"""
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs valid JSON."},
                    {"role": "user", "content": prompt2.strip()},
                ],
                temperature=0.0,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error (generate writing part2): {e}")

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON returned from GPT for writing part2")

    async def analyse_writing(self, part1_answer: dict, part2_answer: str, lang_code: str = "en") -> dict:
        """
        Analyse IELTS Writing Task 1 and Task 2 responses.
        :param part1_answer: dict with keys "diagram_data" and "user_answer" for Task 1.
        :param part2_answer: str with the user's essay for Task 2.
        :param lang_code: Language code for feedback (default is "en" for English).
        :return: dict with analysis results in the expected JSON format.
        """
        analys_prompt = """
You are an expert IELTS examiner. Your task is to evaluate IELTS Writing Task 1 and Task 2 responses provided by a candidate.

Task 1 Evaluation Criteria:
- Task Achievement: Does the response address key points from the provided diagram accurately?
- Coherence and Cohesion: Are ideas logically organized and connected?
- Lexical Resource: Is a wide range of vocabulary used accurately?
- Grammatical Range and Accuracy: Are sentence structures varied and grammatical errors minimal?
- Word Count: Is the response within 150 words? Deduct or comment if not.

Task 2 Evaluation Criteria:
- Task Response: Does the essay fully address the task, presenting a clear position?
- Coherence and Cohesion: Are ideas logically sequenced and effectively linked?
- Lexical Resource: Is vocabulary diverse and appropriate?
- Grammatical Range and Accuracy: Are grammar and punctuation correct?
- Word Count: Is the essay within 250 words? Comment if under/over length.
- Timing Feedback: Was the response likely completed in time? Suggest improvements.

Return valid JSON with:
{
  "task1": {
    "task_achievement": {"score": <0-9>, "feedback": "<string>"},
    "coherence_and_cohesion": {"score": <0-9>, "feedback": "<string>"},
    "lexical_resource": {"score": <0-9>, "feedback": "<string>"},
    "grammatical_range_and_accuracy": {"score": <0-9>, "feedback": "<string>"},
    "word_count": {"score": <0-9>, "feedback": "<string>"}
  },
  "task2": {
    "task_response": {"score": <0-9>, "feedback": "<string>"},
    "coherence_and_cohesion": {"score": <0-9>, "feedback": "<string>"},
    "lexical_resource": {"score": <0-9>, "feedback": "<string>"},
    "grammatical_range_and_accuracy": {"score": <0-9>, "feedback": "<string>"},
    "word_count": {"score": <0-9>, "feedback": "<string>"},
    "timing": {"score": <0-9>, "feedback": "<string>"}
  },
  "overall_band_score": <0-9>
}
"""
        lang_map = {"en": "English", "ru": "Russian", "uz": "Uzbek"}
        language_name = lang_map.get(lang_code, "English")

        diagram_data = part1_answer.get("diagram_data", {})
        user1 = part1_answer.get("user_answer", "")
        user2 = part2_answer

        data_obj = {
            "diagram_data": diagram_data,
            "task1_answer": user1,
            "task2_answer": user2
        }

        prompt_with_lang = f"""
{analys_prompt.strip()}

Language for feedback: {language_name}.
Here is the data:
{json.dumps(data_obj)}
"""

        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs valid JSON."},
                    {"role": "user", "content": prompt_with_lang.strip()},
                ],
                temperature=0.0,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI API error (analyse writing): {e}")

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON returned from GPT for writing analysis")
