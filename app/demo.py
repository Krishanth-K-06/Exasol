from __future__ import annotations

from pathlib import Path

from app.schemas.incident import ApprovalRequest
from app.services.orchestrator import IncidentOrchestrator


def main() -> None:
    state = Path(".local-state")
    workflow = IncidentOrchestrator(Path("/Users/admin/Downloads/autonomous_data_incident_platform"), state)
    incident = workflow.inject("SCN-02")
    print("=" * 60)
    print("AUTONOMOUS DATA INCIDENT AGENT")
    print("[1] DETECT      SCN-02 schema change")
    print("[2] INVESTIGATE pipeline logs, schema history, lineage, memory")
    result = workflow.run(incident)
    print(f"[3] ROOT CAUSE  {result.root_cause}")
    print(f"[4] CONTROL     {result.control_decision}")
    print(f"[5] SIMULATION  {result.simulation_result['status']}")
    print(f"[6] VERIFY      {result.verification_result.status}")
    print(f"[7] RISK        {result.risk_assessment.score} / {result.risk_assessment.level}")
    if result.status == "WAITING_APPROVAL":
        print("[8] APPROVAL    required; approving demo action")
        result = workflow.approve(result, ApprovalRequest(reviewer="demo", decision="APPROVE", reason="Demo approval"))
    print(f"[9] DEPLOY      {result.deployment_status}")
    print(f"[10] FINAL      {result.status}")
    print("[11] MEMORY     stored in local fallback and Qdrant when configured")
    print("=" * 60)


if __name__ == "__main__":
    main()
