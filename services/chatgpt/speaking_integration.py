import json
from fastapi import HTTPException, status, UploadFile
from openai import AuthenticationError, BadRequestError, OpenAIError, RateLimitError
from .base_integration import BaseChatGPTIntegration

QUESTIONS_PROMPT = """
Create a set of IELTS Speaking test questions divided into 3 parts without any unnecessary notes. Please try to find relevant and updated IELTS questions:
In the first part, always ask for full name, address, work/education. Then you can create questions on 2 different topics. Ask 3-6 personal questions in total, such as likes/dislikes, free time, favorite things, etc.
Part 2 should consist of descriptive and three-point questions.
Part 3 should be argumentative questions. Create questions related to part 2. There should be a total of 3-6 questions.
Make sure the questions are relevant to the IELTS Speaking exam and focus on general, interrelated topics that test the student's fluency and consistency in English, and the total time should be 1-15 minutes per candidate.
"""

ANALYSE_PROMPT = """
You are an experienced IELTS examiner. Evaluate the following candidate's speaking responses based on the IELTS Speaking criteria:

Fluency and Coherence: Assess the flow of speech, logical structuring, and absence of unnatural pauses.
Lexical Resource: Evaluate the variety and appropriateness of vocabulary used.
Grammatical Range and Accuracy: Consider the grammatical structures used and their accuracy.
Pronunciation: Assess the clarity of pronunciation, stress, and intonation.
Please provide:

Individual scores (Band 1 to Band 9) for each criterion.
A detailed analysis explaining the strengths and weaknesses for each criterion.
A final overall band score (Band 1 to Band 9) based on the average of the individual scores.
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
            temperature=0.0,
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
        return json.loads(response.choices[0].message.content)

    async def transcribe_audio_file_async(self, audio: UploadFile, lang="en") -> str:
        """
        Asynchronously transcribe audio using OpenAI Whisper.
        """
        try:
            content = await audio.read()
            transcript = await self.async_client.audio.transcriptions.create(
                file=content,
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