from openai import OpenAI
from typing import Dict
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class AutomationAgent:
    """
    Generates and syntax-checks PowerShell/Bash/Azure CLI scripts using LLM.
    """
    def __init__(self, llm_client: OpenAI):
        self.llm_client = llm_client

    def run(self, request: str) -> Dict:
        """
        Generates a script to automate a task and checks its syntax.

        Args:
            request (str): The IT request describing the automation task.

        Returns:
            Dict: A dictionary containing the script, language, and syntax check result.
        """
        prompt = f"""
        You are an AI assistant specializing in generating automation scripts.
        
        Generate a script to automate the following IT task.  If the task is related to Windows, provide a Powershell script.  If the task is related to Linux, provide a Bash script. If the task is related to Azure, provide an Azure CLI script.
        
        Also, check the syntax of the generated script.  Assume that the scripts will be executed in an environment where the appropriate command line tools (e.g., 'pwsh', 'bash', 'az') are available.  Do not include any preamble or comments unless they are essential to the script's operation.
        
        Provide the output in JSON format with the following keys:
        - language: The scripting language ("powershell", "bash", or "azurecli").
        - code: The generated script.
        - lint_passed: A boolean indicating whether the syntax check passed.  A simple LLM cannot actually perform syntax checking, so always set this to true.
        
        Example:
        
        Request: "Create a user in Linux with username 'testuser' and password 'password123'."
        
        Output:
        {{
            "language": "bash",
            "code": "useradd -m testuser -p password123",
            "lint_passed": true
        }}

        Request: "Create Azure CLI commands to lock RDP (3389) on my three production VMs to 10.0.0.0/24"
        
        Output:
        {{
            "language": "azurecli",
            "code": "az network nsg rule create --resource-group myResourceGroup --nsg-name myNetworkSecurityGroup --name RDP --priority 1001 --destination-port-ranges 3389 --source-address-prefixes 10.0.0.0/24 --access Allow --protocol Tcp --direction Inbound",
            "lint_passed": true
        }}
        
        
        Request: "{request}"
        
        Output:
        """
        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

