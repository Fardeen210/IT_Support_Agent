from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class WriterAgent:
    def __init__(self, llm_client: OpenAI):
        self.llm_client = llm_client

    def run(self, request: str) -> dict:
        prompt = f"""
        You are an AI assistant specializing in generating structured IT documentation, such as email drafts.
        Generate an email draft based on the following information. The email should be concise and informative, suitable for a technical audience. Do not include a salutation or signature.
        Output in JSON format:
        {{
            "email_draft": "<draft text here>"
        }}

        Request: "{request}"

        Output (in JSON):
        """
        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)