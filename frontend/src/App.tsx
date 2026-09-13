import React from 'react'
import {
  Activity, AlertTriangle, CheckCircle2, Clock, Code2, Cpu,
  GitBranch, Play, RefreshCw, RotateCcw, Search, Shield,
  Sparkles, Terminal, UserCheck, Zap, ChevronRight, Database,
  Eye, TrendingUp, ArrowRight, XCircle, Layers
} from 'lucide-react'
import {
  fetchIncidents, fetchIncident, fetchScenarios, fetchObservability,
  injectScenario, runWorkflow, approveIncident, rollbackIncident,
  resetScenarios, investigateIncident, remediateIncident,
  simulateIncident, verifyIncident,
} from './api'
import type { IncidentState, Scenario, ObservabilityReport } from './types'

// ── Helpers ────────────────────────────────────────────────────
const STATUS_ORDER = [
  'DETECTED', 'INVESTIGATING', 'FIX_PROPOSED', 'SIMULATING',
  'WAITING_APPROVAL', 'DEPLOYING', 'RESOLVED', 'ROLLED_BACK', 'FAILED'
]

function statusIndex(s: string) {
  const i = STATUS_ORDER.indexOf(s)
  return i === -1 ? 0 : i
}

function severityColor(sev: string) {
  if (sev === 'CRITICAL') return '#ffffff'
  if (sev === 'HIGH') return '#c0c0c0'
  if (sev === 'MEDIUM') return '#808080'
  return '#555555'
}

function statusPill(status: string) {
  if (status === 'RESOLVED') return 'pill pill-dim'
  if (status === 'WAITING_APPROVAL') return 'pill pill-active'
  if (status === 'DETECTED' || status === 'INVESTIGATING') return 'pill pill-white'
  if (status === 'FAILED' || status === 'ROLLED_BACK') return 'pill pill-dim'
  return 'pill pill-white'
}

function fmt(ts: string) {
  return new Date(ts).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const PIPELINE_STEPS = [
  { key: 'DETECTED', label: 'DETECT', icon: <Eye size={12} /> },
  { key: 'INVESTIGATING', label: 'INVEST', icon: <Search size={12} /> },
  { key: 'FIX_PROPOSED', label: 'FIX', icon: <Code2 size={12} /> },
  { key: 'SIMULATING', label: 'SIM', icon: <Cpu size={12} /> },
  { key: 'WAITING_APPROVAL', label: 'APPROVE', icon: <UserCheck size={12} /> },
  { key: 'DEPLOYING', label: 'DEPLOY', icon: <GitBranch size={12} /> },
  { key: 'RESOLVED', label: 'DONE', icon: <CheckCircle2 size={12} /> },
]

// ── Sub-components ─────────────────────────────────────────────

function LiveDot() {
  return (
    <span className="live-dot" aria-label="live">
      <span />
    </span>
  )
}

function MetricCard({
  value, label, sub, progress, delay = 0
}: { value: string | number, label: string, sub?: string, progress?: number, delay?: number }) {
  return (
    <div className="metric-card" style={{ animationDelay: `${delay}ms` }}>
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
      {sub && <div className="metric-trend">{sub}</div>}
      {progress !== undefined && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ '--progress-width': `${progress}%` } as React.CSSProperties}
          />
        </div>
      )}
    </div>
  )
}

function PipelineBar({ status }: { status: string }) {
  const curIdx = statusIndex(status)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0, position: 'relative', padding: '0 4px' }}>
      {/* connector line */}
      <div style={{
        position: 'absolute', top: 15, left: 20, right: 20,
        height: 1, background: 'var(--border-1)', zIndex: 0
      }} />
      {PIPELINE_STEPS.map((step, idx) => {
        const done = idx < curIdx || status === 'RESOLVED'
        const current = step.key === status
        return (
          <div key={step.key} className={`pipeline-step ${done ? 'done' : ''} ${current ? 'current' : ''}`}>
            <div className="pipeline-step-icon">
              <span style={{ color: done || current ? 'white' : 'var(--text-3)' }}>
                {done && !current ? <CheckCircle2 size={10} /> : step.icon}
              </span>
            </div>
            <span className="pipeline-step-label">{step.label}</span>
          </div>
        )
      })}
    </div>
  )
}

