export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type IncidentStatus =
  | 'DETECTED'
  | 'INVESTIGATING'
  | 'FIX_PROPOSED'
  | 'SIMULATING'
  | 'WAITING_APPROVAL'
  | 'DEPLOYING'
  | 'RESOLVED'
  | 'ROLLED_BACK'
  | 'BLOCKED'
  | 'FAILED'

export interface Evidence {
  metric: string
  table?: string
  column?: string
  current_value?: string | number | null
  expected_value?: string | number | null
  status: 'PASS' | 'FAIL' | 'INFO'
  details: string
}

export interface FixProposal {
  fix_type: 'SQL' | 'PYTHON' | 'PIPELINE'
  sql?: string
  description: string
  expected_effect: string
  estimated_rows_affected: number
  rollback_strategy: string
  risk_factors: string[]
  idempotency_key: string
}

export interface VerificationResult {
  status: 'PASS' | 'FAIL'
  checks: Record<string, string>
  before_metrics: Record<string, any>
  after_metrics: Record<string, any>
  failures: string[]
}

export interface RiskAssessment {
  score: number
  level: Severity
  reasons: string[]
  requires_approval: boolean
  rollback_available: boolean
}

export interface TimelineEvent {
  timestamp: string
  action: string
  result: string
  metadata?: Record<string, any>
}

export interface IncidentState {
  incident_id: string
  scenario_id?: string
  incident_type: string
  severity: Severity
  affected_table: string
  symptoms: string
  evidence: Evidence[]
  detected_at: string
  resolved_at?: string | null
  status: IncidentStatus
  investigation?: {
    root_cause?: string
    confidence?: number
    evidence?: any[]
    similar_incidents?: any[]
    investigation_path?: string
    recommended_action?: string
  }
  root_cause?: string | null
  confidence: number
  similar_incidents: any[]
  proposed_fix?: FixProposal | null
  control_decision?: Record<string, any> | null
  simulation_result?: {
    status?: string
    blast_radius?: string
    rows_affected?: number
    delta?: Record<string, any>
    before_metrics?: Record<string, any>
    after_metrics?: Record<string, any>
    reason?: string
  } | null
  verification_result?: VerificationResult | null
  risk_assessment?: RiskAssessment | null
  approval_status: string
  deployment_status: string
  rollback_status: string
  timeline: TimelineEvent[]
  error?: string | null
}

export interface Scenario {
  scenario_id: string
  incident_type: string
  affected_table: string
  symptoms: string
  risk_level?: string
  expected_fix?: string
}

export interface ObservabilityReport {
  checks: Evidence[]
  failed: number
}
