from fastapi import APIRouter, HTTPException
from app.models import (
    ExecuteRequest,
    TaskResponse,
    PlanApprovalResponse,
    TaskStatusResponse,
)
from app.workflows.coordinator_graph import build_coordinator_graph, approval_pause_node
from uuid import uuid4
from typing import Dict, Any

router = APIRouter()
TASKS: Dict[str, Dict[str, Any]] = {}
PLANS: Dict[str, Dict[str, Any]] = {}


@router.post("/execute", response_model=TaskResponse)
async def execute(request: ExecuteRequest):
    task_id = str(uuid4())
    graph = build_coordinator_graph()
    context = {
        "task_id": task_id,
        "request": request.request,
        "require_approval": request.require_approval,
    }
    print(f"Context: {context}")
    
    updated_state = graph.invoke(context, config={"configurable": {"thread_id": task_id}})
    status = updated_state["status"]
    print(f"Status: {status}")

    if status == "waiting_approval":
        # Store in PLANS for approval
        PLANS[task_id] = updated_state
        TASKS[task_id] = {"status": status, "plan": updated_state.get("plan"), "request": request.request}
        return TaskResponse(
            task_id=task_id,
            status=status,
            result=updated_state.get("plan"),
        )
    else:
        # Completed—store in TASKS
        TASKS[task_id] = {
            "status": status,
            "result": updated_state.get("results"),
            "request": request.request
        }
        return TaskResponse(
            task_id=task_id,
            status=status,
            result=updated_state.get("results"),
        )

@router.post("/plans/{id}/approve", response_model=PlanApprovalResponse)
async def approve_plan(id: str):
    if id not in PLANS:
        raise HTTPException(status_code=404, detail="Plan not found")
    context = PLANS[id]
    context["status"] = "active"
    graph = build_coordinator_graph()
    # Resume from approval node
    print("DEBUG: Approving plan. Context keys:", context.keys())
    print("DEBUG: Plan in context:", context.get("plan"))
    updated_result_state = graph.invoke(None, config={"configurable": {"thread_id": id}})
    TASKS[id] = {
        "status": updated_result_state["status"],
        "result": updated_result_state.get("results"),
        "request": context["request"]
    }
    del PLANS[id]
    return PlanApprovalResponse(status=updated_result_state["status"])

@router.post("/plans/{id}/reject", response_model=PlanApprovalResponse)
async def reject_plan(id: str):
    if id not in PLANS:
        raise HTTPException(status_code=404, detail="Plan not found")
    TASKS[id] = {"status": "rejected"}
    del PLANS[id]
    return PlanApprovalResponse(status="rejected")

@router.get("/tasks/{id}", response_model=TaskStatusResponse)
async def get_task_status(id: str):
    if id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    task = TASKS[id]
    status = task.get("status")
    result = task.get("result", {}) or {}
    diagnosis = result.get("diagnosis")
    script = result.get("script")
    email_draft = result.get("email_draft")
    duration_seconds = result.get("duration_seconds")
    return TaskStatusResponse(
        task_id=id,
        status=status,
        diagnosis=diagnosis,
        script=script,
        email_draft=email_draft,
        duration_seconds=duration_seconds
    )
