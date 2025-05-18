from openai import OpenAI
from typing import Dict
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client (replace with your API key)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class DiagnosticAgent:
    """
    Performs root-cause analysis and provides ranked fixes using LLM.
    """
    def __init__(self, llm_client: OpenAI):
        self.llm_client = llm_client

    def run(self, request: str) -> Dict:
        """
        Performs root-cause analysis and suggests fixes using LLM.

        Args:
            request (str): The IT request describing the issue.

        Returns:
            Dict: A dictionary containing the root cause and suggested solutions.
        """
        prompt = f"""
        You are an AI assistant specializing in IT diagnostics.
        
        Analyze the following IT issue and provide a root cause analysis and ranked solutions.
        
        Provide the output in JSON format with the following keys:
        - root_cause: A string describing the most likely root cause.
        - evidence: A list of strings providing evidence for the root cause.
        - solutions: A list of dictionaries, where each dictionary has the keys "title" and "confidence".  "Confidence" should be one of "high", "medium", or "low".
        
        Example:
        
        Request: "Server CPU utilization is consistently above 90%."
        
        Output:
        {{
            "root_cause": "High CPU utilization is likely due to a runaway process or resource contention.",
            "evidence": ["perfmon shows high cpu usage by process X", "high iowait"],
            "solutions": [
                {{
                    "title": "Identify and terminate the runaway process.",
                    "confidence": "high"
                }},
                {{
                    "title": "Check for resource contention (e.g., memory, I/O).",
                    "confidence": "medium"
                }},
                {{
                    "title": "Update system drivers.",
                    "confidence": "low"
                }}
            ]
        }}
        
        Request: "{request}"
        
        Output:
        """
        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)