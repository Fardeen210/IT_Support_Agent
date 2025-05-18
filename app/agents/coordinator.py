import os
import json
import uuid
import time
from dotenv import load_dotenv
from typing import Dict, Any
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class CoordinatorAgent:
    def __init__(self, client: OpenAI):
        self.client = client

    def plan(self, request: str, require_approval: bool = False) -> Dict[str, Any]:
        """
        Generates an execution plan based on the input request using LLM.
        """
        prompt = f"""
        You are an AI assistant that analyzes IT requests and creates an execution plan.
        Analyze the following IT request and determine the necessary steps and agents required to fulfill the request.

        Agents available:
            DiagnosticAgent: Performs root-cause analysis and provides ranked fixes 
            AutomationAgent: Generates and syntax-checks PowerShell/Bash/Azure CLI scripts 
            WriterAgent: Transforms results into structured content (email, SOP, summary) 

        Request: "{request}"
        Require approval before execution: {require_approval}

        Output the plan in JSON with the following keys:
            "agents": A list of agent names (e.g., ["DiagnosticAgent", "AutomationAgent", "WriterAgent"]).
            "steps": A list of step descriptions (e.g., ["Generate NSG rules", "Pause for approval", "Generate rollback script"]).
            "summary": A short summary sentence.
        If approval is required, include a step such as "Pause and await approval" in the steps.

        Output in JSON format:
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)

        # Defensive: Ensure structure (these can be safely removed after validation)
        if "steps" not in parsed:
            parsed["steps"] = ["[LLM did not provide steps]"]
        if "summary" not in parsed:
            parsed["summary"] = "[LLM did not provide summary]"

        parsed["require_approval"] = require_approval
        parsed["status"] = "waiting_approval" if require_approval else "active"
        parsed["task_id"] = str(uuid.uuid4())
        return parsed

    def merge_results(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
    
        prompt = f"""
            You are an AI assistant that merges the outputs from multiple agents into a single, coherent response.

            Combine these results into the following structure:
            {{
                "status": "completed",
                "diagnosis": {{...}},
                "script": {{...}},
                "email_draft": "...",
                "duration_seconds": 42
            }}

        Agent Outputs:
        {json.dumps(agent_outputs, indent=2)}

        Output in JSON format:
        """
        start = time.perf_counter()
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        merged = json.loads(content)
        merged["duration_seconds"] = int(time.perf_counter() - start)

    # Defensive: Fill missing keys from agent_outputs if LLM skipped any
        merged.setdefault("diagnosis", agent_outputs.get("diagnostic"))
        merged.setdefault("script", agent_outputs.get("automation"))
        merged.setdefault("email_draft", agent_outputs.get("writer"))
        merged.setdefault("status", "completed")
    # (optionally log merged for debugging)
        print("Merged output:", merged)
        return merged

