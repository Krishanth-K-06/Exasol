from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.schemas.incident import IncidentState
from app.services.orchestrator import IncidentOrchestrator


class WorkflowState(TypedDict):
    incident: IncidentState
    approved: bool


def build_graph(workflow: IncidentOrchestrator):
    def run(state: WorkflowState) -> WorkflowState:
        state["incident"] = workflow.run(state["incident"], state.get("approved", False))
        return state

    graph = StateGraph(WorkflowState)
    graph.add_node("closed_loop", run)
    graph.add_edge(START, "closed_loop")
    graph.add_edge("closed_loop", END)
    return graph.compile()
