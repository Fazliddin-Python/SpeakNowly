import openai
from typing import Dict

class ChatGPTIntegration:
    def __init__(self, api_key: str):
        openai.api_key = api_key

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