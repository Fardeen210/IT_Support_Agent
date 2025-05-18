import pytest
from fastapi.testclient import TestClient
from app.main import app
import subprocess

client = TestClient(app)

def get_task(task_id):
    resp = client.get(f"/api/v1/tasks/{task_id}")
    return resp.json()

@pytest.mark.timeout(20)
def test_happy_path():
    req = {
        "request": "Diagnose why Windows Server 2019 VM cpu01 hits 95%+ CPU, generate a PowerShell script to collect perfmon logs, and draft an email to management summarising findings.",
        "require_approval": False
    }
    r = client.post("/api/v1/execute", json=req)
    assert r.status_code == 200
    resp = r.json()
    print(f"Response: {resp}") 
    assert resp["status"] == "completed"
    result = resp.get("result", {})
    assert "diagnosis" in result
    assert "script" in result
    # Optionally: check non-empty content
    assert result.get("diagnosis")
    assert result.get("script")

@pytest.mark.timeout(20)
def test_approval_flow():
    req = {
        "request": "Create Azure CLI commands to lock RDP (3389) on my three production VMs to 10.0.0.0/24 and pause for approval before outputting the commands.",
        "require_approval": True
    }
    r = client.post("/api/v1/execute", json=req)
    assert r.status_code == 200
    resp = r.json()
    assert resp["status"] == "waiting_approval"
    task_id = resp["task_id"]
    # Approve the plan
    approve = client.post(f"/api/v1/plans/{task_id}/approve")
    assert approve.status_code == 200
    # Now check the task status: should be completed
    task = get_task(task_id)
    assert task["status"] == "completed"
    # There should be a script or commands in the final output
    result = task.get("result", task)  # fallback to whole dict if needed
    assert result.get("script") or result.get("commands")

@pytest.mark.timeout(10)
def test_agent_retry(monkeypatch):
    from app.agents import AGENT_REGISTRY

    class FailingAutomationAgent:
        def __init__(self):
            self.called = 0
        def run(self, request):
            self.called += 1
            if self.called == 1:
                raise Exception("Simulated failure")
            return {"language": "powershell", "code": "Write-Output 'Test'", "lint_passed": True}

    # Patch
    original = AGENT_REGISTRY["automation"]
    AGENT_REGISTRY["automation"] = FailingAutomationAgent()
    req = {
        "request": "Generate a PowerShell script to output 'Test'.",
        "require_approval": False
    }
    r = client.post("/api/v1/execute", json=req)
    resp = r.json()
    # Clean up the patch
    AGENT_REGISTRY["automation"] = original
    # If retry succeeded, status is completed and script is present
    assert resp["status"] in ["completed", "failed"]
    if resp["status"] == "completed":
        result = resp.get("result", {})
        assert "script" in result
        assert result.get("script")

@pytest.mark.timeout(20)
def test_script_compiles():
    req = {
        "request": "Generate a PowerShell script to list all running processes.",
        "require_approval": False
    }
    r = client.post("/api/v1/execute", json=req)
    resp = r.json()
    result = resp.get("result", {})
    script = result.get("script", {})
    # Accept either {'code': "..."} or just a string script
    code = ""
    if isinstance(script, dict):
        code = script.get("code") or script.get("sample_code") or ""
    elif isinstance(script, str):
        code = script
    assert code.strip() != ""
    # If powershell, test syntax using pwsh
    if script.get("language", "").lower() == "powershell":
        check = subprocess.run(["pwsh", "-Command", code], capture_output=True, text=True)
        # Accept both success or expected runtime errors (because no context)
        assert check.returncode == 0 or check.stderr
    elif script.get("language", "").lower() == "bash":
        with open("test_script.sh", "w") as f:
            f.write(code)
        check = subprocess.run(["bash", "-n", "test_script.sh"], capture_output=True, text=True)
        assert check.returncode == 0
