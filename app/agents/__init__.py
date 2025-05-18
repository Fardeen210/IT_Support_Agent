import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

from .coordinator import CoordinatorAgent
from .diagnostic import DiagnosticAgent
from .automation import AutomationAgent
from .writer import WriterAgent

# Register all agents in the app/agents directory

AGENT_REGISTRY = {
    "coordinator": CoordinatorAgent(client),
    "diagnostic": DiagnosticAgent(client),
    "automation": AutomationAgent(client),
    "writer": WriterAgent(client),
}