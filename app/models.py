from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ExecuteRequest(BaseModel):
    request: str
    require_approval: bool = False

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None  # unified for both plan and result

class PlanApprovalResponse(BaseModel):
    status: str
    error: Optional[str] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    diagnosis: Optional[Dict[str, Any]] = None
    script: Optional[Dict[str, Any]] = None
    email_draft: Optional[str] = None
    duration_seconds: Optional[int] = None  # If you want to expose planning stage as well
