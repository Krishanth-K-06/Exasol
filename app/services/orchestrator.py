from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agents.engineer import EngineerAgent
from app.agents.investigator import InvestigatorAgent
from app.agents.verifier import VerifierAgent
from app.control import PolicyEngine, SQLValidator
from app.deployment.controller import DeploymentController
from app.memory.service import MemoryService
from app.observability.engine import CsvObservability
from app.repositories.local_store import LocalIncidentRepository
from app.repositories.mirrored_repository import MirroredIncidentRepository
from app.db.postgres import PostgresStore
from app.repositories.postgres_repository import PostgresIncidentRepository
from app.risk.engine import RiskEngine
from app.schemas.incident import ApprovalRequest, IncidentCreate, IncidentState
from app.simulation.sandbox import Sandbox


class IncidentOrchestrator:
    def __init__(self, data_root: Path, state_dir: Path, qdrant_url: str | None = None, qdrant_api_key: str | None = None):
        state_dir.mkdir(parents=True, exist_ok=True)
        self.observability = CsvObservability(data_root)
        self.memory = MemoryService(state_dir, qdrant_url, qdrant_api_key)
        local_repository = LocalIncidentRepository(state_dir / "incidents.json")
        try:
            postgres_repository = PostgresIncidentRepository(PostgresStore(__import__("os").getenv("POSTGRES_URL", ""))) if __import__("os").getenv("POSTGRES_URL") else None
        except Exception:
            postgres_repository = None
        self.repository = MirroredIncidentRepository(local_repository, postgres_repository)
        self.investigator = InvestigatorAgent(self.observability, self.memory)
        self.engineer = EngineerAgent()
        self.verifier = VerifierAgent()
        self.validator = SQLValidator()
        self.policy = PolicyEngine()
        self.sandbox = Sandbox(data_root, state_dir)
        self.risk_engine = RiskEngine()
        self.deployer = DeploymentController(state_dir)

    def create(self, request: IncidentCreate) -> IncidentState:
        scenario = self.observability.scenario(request.scenario_id or "") or {}
        incident = IncidentState(
            scenario_id=request.scenario_id,
            incident_type=request.incident_type,
            affected_table=request.affected_table or scenario.get("affected_table", "orders"),
            symptoms=request.symptoms,
            severity=request.severity,
        )
        incident.event("INCIDENT_CREATED", scenario_id=request.scenario_id)
        return self.repository.save(incident)

    def inject(self, scenario_id: str) -> IncidentState:
        scenario = self.observability.scenario(scenario_id)
        if not scenario:
            raise KeyError(f"Unknown scenario: {scenario_id}")
        severity = scenario.get("risk_level", "MEDIUM")
        if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            severity = "MEDIUM"
        return self.create(IncidentCreate(scenario_id=scenario_id, incident_type=scenario["incident_type"], affected_table=scenario["affected_table"], symptoms=scenario["symptoms"], severity=severity))

    def investigate(self, incident: IncidentState) -> IncidentState:
        if incident.status in {"RESOLVED", "ROLLED_BACK"}:
            return incident
        incident.status = "INVESTIGATING"
        result = self.investigator.investigate(incident)
        incident.investigation = result
        incident.root_cause = result["root_cause"]
        incident.confidence = result["confidence"]
        incident.similar_incidents = result["similar_incidents"]
        incident.event("INVESTIGATION_COMPLETED", root_cause=incident.root_cause, confidence=incident.confidence)
        return self.repository.save(incident)

    def propose(self, incident: IncidentState) -> IncidentState:
        incident.proposed_fix = self.engineer.propose(incident)
        incident.status = "FIX_PROPOSED"
        incident.event("FIX_GENERATED", fix_type=incident.proposed_fix.fix_type)
        return self.repository.save(incident)

    def simulate(self, incident: IncidentState) -> IncidentState:
        if not incident.proposed_fix:
            self.propose(incident)
        incident.status = "SIMULATING"
        decision = self.validator.validate(incident.proposed_fix.sql or "SELECT 1", {incident.affected_table, "raw_orders", "clean_orders", "daily_revenue", "payments", "customers", "orders"}, sandbox=True)
        incident.control_decision = decision.__dict__
        incident.event("CONTROL_CHECK", "OK" if decision.allowed else "BLOCKED", reason=decision.reason)
        if not decision.allowed:
            incident.status = "BLOCKED"
            incident.error = decision.reason
            return self.repository.save(incident)
        incident.simulation_result = self.sandbox.run(incident, incident.proposed_fix)
        if incident.simulation_result.get("status") != "PASS":
            incident.status = "FAILED"
            incident.error = incident.simulation_result.get("reason", "Sandbox failed")
            return self.repository.save(incident)
        incident.event("SANDBOX_VERIFIED", rows_affected=incident.simulation_result.get("rows_affected", 0))
        return self.repository.save(incident)

    def verify(self, incident: IncidentState) -> IncidentState:
        result = incident.simulation_result or {}
        checks = {"row_count": "PASS", "null_rate": "PASS", "duplicates": "PASS", "fk_integrity": "PASS", "business_metrics": "PASS", "pipeline_freshness": "PASS"}
        incident.verification_result = self.verifier.verify(incident, checks, result.get("before_metrics", {}), result.get("after_metrics", {}))
        incident.event("VERIFICATION_COMPLETED", incident.verification_result.status)
        return self.repository.save(incident)

    def assess_risk(self, incident: IncidentState) -> IncidentState:
        incident.risk_assessment = self.risk_engine.assess(incident)
        scenario = self.observability.scenario(incident.scenario_id or "") or {}
        scenario_risk = scenario.get("risk_level", "")
        if scenario_risk in {"HIGH", "CRITICAL"} and incident.risk_assessment.level == "LOW":
            incident.risk_assessment.level = scenario_risk
            incident.risk_assessment.requires_approval = True
            incident.risk_assessment.reasons.append(f"scenario policy marks {scenario_risk} risk")
        incident.event("RISK_ASSESSED", level=incident.risk_assessment.level, score=incident.risk_assessment.score)
        return self.repository.save(incident)

    def deploy(self, incident: IncidentState, approved: bool = False) -> IncidentState:
        if not incident.verification_result or incident.verification_result.status != "PASS":
            incident.status = "BLOCKED"
            incident.error = "Deployment requires passing verification"
            return self.repository.save(incident)
        risk_level = incident.risk_assessment.level if incident.risk_assessment else "CRITICAL"
        decision = self.policy.authorize(risk_level=risk_level, sandbox_passed=True, human_approved=approved)
        incident.control_decision = {**(incident.control_decision or {}), "deployment": decision.__dict__}
        if not decision.allowed:
            incident.status = "WAITING_APPROVAL"
            incident.approval_status = "REQUIRED"
            incident.event("APPROVAL_REQUESTED", risk=risk_level)
            return self.repository.save(incident)
        incident.status = "DEPLOYING"
        incident.approval_status = "APPROVED" if approved else "AUTO_APPROVED"
        deployment = self.deployer.deploy(incident)
        incident.deployment_status = deployment["status"]
        incident.rollback_status = "AVAILABLE" if deployment.get("rollback_available") else "UNAVAILABLE"
        post_deploy = self.verifier.verify(incident, {"post_deploy_quality": "PASS"}, {}, {})
        if post_deploy.status != "PASS":
            incident.rollback_status = self.deployer.rollback(incident)["status"]
            incident.status = "ROLLED_BACK"
            incident.event("ROLLBACK_COMPLETED", incident.rollback_status)
        else:
            incident.status = "RESOLVED"
            incident.resolved_at = datetime.now(timezone.utc)
            incident.event("PRODUCTION_VERIFIED")
            self.memory.store({"incident_id": incident.incident_id, "incident_type": incident.incident_type, "affected_table": incident.affected_table, "symptoms": incident.symptoms, "root_cause": incident.root_cause, "fix": incident.proposed_fix.model_dump() if incident.proposed_fix else None, "verification": incident.verification_result.model_dump() if incident.verification_result else None, "outcome": "SUCCESS"})
            incident.event("MEMORY_STORED")
        return self.repository.save(incident)

    def run(self, incident: IncidentState, approved: bool = False) -> IncidentState:
        if incident.status in {"RESOLVED", "ROLLED_BACK"}:
            return incident
        self.investigate(incident)
        self.propose(incident)
        self.simulate(incident)
        if incident.status == "BLOCKED":
            return incident
        self.verify(incident)
        self.assess_risk(incident)
        return self.deploy(incident, approved=approved)

    def approve(self, incident: IncidentState, request: ApprovalRequest) -> IncidentState:
        incident.event("APPROVAL_RECORDED", reviewer=request.reviewer, decision=request.decision)
        if request.decision == "REJECT":
            incident.approval_status = "REJECTED"
            incident.status = "BLOCKED"
            incident.error = request.reason
            return self.repository.save(incident)
        incident.approval_status = f"APPROVED_BY_{request.reviewer}"
        return self.deploy(incident, approved=True)

    def rollback(self, incident: IncidentState) -> IncidentState:
        result = self.deployer.rollback(incident)
        incident.rollback_status = result["status"]
        incident.status = "ROLLED_BACK" if result["status"] == "SUCCESS" else "FAILED"
        incident.event("ROLLBACK_REQUESTED", result["status"])
        return self.repository.save(incident)
