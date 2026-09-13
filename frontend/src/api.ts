import type { IncidentState, ObservabilityReport, Scenario } from './types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Failed to fetch health')
  return res.json()
}

export async function fetchObservability(): Promise<ObservabilityReport> {
  const res = await fetch(`${API_BASE}/observability/report`)
  if (!res.ok) throw new Error('Failed to fetch observability report')
  return res.json()
}

export async function fetchScenarios(): Promise<Scenario[]> {
  const res = await fetch(`${API_BASE}/scenarios`)
  if (!res.ok) throw new Error('Failed to fetch scenarios')
  return res.json()
}

export async function resetScenarios(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/scenarios/reset`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to reset scenarios')
  return res.json()
}

export async function fetchIncidents(): Promise<IncidentState[]> {
  const res = await fetch(`${API_BASE}/incidents`)
  if (!res.ok) throw new Error('Failed to fetch incidents')
  return res.json()
}

export async function fetchIncident(incidentId: string): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}`)
  if (!res.ok) throw new Error(`Failed to fetch incident ${incidentId}`)
  return res.json()
}

export async function injectScenario(scenarioId: string): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/scenarios/${scenarioId}/inject`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to inject scenario ${scenarioId}`)
  return res.json()
}

export async function runWorkflow(incidentId: string, approved = false): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/run?approved=${approved}`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to run workflow for incident ${incidentId}`)
  return res.json()
}

export async function investigateIncident(incidentId: string): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/investigate`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to investigate incident ${incidentId}`)
  return res.json()
}

export async function remediateIncident(incidentId: string): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/remediate`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to remediate incident ${incidentId}`)
  return res.json()
}

export async function simulateIncident(incidentId: string): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/simulate`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to simulate incident ${incidentId}`)
  return res.json()
}

export async function verifyIncident(incidentId: string): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/verify`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to verify incident ${incidentId}`)
  return res.json()
}

export async function approveIncident(
  incidentId: string,
  decision: 'APPROVE' | 'REJECT',
  reviewer = 'Data Reliability Lead',
  reason = 'Approved based on sandbox verification and acceptable blast radius'
): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer, decision, reason }),
  })
  if (!res.ok) throw new Error(`Failed to ${decision.toLowerCase()} incident ${incidentId}`)
  return res.json()
}

export async function deployIncident(incidentId: string, approved = false): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/deploy?approved=${approved}`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to deploy incident ${incidentId}`)
  return res.json()
}

export async function rollbackIncident(incidentId: string): Promise<IncidentState> {
  const res = await fetch(`${API_BASE}/incidents/${incidentId}/rollback`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to rollback incident ${incidentId}`)
  return res.json()
}
