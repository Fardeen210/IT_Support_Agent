from langgraph.graph import StateGraph, START, END 
from typing import Dict, Any, Literal, TypedDict, Optional
from langgraph.checkpoint.memory import MemorySaver

from app.agents import AGENT_REGISTRY

# --- NODE FUNCTIONS ---
class CoordinatorState(TypedDict):
    request: str
    require_approval: Optional[bool]
    plan: dict
    status: str
    results: dict
    error: Optional[str]
    retry_count: int

checkpointer = MemorySaver()



def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    coordinator = AGENT_REGISTRY["coordinator"]
    plan = coordinator.plan(state["request"], state.get("require_approval", False))
    # Defensive: fill keys if missing
    plan['agents'] = plan.get('agents', [])
    plan['steps'] = plan.get('steps', [])
    plan['summary'] = plan.get('summary', '')
    # Set status at top level
    status = "waiting_approval" if state.get("require_approval") else "active"
    state['status'] = status
    plan['require_approval'] = state.get("require_approval", False)
    plan['status'] = status
    state['plan'] = plan
    print("DEBUG: In plan_node, setting state['plan'] =", state['plan'])
    return state

def approval_pause_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pauses for external approval. No-op until /approve is called.
    """
    return state

def after_approval_pause_edge(state: Dict[str, Any]) -> Literal["run_agents_node", "merge_results_node"]:
    if state.get("status") == "rejected":
        return "merge_results_node"
    return "run_agents_node"

def run_agents_node(state: Dict[str, Any], config=None) -> Dict[str, Any]:
    plan = state.get("plan", {})
    print("DEBUG: Entering run_agents_node with plan:", plan)
    outputs: Dict[str, Any] = {}
    request = state.get("request", "")
    error = None

    print(f"Run Agents Node: Plan is {plan}") 

    for agent_name in plan.get("agents", []):
        key = agent_name.replace("Agent", "").lower()
        agent = AGENT_REGISTRY.get(key)
        try:
            outputs[key] = agent.run(request)
            print(f"Output from {key}: {outputs[key]}")  # Add this
        except Exception as exc:
            error = f"{agent_name} failed: {exc}"
            print(error)  # Add this
            return {
                **state,
                "error": error,
                "status": "failed"
            }

    return {
        **state,
        "results": outputs,
        "error": None,
        "status": "completed"
    }

def merge_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges outputs from all agents into a final structured response.
    """
    coordinator = AGENT_REGISTRY["coordinator"]
    merged = coordinator.merge_results(state.get("results", {}))
    return {**state, "results": merged}

# --- CONDITIONAL EDGE FUNCTIONS ---

def after_plan_edge(state: Dict[str, Any]) -> Literal["approval_pause_node", "run_agents_node"]:
    if state["status"] == "waiting_approval":
        return "approval_pause_node"
    return "run_agents_node"

def after_run_agents_edge(state: Dict[str, Any]) -> Literal["run_agents_node", "merge_results_node"]:
    if state.get("status") == "failed":
        return END
    if state.get("error") and "AutomationAgent" in str(state.get("error")) and state.get("retry_count", 0) < 2:
        return "run_agents_node"
    return "merge_results_node"

# --- GRAPH BUILDER ---

def build_coordinator_graph():
    builder = StateGraph(CoordinatorState)

    # Add nodes
    builder.add_node(plan_node)
    builder.add_node(approval_pause_node)
    builder.add_node(run_agents_node)  
    builder.add_node(merge_results_node)


    # Entry
    builder.add_edge(START, "plan_node")
    builder.add_edge("approval_pause_node", "run_agents_node")
    
    builder.add_conditional_edges("plan_node", after_plan_edge) 
    builder.add_conditional_edges("approval_pause_node", after_approval_pause_edge)
    builder.add_conditional_edges("run_agents_node", after_run_agents_edge)
    builder.add_edge("merge_results_node", END)

    return builder.compile(
        interrupt_before=["approval_pause_node"],
        checkpointer=checkpointer
    )

if __name__ == "__main__":
    graph = build_coordinator_graph()
    g = graph.get_graph().draw_mermaid_png()

    base_filename = "coordinator_graph"

    png_filename = f"{base_filename}.png"
    
    with open(png_filename, "wb") as f:
        f.write(g)
    print(f"Saved PNG diagram to {png_filename}")