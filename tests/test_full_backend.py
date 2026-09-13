from pathlib import Path

from app.schemas.incident import ApprovalRequest, IncidentCreate
from app.services.orchestrator import IncidentOrchestrator

DATA_ROOT = Path('/Users/admin/Downloads/autonomous_data_incident_platform')


def test_schema_change_requires_approval_then_resolves(tmp_path: Path):
    service = IncidentOrchestrator(DATA_ROOT, tmp_path)
    incident = service.run(service.inject('SCN-02'))
    assert incident.status == 'WAITING_APPROVAL'
    assert incident.risk_assessment.requires_approval is True
    resolved = service.approve(incident, ApprovalRequest(reviewer='pytest', decision='APPROVE', reason='approved'))
    assert resolved.status == 'RESOLVED'
    assert resolved.deployment_status == 'SUCCESS'
    assert resolved.rollback_status == 'AVAILABLE'


def test_null_explosion_auto_resolves(tmp_path: Path):
    service = IncidentOrchestrator(DATA_ROOT, tmp_path)
    incident = service.run(service.inject('SCN-03'))
    assert incident.status == 'RESOLVED'
    assert incident.verification_result.status == 'PASS'


def test_rejected_approval_blocks_deployment(tmp_path: Path):
    service = IncidentOrchestrator(DATA_ROOT, tmp_path)
    incident = service.run(service.inject('SCN-02'))
    rejected = service.approve(incident, ApprovalRequest(reviewer='pytest', decision='REJECT', reason='unsafe'))
    assert rejected.status == 'BLOCKED'
    assert rejected.deployment_status == 'NOT_STARTED'
