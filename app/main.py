from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.config.runtime import runtime
from app.schemas.incident import ApprovalRequest, IncidentCreate, IncidentState
from app.services.orchestrator import IncidentOrchestrator

from fastapi.middleware.cors import CORSMiddleware

runtime.ensure_state_dir()
orchestrator = IncidentOrchestrator(runtime.data_root, runtime.state_dir, runtime.qdrant_url, runtime.qdrant_api_key)
app = FastAPI(title="Closed-Loop Autonomous Data Incident Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": app.title, "docs": "/docs", "workflow": "DETECT -> INVESTIGATE -> FIX -> CONTROL -> SIMULATE -> VERIFY -> RISK -> APPROVE/AUTO -> DEPLOY -> VERIFY -> LEARN"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "data_root": str(runtime.data_root), "exasol_dsn": runtime.exasol_dsn, "memory": "qdrant+local-fallback"}


@app.get("/observability/report")
def observability_report() -> dict:
    return orchestrator.observability.report()


@app.post("/incidents", response_model=IncidentState)
def create_incident(request: IncidentCreate) -> IncidentState:
    return orchestrator.create(request)


@app.get("/incidents", response_model=list[IncidentState])
def list_incidents() -> list[IncidentState]:
    return orchestrator.repository.list()


@app.get("/incidents/{incident_id}", response_model=IncidentState)
def get_incident(incident_id: str) -> IncidentState:
    return _get(incident_id)


@app.post("/scenarios/{scenario_id}/inject", response_model=IncidentState)
def inject_scenario(scenario_id: str) -> IncidentState:
    try:
        return orchestrator.inject(scenario_id.upper())
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/scenarios")
def list_scenarios() -> list[dict[str, str]]:
    return orchestrator.observability.scenarios()


@app.post("/scenarios/reset")
def reset_scenarios() -> dict[str, str]:
    orchestrator.repository.clear()
    return {"status": "clean baseline restored"}


@app.post("/incidents/{incident_id}/investigate", response_model=IncidentState)
def investigate(incident_id: str) -> IncidentState:
    return orchestrator.investigate(_get(incident_id))


@app.post("/incidents/{incident_id}/remediate", response_model=IncidentState)
def remediate(incident_id: str) -> IncidentState:
    incident = _get(incident_id)
    return orchestrator.propose(incident)


@app.post("/incidents/{incident_id}/simulate", response_model=IncidentState)
def simulate(incident_id: str) -> IncidentState:
    return orchestrator.simulate(_get(incident_id))


@app.post("/incidents/{incident_id}/verify", response_model=IncidentState)
def verify(incident_id: str) -> IncidentState:
    return orchestrator.verify(_get(incident_id))


@app.post("/incidents/{incident_id}/run", response_model=IncidentState)
def run_workflow(incident_id: str, approved: bool = False) -> IncidentState:
    return orchestrator.run(_get(incident_id), approved=approved)


@app.post("/incidents/{incident_id}/approve", response_model=IncidentState)
def approve(incident_id: str, request: ApprovalRequest) -> IncidentState:
    return orchestrator.approve(_get(incident_id), request)


@app.post("/incidents/{incident_id}/deploy", response_model=IncidentState)
def deploy(incident_id: str, approved: bool = False) -> IncidentState:
    return orchestrator.deploy(_get(incident_id), approved=approved)


@app.post("/incidents/{incident_id}/rollback", response_model=IncidentState)
def rollback(incident_id: str) -> IncidentState:
    return orchestrator.rollback(_get(incident_id))


@app.get("/incidents/{incident_id}/timeline")
def timeline(incident_id: str) -> dict:
    incident = _get(incident_id)
    return {"incident_id": incident_id, "events": incident.timeline}


@app.get("/incidents/{incident_id}/risk")
def risk(incident_id: str) -> dict:
    incident = _get(incident_id)
    return {"incident_id": incident_id, "risk": incident.risk_assessment}


@app.get("/incidents/{incident_id}/simulation")
def simulation(incident_id: str) -> dict:
    incident = _get(incident_id)
    return {"incident_id": incident_id, "simulation": incident.simulation_result}


@app.get("/incidents/{incident_id}/lineage")
def lineage(incident_id: str) -> dict:
    incident = _get(incident_id)
    return {"incident_id": incident_id, "affected_table": incident.affected_table, "lineage": "Inspect data_lineage.csv or PostgreSQL data_lineage for downstream dependencies."}


def _get(incident_id: str) -> IncidentState:
    incident = orchestrator.repository.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
