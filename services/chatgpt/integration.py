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
        try:
            with open(audio_path, "rb") as audio_file:
                transcript_response = await self.async_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenAI Whisper transcription error: {e}")

        # When response_format="text", transcript_response is already a string
        if isinstance(transcript_response, str):
            return transcript_response
        else:
            raise HTTPException(status_code=500, detail="Unexpected response format from Whisper transcription")


    # -----------------------
    #    Reading Methods
    # -----------------------

    async def generate_reading_data(self) -> Dict:
        """
        Generate an IELTS-style reading passage (100-150 words) along with three multiple-choice questions.
        Returns a dict with structure:
        {
          "passage_text": "<the passage>",
          "questions": [
            {
              "text": "<question text>",
              "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
              "correct_option": "B"
            },
            { ... }, { ... }
          ]
        }
        """
        prompt = """
You are an AI that generates IELTS-style reading passages and multiple-choice questions.
Produce:
1. A short reading passage of approximately 100-150 words.
2. Exactly three multiple-choice questions based on that passage.
Each question should have four options labeled "A)", "B)", "C)", "D)".
Indicate which option is correct.

Return exactly one JSON structure, without extra commentary:
{
  "passage_text": "<the 100-150 word passage>",
  "questions": [
    {
      "text": "<question 1 text>",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "A"
    },
    { ... },
    { ... }
  ]
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
            raise HTTPException(status_code=502, detail=f"OpenAI API error (generate reading data): {e}")

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON returned from GPT for reading data")

    async def analyse_reading_answers(self, passage_text: str, user_answers: List[str], correct_options: List[str]) -> Dict:
        """
        Analyze user's answers to the generated multiple-choice questions.
        :param passage_text: The original passage text.
        :param user_answers: List of answer letters e.g. ["A", "C", "B"].
        :param correct_options: List of correct answer letters e.g. ["A", "B", "D"].
        Returns a dict:
        {
          "score": <integer 0-3>,
          "detailed_feedback": [
            {"question_index": 0, "correct": true, "explanation": "<...>"},
            { ... },
            { ... }
          ]
        }
        """
        # Build a JSON payload that includes user answers and correct answers
        user_block = "\n".join(
            [f"Question {i+1}: user answered '{ua}', correct is '{ca}'"
             for i, (ua, ca) in enumerate(zip(user_answers, correct_options))]
        )
        prompt = f"""
You are an IELTS reading instructor. The passage was:

{passage_text}

The student answered three multiple-choice questions as follows:
{user_block}

Provide JSON with:
- "score": total correct count (0-3)
- "detailed_feedback": array of three objects, each:
    {{
      "question_index": <0-based index>,
      "correct": true/false,
      "explanation": "<brief explanation>"
    }}
Example:
{{
  "score": 2,
  "detailed_feedback": [
    {{"question_index": 0, "correct": true, "explanation": "Reason..."}},
    {{"question_index": 1, "correct": false, "explanation": "Reason..."}},
    {{"question_index": 2, "correct": true, "explanation": "Reason..."}}
  ]
}}
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
            raise HTTPException(status_code=502, detail=f"OpenAI API error (analyse reading answers): {e}")

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON returned from GPT for reading analysis")


    # -----------------------
    #    Writing Methods
    # -----------------------

    def generate_writing_part1_question(self) -> Dict:
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
            response = openai.ChatCompletion.create(
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

    def create_bar_chart(self, categories: List[str], year1: int, year2: int,
                         data_year1: List[float], data_year2: List[float]) -> str:
        """
        Create a bar chart (.png) comparing data_year1 vs data_year2 across categories.
        Saves under media/writing/diagrams and returns file path.
        """
        import matplotlib.pyplot as plt # type: ignore

        output_dir = "media/writing/diagrams"
        os.makedirs(output_dir, exist_ok=True)

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

    def create_line_chart(self, categories: List[str], year1: int, year2: int,
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

    def create_pie_chart(self, categories: List[str], year1: int, year2: int,
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

    def generate_writing_part2_question(self) -> Dict:
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
            response = openai.ChatCompletion.create(
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

    def analyse_writing(self, part1_answer: dict, part2_answer: str, lang_code: str = "en") -> Dict:
        """
        Analyze IELTS Writing Task 1 and Task 2 responses.
        part1_answer: dict with keys "diagram_data" and "user_answer"
        part2_answer: essay text string.
        lang_code: "en", "ru", or "uz" to specify output language.
        Returns a JSON dict with scores & feedback for each criterion and overall.
        """
        # Build combined prompt with analysis criteria
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
        # Map language code to language name
        lang_map = {"en": "English", "ru": "Russian", "uz": "Uzbek"}
        language_name = lang_map.get(lang_code, "English")

        # Prepare data to send to GPT
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
            response = openai.ChatCompletion.create(
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
