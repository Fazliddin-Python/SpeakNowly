import openai
from typing import Dict, List
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

class ChatGPTIntegration:
    """
    Integration with OpenAI ChatCompletion for evaluation tasks.
    """

    async def analyse_listening(self, system: str, user: str) -> str:
        """
        Send system/user prompts to ChatGPT and return raw content.

        :param system: System-level instructions for the model.
        :param user: User content containing answers or data to analyze.
        :return: Model's response content as string.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    async def analyse_writing(self, part1_answer: str, part2_answer: str) -> Dict:
        """
        Sends the user's answers to ChatGPT for Writing analysis.
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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"]

    async def analyse_speaking(self, part1_answer: str, part2_answer: str, part3_answer: str) -> Dict:
        """
        Sends the user's answers to ChatGPT for Speaking analysis.
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
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"]

async def transcribe_audio(audio_path: str) -> str:
    with open(audio_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript["text"]