function IncidentRow({
  inc, selected, onClick
}: { inc: IncidentState, selected: boolean, onClick: () => void }) {
  return (
    <div className={`incident-row ${selected ? 'selected' : ''}`} onClick={onClick}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: 'var(--text-0)' }}>
          {inc.scenario_id || inc.incident_type}
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700,
          color: severityColor(inc.severity), letterSpacing: '0.06em'
        }}>
          {inc.severity}
        </span>
      </div>
      <p style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 8, lineHeight: 1.4 }}
        className="truncate">{inc.symptoms}</p>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
          {inc.affected_table}
        </span>
        <span className={statusPill(inc.status)}>{inc.status}</span>
      </div>
    </div>
  )
}

function TimelinePanel({ incident }: { incident: IncidentState }) {
  const events = [...incident.timeline].reverse()
  return (
    <div className="detail-card" style={{ height: '100%' }}>
      <div className="detail-card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Clock size={14} style={{ color: 'var(--text-3)' }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-2)' }}>
            Audit Timeline
          </span>
        </div>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
          {incident.timeline.length} events
        </span>
      </div>
      <div className="detail-card-body" style={{ maxHeight: 320, overflowY: 'auto' }}>
        <div style={{ paddingTop: 4 }}>
          {events.map((ev, i) => (
            <div key={i} className="timeline-item" style={{ animationDelay: `${i * 40}ms` }}>
              <div className={`timeline-dot ${i === 0 ? 'active' : ''}`}>
                {i === 0 && <div style={{ width: 4, height: 4, borderRadius: '50%', background: 'white' }} />}
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 8 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11, color: 'var(--text-0)' }}>
                  {ev.action}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-3)', flexShrink: 0 }}>
                  {fmt(ev.timestamp)}
                </span>
              </div>
              <div style={{ marginTop: 3, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 10,
                  padding: '1px 6px', borderRadius: 3,
                  background: ev.result === 'OK' ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-1)',
                  color: ev.result === 'OK' ? 'var(--text-1)' : 'var(--text-3)',
                }}>
                  {ev.result}
                </span>
                {ev.metadata && Object.keys(ev.metadata).length > 0 && (
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
                    {JSON.stringify(ev.metadata)}
                  </span>
                )}
              </div>
            </div>
          ))}
          {events.length === 0 && (
            <p style={{ color: 'var(--text-3)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
              No events yet
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Main App ────────────────────────────────────────────────────
export default function App() {
  const [incidents, setIncidents] = React.useState<IncidentState[]>([])
  const [selectedIncident, setSelectedIncident] = React.useState<IncidentState | null>(null)
  const [scenarios, setScenarios] = React.useState<Scenario[]>([])
  const [observability, setObservability] = React.useState<ObservabilityReport | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [loadError, setLoadError] = React.useState<string | null>(null)
  const [actionLoading, setActionLoading] = React.useState<string | null>(null)
  const [activeTab, setActiveTab] = React.useState<'overview' | 'scenarios' | 'observability'>('overview')
  const [statusFilter, setStatusFilter] = React.useState('ALL')
  const [lastRefresh, setLastRefresh] = React.useState(new Date())

  const loadData = React.useCallback(async () => {
    try {
      const [incList, scnList, obs] = await Promise.all([
        fetchIncidents(), fetchScenarios(), fetchObservability(),
      ])
      setLoadError(null)
      setIncidents(incList)
      setScenarios(scnList)
      setObservability(obs)
      setLastRefresh(new Date())
      setLoading(false)
      setSelectedIncident(current => {
        if (incList.length === 0) return null
        if (!current) return incList[0]
        return incList.find(i => i.incident_id === current.incident_id) ?? current
      })
    } catch (err) {
      console.error('Load error:', err)
      setLoadError('Unable to reach the incident control plane. Check the API and retry.')
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
  }, [loadData])

  const handleSelectIncident = async (id: string) => {
    try {
      const d = await fetchIncident(id)
      setSelectedIncident(d)
    } catch (e) { console.error(e) }
  }

  const withLoading = async (key: string, fn: () => Promise<IncidentState | void>) => {
    setActionLoading(key)
    try {
      const result = await fn()
      if (result) setSelectedIncident(result)
      await loadData()
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : 'The requested action failed.')
    } finally {
      setActionLoading(null)
    }
  }

  const busy = actionLoading !== null

  // Stats
  const totalIncidents = incidents.length
  const activeCount = incidents.filter(i => !['RESOLVED', 'ROLLED_BACK'].includes(i.status)).length
  const resolvedCount = incidents.filter(i => i.status === 'RESOLVED').length
  const waitingCount = incidents.filter(i => i.status === 'WAITING_APPROVAL').length
  const resolvedPct = totalIncidents > 0 ? Math.round((resolvedCount / totalIncidents) * 100) : 0

  const filteredIncidents = incidents.filter(i => {
    if (statusFilter === 'ALL') return true
    if (statusFilter === 'ACTIVE') return !['RESOLVED', 'ROLLED_BACK'].includes(i.status)
    if (statusFilter === 'WAITING') return i.status === 'WAITING_APPROVAL'
    if (statusFilter === 'RESOLVED') return i.status === 'RESOLVED'
    return true
  })

  return (
    <div className="grid-bg app-shell" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 1 }}>

      {/* ── TOPBAR ── */}
      <header className="topbar" style={{
        position: 'sticky', top: 0, zIndex: 50,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 24px', height: 52,
        background: 'rgba(0,0,0,0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border-1)',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 30, height: 30,
            borderRadius: 8,
            background: 'white',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Sparkles size={15} color="black" strokeWidth={2.5} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: '-0.01em', color: 'white' }}>
                Aegis Incident Agent
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-3)',
                border: '1px solid var(--border-1)', padding: '1px 5px', borderRadius: 3
              }}>v1.0</span>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)', marginTop: 1 }}>
              Exasol · Postgres · Qdrant · Closed-Loop Autonomous
            </div>
          </div>
        </div>

        {/* Center Nav */}
        <div style={{ display: 'flex', gap: 2, background: 'var(--bg-2)', padding: 3, borderRadius: 8, border: '1px solid var(--border-1)' }}>
          {(['overview', 'scenarios', 'observability'] as const).map(tab => (
            <button key={tab} className={`nav-tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
              {tab === 'overview' && <><Activity size={12} style={{ display: 'inline', marginRight: 5 }} />Incidents</>}
              {tab === 'scenarios' && <><Layers size={12} style={{ display: 'inline', marginRight: 5 }} />Scenarios</>}
              {tab === 'observability' && <><Eye size={12} style={{ display: 'inline', marginRight: 5 }} />Observability</>}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
            <LiveDot />
            <span>LIVE · {lastRefresh.toLocaleTimeString('en-US', { hour12: false })}</span>
          </div>
          <button
            className="btn-primary"
            onClick={() => withLoading('inject-SCN-02', () => injectScenario('SCN-02'))}
            disabled={busy}
          >
            <Zap size={12} strokeWidth={3} />
            Hero Demo (SCN-02)
          </button>
          <button
            className="btn-ghost"
            onClick={async () => {
              if (confirm('Reset to clean baseline?')) {
                await withLoading('reset', async () => {
                  await resetScenarios()
                  setSelectedIncident(null)
                })
              }
            }}
            disabled={busy}
          >
            <RotateCcw size={12} />
            Reset
          </button>
        </div>
      </header>

      {/* ── TICKER STATUS BAR ── */}
      <div style={{
        background: 'var(--bg-1)',
        borderBottom: '1px solid var(--border-0)',
        padding: '0 24px',
        height: 34,
        display: 'flex',
        alignItems: 'center',
        gap: 32,
        overflow: 'hidden',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24, fontFamily: 'var(--font-mono)', fontSize: 10, flexShrink: 0 }}>
          {[
            { label: 'TOTAL', val: totalIncidents, highlight: false },
            { label: 'ACTIVE LOOP', val: activeCount, highlight: activeCount > 0 },
            { label: 'AWAITING APPROVAL', val: waitingCount, highlight: waitingCount > 0 },
            { label: 'RESOLVED', val: resolvedCount, highlight: false },
          ].map(m => (
            <div key={m.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: 'var(--text-3)' }}>{m.label}</span>
              <span style={{
                fontWeight: 800, fontSize: 12,
                color: m.highlight ? 'white' : 'var(--text-2)',
              }}>{m.val}</span>
            </div>
          ))}
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 16, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <Shield size={10} />
            <span>CONTROL LAYER: ACTIVE</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <Database size={10} />
            <span>SANDBOX: ENFORCED</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <Terminal size={10} />
            <span>AGENTS: DETERMINISTIC</span>
          </div>
        </div>
      </div>

      {loadError && (
        <div className="system-alert" role="alert">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={14} />
            <span>{loadError}</span>
          </div>
          <button className="btn-ghost" onClick={loadData} disabled={busy}>
            <RefreshCw size={12} /> Retry
          </button>
        </div>
      )}

      {/* ── CONTENT ── */}
      <main className="main-content" style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative', zIndex: 1 }}>

        {/* ═══ OVERVIEW TAB ═══ */}
        {activeTab === 'overview' && (
          <div className="overview-layout" style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

            {/* Left sidebar */}
            <aside className="incident-sidebar" style={{
              width: 300,
              borderRight: '1px solid var(--border-1)',
              display: 'flex',
              flexDirection: 'column',
              background: 'var(--bg-1)',
              overflow: 'hidden',
            }}>
              {/* Metric row */}
              <div style={{ padding: '14px 14px 0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <MetricCard value={activeCount} label="Active" sub="in pipeline" delay={0} />
                <MetricCard value={waitingCount} label="Approval" sub="pending review" delay={50} progress={waitingCount > 0 ? 100 : 0} />
              </div>

              {/* Filter */}
              <div style={{ padding: '12px 14px 8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-3)' }}>
                  Incident Feed
                </span>
                <select
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                  style={{
                    background: 'var(--bg-3)', border: '1px solid var(--border-1)', borderRadius: 5,
                    color: 'var(--text-2)', fontFamily: 'var(--font-mono)', fontSize: 10, padding: '3px 8px',
                    cursor: 'pointer', outline: 'none',
                  }}
                >
                  <option value="ALL">All</option>
                  <option value="ACTIVE">Active</option>
                  <option value="WAITING">Waiting</option>
                  <option value="RESOLVED">Resolved</option>
                </select>
              </div>

              {/* List */}
              <div style={{ flex: 1, overflowY: 'auto' }}>
                {loading ? (
                  <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {[1, 2, 3].map(i => (
                      <div key={i} className="skeleton" style={{ height: 72, borderRadius: 8 }} />
                    ))}
                  </div>
                ) : filteredIncidents.length === 0 ? (
                  <div style={{ padding: 24, textAlign: 'center' }}>
                    <Activity size={28} style={{ color: 'var(--text-4)', margin: '0 auto 10px' }} />
                    <p style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 12 }}>No incidents</p>
                    <button className="btn-primary" style={{ fontSize: 11, padding: '6px 14px' }}
                      onClick={() => withLoading('inject-SCN-02', () => injectScenario('SCN-02'))}>
                      <Zap size={11} /> Inject SCN-02
                    </button>
                  </div>
                ) : (
                  filteredIncidents.map(inc => (
                    <IncidentRow
                      key={inc.incident_id}
                      inc={inc}
                      selected={selectedIncident?.incident_id === inc.incident_id}
                      onClick={() => handleSelectIncident(inc.incident_id)}
                    />
                  ))
                )}
              </div>
            </aside>

            {/* Detail Panel */}
            {selectedIncident ? (
              <section className="incident-detail" style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 18 }}>

                {/* Hero card */}
                <div style={{
                  position: 'relative',
                  border: '1px solid var(--border-2)',
                  borderRadius: 'var(--radius-xl)',
                  background: 'var(--bg-2)',
                  padding: '24px 28px',
                  overflow: 'hidden',
                  animation: 'fade-in 0.4s ease',
                }}>
                  {/* top shimmer */}
                  <div style={{
                    position: 'absolute', top: 0, left: 0, right: 0, height: 1,
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent)'
                  }} />
                  {/* background glow */}
                  <div style={{
                    position: 'absolute', top: -60, right: -60,
                    width: 200, height: 200, borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%)',
                    pointerEvents: 'none'
                  }} />

                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
                          {selectedIncident.incident_id.slice(0, 16)}…
                        </span>
                        <ChevronRight size={10} style={{ color: 'var(--text-4)' }} />
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
                          {selectedIncident.affected_table}
                        </span>
                        <span className={statusPill(selectedIncident.status)}>
                          {selectedIncident.status}
                        </span>
                      </div>
                      <h2 style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', color: 'white', lineHeight: 1.2, marginBottom: 8 }}>
                        {selectedIncident.scenario_id
                          ? `${selectedIncident.scenario_id} — ${selectedIncident.incident_type}`
                          : selectedIncident.incident_type}
                      </h2>
                      <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6, maxWidth: 600 }}>
                        {selectedIncident.symptoms}
                      </p>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8, flexShrink: 0 }}>
                      <button
                        className="btn-primary"
                        onClick={() => withLoading('run-all', () => runWorkflow(selectedIncident.incident_id))}
                        disabled={busy || selectedIncident.status === 'RESOLVED'}
                      >
                        {actionLoading === 'run-all'
                          ? <RefreshCw size={13} className="animate-spin" />
                          : <Play size={13} strokeWidth={3} />}
                        Run Autonomous Cycle
                      </button>
                      {selectedIncident.rollback_status === 'AVAILABLE' && (
                        <button
                          className="btn-ghost"
                          style={{ borderColor: 'rgba(255,80,80,0.3)', color: '#ff7070' }}
                          onClick={() => withLoading('rollback', () => rollbackIncident(selectedIncident.incident_id))}
                          disabled={busy}
                        >
                          <RotateCcw size={12} /> Safe Rollback
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Pipeline bar */}
                  <div style={{ marginTop: 22, paddingTop: 18, borderTop: '1px solid var(--border-0)' }}>
                    <PipelineBar status={selectedIncident.status} />
                  </div>

                  {/* Step-by-step controls */}
                  <div style={{ marginTop: 16, display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)', marginRight: 4 }}>
                      STEP-BY-STEP:
                    </span>
                    {[
                      { label: '① Investigate', key: 'investigate', fn: () => investigateIncident(selectedIncident.incident_id), icon: <Search size={11} /> },
                      { label: '② Propose Fix', key: 'remediate', fn: () => remediateIncident(selectedIncident.incident_id), icon: <Code2 size={11} /> },
                      { label: '③ Simulate', key: 'simulate', fn: () => simulateIncident(selectedIncident.incident_id), icon: <Cpu size={11} /> },
                      { label: '④ Verify & Risk', key: 'verify', fn: () => verifyIncident(selectedIncident.incident_id), icon: <Shield size={11} /> },
                    ].map(s => (
                      <button key={s.key} className="step-btn"
                        onClick={() => withLoading(`step-${s.key}`, s.fn)}
                        disabled={busy || selectedIncident.status === 'RESOLVED'}>
                        {actionLoading === `step-${s.key}` ? <RefreshCw size={11} /> : s.icon}
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Approval banner */}
                {selectedIncident.status === 'WAITING_APPROVAL' && (
                  <div className="approval-banner" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20 }}>
                    <div style={{ position: 'relative', zIndex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                        <Shield size={16} style={{ color: 'white' }} />
                        <span style={{ fontWeight: 700, fontSize: 13, letterSpacing: '0.02em' }}>
                          HUMAN APPROVAL REQUIRED
                        </span>
                        <LiveDot />
                      </div>
                      <p style={{ fontSize: 12, color: 'var(--text-2)' }}>
                        Risk engine scored this fix as HIGH/CRITICAL. Sandbox verification passed. Authorize to deploy to production.
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: 10, position: 'relative', zIndex: 1, flexShrink: 0 }}>
                      <button className="btn-ghost"
                        onClick={() => withLoading('reject', () => approveIncident(selectedIncident.incident_id, 'REJECT'))}
                        disabled={busy}>
                        <XCircle size={13} /> Reject
                      </button>
                      <button className="btn-primary"
                        onClick={() => withLoading('approve', () => approveIncident(selectedIncident.incident_id, 'APPROVE'))}
                        disabled={busy}>
                        <UserCheck size={13} /> Authorize Deploy
                      </button>
                    </div>
                  </div>
                )}

                {/* 2x2 Agent Cards */}
                <div className="agent-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>

                  {/* Investigator */}
                  <div className="detail-card anim-delay-1">
                    <div className="detail-card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Search size={13} style={{ color: 'var(--text-3)' }} />
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-2)' }}>
                          Investigator Agent
                        </span>
                      </div>
                      {selectedIncident.confidence > 0 && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, padding: '2px 8px', borderRadius: 4, border: '1px solid var(--border-1)', color: 'var(--text-1)' }}>
                          {(selectedIncident.confidence * 100).toFixed(0)}% confidence
                        </span>
                      )}
                    </div>
                    <div className="detail-card-body">
                      <div style={{ marginBottom: 14 }}>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 6 }}>
                          Root Cause
                        </div>
                        <p style={{ fontSize: 12, color: selectedIncident.root_cause ? 'var(--text-0)' : 'var(--text-3)', fontStyle: selectedIncident.root_cause ? 'normal' : 'italic', lineHeight: 1.5 }}>
                          {selectedIncident.root_cause || 'Awaiting investigation…'}
                        </p>
                      </div>
                      {selectedIncident.evidence.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 2 }}>
                            Evidence
                          </div>
                          {selectedIncident.evidence.slice(0, 4).map((ev, i) => (
                            <div key={i} className="evidence-row" style={{ animationDelay: `${i * 50}ms` }}>
                              <span style={{ color: 'var(--text-1)' }}>{ev.metric}</span>
                              <span style={{
                                fontWeight: 700,
                                color: ev.status === 'FAIL' ? 'white' : 'var(--text-3)',
                                padding: '1px 6px', borderRadius: 3,
                                background: ev.status === 'FAIL' ? 'rgba(255,255,255,0.1)' : 'transparent',
                                border: ev.status === 'FAIL' ? '1px solid rgba(255,255,255,0.2)' : 'none',
                              }}>
                                {ev.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Engineer */}
                  <div className="detail-card anim-delay-2">
                    <div className="detail-card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Code2 size={13} style={{ color: 'var(--text-3)' }} />
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-2)' }}>
                          Engineer Agent
                        </span>
                      </div>
                      {selectedIncident.proposed_fix && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 4, background: 'white', color: 'black' }}>
                          {selectedIncident.proposed_fix.fix_type}
                        </span>
                      )}
                    </div>
                    <div className="detail-card-body">
                      {selectedIncident.proposed_fix ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                          <p style={{ fontSize: 12, color: 'var(--text-1)', lineHeight: 1.5 }}>
                            {selectedIncident.proposed_fix.description}
                          </p>
                          {selectedIncident.proposed_fix.sql && (
                            <div className="code-block">
                              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                                {selectedIncident.proposed_fix.sql}
                              </pre>
                            </div>
                          )}
                          <div style={{ display: 'flex', gap: 10, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
                            <span>Rollback: {selectedIncident.proposed_fix.rollback_strategy}</span>
                          </div>
                        </div>
                      ) : (
                        <p style={{ fontSize: 12, color: 'var(--text-3)', fontStyle: 'italic' }}>
                          No fix proposed yet. Run the workflow or click Propose Fix.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Simulation */}
                  <div className="detail-card anim-delay-3">
                    <div className="detail-card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Cpu size={13} style={{ color: 'var(--text-3)' }} />
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-2)' }}>
                          Sandbox Simulation
                        </span>
                      </div>
                      {selectedIncident.simulation_result?.status && (
                        <span style={{
                          fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700,
                          padding: '2px 8px', borderRadius: 4,
                          border: '1px solid var(--border-2)', color: 'var(--text-0)'
                        }}>
                          {selectedIncident.simulation_result.status}
                        </span>
                      )}
                    </div>
                    <div className="detail-card-body">
                      {selectedIncident.simulation_result ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {[
                            { k: 'ROWS AFFECTED', v: selectedIncident.simulation_result.rows_affected ?? 0 },
                            { k: 'BLAST RADIUS', v: selectedIncident.simulation_result.blast_radius || 'LOW' },
                          ].map(r => (
                            <div key={r.k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border-0)' }}>
                              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>{r.k}</span>
                              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: 'var(--text-0)' }}>{r.v}</span>
                            </div>
                          ))}
                          {selectedIncident.verification_result?.checks && (
                            <div>
                              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)', marginBottom: 8 }}>DETERMINISTIC CHECKS</div>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                                {Object.entries(selectedIncident.verification_result.checks).map(([k, v]) => (
                                  <div key={k} className="evidence-row">
                                    <span style={{ color: 'var(--text-2)' }}>{k}</span>
                                    <span style={{ fontWeight: 700, color: v === 'PASS' ? 'var(--text-1)' : 'white' }}>{v}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p style={{ fontSize: 12, color: 'var(--text-3)', fontStyle: 'italic' }}>
                          Fix not yet simulated in isolated SQLite sandbox.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Risk Engine */}
                  <div className="detail-card anim-delay-4">
                    <div className="detail-card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Shield size={13} style={{ color: 'var(--text-3)' }} />
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-2)' }}>
                          Risk Engine
                        </span>
                      </div>
                      {selectedIncident.risk_assessment && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 800, color: 'white', lineHeight: 1 }}>
                            {selectedIncident.risk_assessment.score}
                          </span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>/100</span>
                          <span className={`pill ${selectedIncident.risk_assessment.level === 'LOW' ? 'pill-dim' : 'pill-white'}`}>
                            {selectedIncident.risk_assessment.level}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="detail-card-body">
                      {selectedIncident.risk_assessment ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                          {/* Score bar */}
                          <div>
                            <div style={{ height: 4, background: 'var(--bg-5)', borderRadius: 99, overflow: 'hidden' }}>
                              <div style={{
                                height: '100%',
                                width: `${selectedIncident.risk_assessment.score}%`,
                                background: selectedIncident.risk_assessment.score > 70
                                  ? 'linear-gradient(90deg, #555, white)'
                                  : 'linear-gradient(90deg, #333, #aaa)',
                                borderRadius: 99,
                                transition: 'width 1.5s cubic-bezier(0.4,0,0.2,1)',
                                animation: 'progress-fill 1.4s ease both',
                                '--progress-width': `${selectedIncident.risk_assessment.score}%`,
                              } as React.CSSProperties} />
                            </div>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-0)' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>DEPLOY GATE</span>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: 'var(--text-0)' }}>
                              {selectedIncident.risk_assessment.requires_approval ? 'HUMAN REQUIRED' : 'AUTO-DEPLOY'}
                            </span>
                          </div>
                          <div>
                            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)', marginBottom: 6 }}>RISK REASONS</div>
                            {selectedIncident.risk_assessment.reasons.map((r, i) => (
                              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, marginBottom: 5 }}>
                                <ArrowRight size={10} style={{ color: 'var(--text-3)', marginTop: 3, flexShrink: 0 }} />
                                <span style={{ fontSize: 11, color: 'var(--text-1)', lineHeight: 1.4 }}>{r}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <p style={{ fontSize: 12, color: 'var(--text-3)', fontStyle: 'italic' }}>
                          Risk assessment triggered post-simulation.
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Timeline */}
                <TimelinePanel incident={selectedIncident} />

              </section>
            ) : (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, color: 'var(--text-3)' }}>
                <Activity size={48} strokeWidth={1} />
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, marginBottom: 8 }}>Select an incident or inject a scenario</p>
                  <button className="btn-primary" onClick={() => withLoading('inject-SCN-02', () => injectScenario('SCN-02'))} disabled={busy}>
                    <Zap size={12} /> Quick Demo — SCN-02
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══ SCENARIOS TAB ═══ */}
        {activeTab === 'scenarios' && (
          <div style={{ flex: 1, overflowY: 'auto', padding: 32 }}>
            <div style={{ maxWidth: 1100, margin: '0 auto' }}>
              <div style={{ marginBottom: 28 }}>
                <h2 style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 6 }}>
                  Synthetic Failure Scenarios
                </h2>
                <p style={{ color: 'var(--text-2)', fontSize: 13 }}>
                  10 deterministic injection scenarios across analytical Exasol tables and operational metadata pipelines.
                  Each scenario triggers the full autonomous resolution loop.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
                {scenarios.map((scn, i) => (
                  <div key={scn.scenario_id} className="scenario-card" style={{ animationDelay: `${i * 40}ms` }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                        <span style={{
                          fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: 13, color: 'white',
                          padding: '3px 10px', borderRadius: 6, background: 'rgba(255,255,255,0.08)',
                          border: '1px solid var(--border-2)',
                        }}>
                          {scn.scenario_id}
                        </span>
                        <span style={{
                          fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
                          color: scn.risk_level === 'HIGH' || scn.risk_level === 'CRITICAL' ? 'white' : 'var(--text-2)',
                          letterSpacing: '0.06em'
                        }}>
                          RISK: {scn.risk_level || 'MEDIUM'}
                        </span>
                      </div>
                      <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-0)', marginBottom: 6 }}>
                        {scn.incident_type}
                      </h3>
                      <p style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6, marginBottom: 14 }}>
                        {scn.symptoms}
                      </p>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)', marginBottom: 18, display: 'flex', gap: 6, alignItems: 'center' }}>
                        <Database size={10} />
                        <span>{scn.affected_table}</span>
                      </div>
                    </div>
                    <button
                      className="btn-primary"
                      style={{ width: '100%', justifyContent: 'center' }}
                      onClick={() => {
                        withLoading(`inject-${scn.scenario_id}`, () => injectScenario(scn.scenario_id))
                        setActiveTab('overview')
                      }}
                      disabled={busy}
                    >
                      {actionLoading === `inject-${scn.scenario_id}`
                        ? <RefreshCw size={12} />
                        : <Zap size={12} strokeWidth={3} />}
                      Inject &amp; Start Autonomous Resolution
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══ OBSERVABILITY TAB ═══ */}
        {activeTab === 'observability' && (
          <div style={{ flex: 1, overflowY: 'auto', padding: 32 }}>
            <div style={{ maxWidth: 1100, margin: '0 auto' }}>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 28 }}>
                <div>
                  <h2 style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 6 }}>
                    Continuous Observability Engine
                  </h2>
                  <p style={{ color: 'var(--text-2)', fontSize: 13 }}>
                    Deterministic freshness, volume, null-rate, schema, and referential integrity checks across all analytical tables.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: 12 }}>
                  <MetricCard
                    value={observability?.checks.length ?? 0}
                    label="Total Checks"
                    delay={0}
                  />
                  <MetricCard
                    value={observability?.failed ?? 0}
                    label="Failing"
                    sub={observability?.failed === 0 ? 'All passing ✓' : 'Action required'}
                    delay={50}
                    progress={observability
                      ? (observability.failed / (observability.checks.length || 1)) * 100
                      : 0}
                  />
                </div>
              </div>

              {/* Observability table */}
              <div style={{ border: '1px solid var(--border-1)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', background: 'var(--bg-2)', animation: 'fade-in 0.5s ease' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      {['Metric', 'Table', 'Column', 'Current', 'Expected', 'Status', 'Details'].map(h => (
                        <th key={h}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {observability?.checks.map((c, i) => (
                      <tr key={i} style={{ animationDelay: `${i * 20}ms` }}>
                        <td style={{ fontWeight: 600, color: 'var(--text-0)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>{c.metric}</td>
                        <td>{c.table || '—'}</td>
                        <td style={{ color: 'var(--text-2)' }}>{c.column || '—'}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{String(c.current_value ?? '—')}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)' }}>{String(c.expected_value ?? '—')}</td>
                        <td>
                          <span style={{
                            fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700,
                            padding: '3px 8px', borderRadius: 4,
                            background: c.status === 'PASS' ? 'rgba(255,255,255,0.06)' : 'white',
                            color: c.status === 'PASS' ? 'var(--text-1)' : 'black',
                            border: c.status === 'PASS' ? '1px solid var(--border-1)' : 'none',
                          }}>
                            {c.status}
                          </span>
                        </td>
                        <td style={{ color: 'var(--text-2)', fontSize: 11 }}>{c.details}</td>
                      </tr>
                    ))}
                    {(!observability?.checks || observability.checks.length === 0) && (
                      <tr>
                        <td colSpan={7} style={{ textAlign: 'center', padding: 32, color: 'var(--text-3)' }}>
                          Loading observability data…
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Legend */}
              <div style={{ marginTop: 16, display: 'flex', gap: 20, alignItems: 'center', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: 'rgba(255,255,255,0.08)', display: 'inline-block', border: '1px solid var(--border-1)' }} />
                  PASS — within expected bounds
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: 'white', display: 'inline-block' }} />
                  FAIL — anomaly detected, incident will be triggered
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ── FOOTER ── */}
      <footer style={{
        borderTop: '1px solid var(--border-0)',
        padding: '8px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        color: 'var(--text-4)',
        background: 'var(--bg-1)',
        position: 'relative', zIndex: 1,
      }}>
        <span>Aegis Autonomous Data Incident Agent · Closed-Loop Architecture</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span>DETECT → INVESTIGATE → FIX → CONTROL → SIMULATE → VERIFY → RISK → APPROVE → DEPLOY → LEARN</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <TrendingUp size={10} />
            <span>Resolution rate: {resolvedPct}%</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
