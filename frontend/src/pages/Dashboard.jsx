import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Terminal, ClipboardCheck, TrendingUp, ArrowRight, Shield, Activity, Zap, ExternalLink, AlertTriangle, FileDown } from 'lucide-react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import api from '../utils/api'
import useAuthStore from '../store/authStore'

const MaturityBadge = ({ level }) => {
  const config = {
    critical: 'badge-red',
    low: 'badge-orange',
    medium: 'badge-yellow',
    high: 'badge-blue',
    advanced: 'badge-green',
  }
  return <span className={config[level] || 'badge-blue'}>{level?.toUpperCase()}</span>
}

const EVENT_LABELS = {
  login: 'Signed in',
  module_start: 'Started module',
  module_complete: 'Completed module',
  quiz_submit: 'Submitted quiz',
  assessment_complete: 'Completed risk assessment',
  report_download: 'Downloaded PDF report',
  simulation_start: 'Started simulation',
  simulation_complete: 'Completed simulation',
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const user = useAuthStore(s => s.user)
  const navigate = useNavigate()
  const [threats, setThreats] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [briefing, setBriefing] = useState(null)
  const [badges, setBadges] = useState(null)

  useEffect(() => {
    api.get('/threats/feed').then(r => setThreats(r.data)).catch(() => {})
    api.get('/badges/my').then(r => setBadges(r.data)).catch(() => {})
    api.post('/badges/check').catch(() => {})
    api.get('/briefing/today').then(r => setBriefing(r.data)).catch(() => {})
  }, [])

  const downloadBoardReport = async () => {
    setDownloading(true)
    try {
      const res = await api.get('/reports/generate', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = 'PrepIQ_Board_Report.pdf'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e) { console.error('Report download failed', e) }
    finally { setDownloading(false) }
  }

  useEffect(() => {
    api.get('/analytics/dashboard').then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20">
      <div className="text-forge-accent font-mono text-sm animate-pulse">Loading platform data...</div>
    </div>
  )

  const radarData = [
    { subject: 'Learning', value: data?.learning?.completion_rate || 0 },
    { subject: 'Simulations', value: Math.min((data?.simulations?.completed || 0) * 33, 100) },
    { subject: 'Assessment', value: data?.assessment?.latest_score || 0 },
  ]

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <Shield size={14} className="text-forge-accent" />
          <span>PREPIQ / DASHBOARD</span>
        </div>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-forge-text">
          Welcome back, <span className="text-forge-accent font-mono">{user?.full_name?.split(' ')[0]}</span>
        </h1>
          <button onClick={downloadBoardReport} disabled={downloading}
            className="flex items-center gap-2 px-4 py-2 border border-forge-accent/30 text-forge-accent rounded-lg text-sm font-mono hover:bg-forge-accent/10 transition-all disabled:opacity-40">
            {downloading ? 'Generating...' : <><FileDown size={14} /> Board Report</>}
          </button>
        </div>
        <p className="text-forge-muted text-sm mt-1">Your cyber preparedness overview</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <span className="stat-label">Modules Completed</span>
            <BookOpen size={16} className="text-forge-accent opacity-50" />
          </div>
          <div className="stat-value">{data?.learning?.completed_modules ?? 0}</div>
          <div className="text-xs text-forge-muted font-mono">
            of {data?.learning?.total_modules ?? 0} available
          </div>
          <div className="mt-3 h-1.5 bg-forge-border rounded-full overflow-hidden">
            <div
              className="h-full bg-forge-accent rounded-full transition-all"
              style={{ width: `${data?.learning?.completion_rate || 0}%` }}
            />
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <span className="stat-label">Simulations Run</span>
            <Terminal size={16} className="text-forge-green opacity-50" />
          </div>
          <div className="stat-value text-forge-green">{data?.simulations?.completed ?? 0}</div>
          {data?.simulations?.avg_score > 0 && (
            <div className="text-xs text-forge-muted font-mono">
              Avg score: {data.simulations.avg_score}%
            </div>
          )}
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <span className="stat-label">Risk Score</span>
            <ClipboardCheck size={16} className="text-forge-yellow opacity-50" />
          </div>
          {data?.assessment?.latest_score != null ? (
            <>
              <div className="stat-value text-forge-yellow">{data.assessment.latest_score}</div>
              <MaturityBadge level={data.assessment.maturity_level} />
            </>
          ) : (
            <div className="text-sm text-forge-muted mt-2">
              <button onClick={() => navigate('/assessment')} className="text-forge-accent hover:underline text-xs font-mono">
                Run your first assessment →
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Continue Learning', desc: 'Pick up where you left off', to: '/learning', color: 'text-forge-accent', Icon: BookOpen },
          { label: 'Run a Simulation', desc: 'Hands-on attack scenarios', to: '/simulations', color: 'text-forge-green', Icon: Terminal },
          { label: 'Risk Assessment', desc: 'Assess your security posture', to: '/assessment', color: 'text-forge-yellow', Icon: ClipboardCheck },
        ].map(({ label, desc, to, color, Icon }) => (
          <button
            key={to}
            onClick={() => navigate(to)}
            className="card-hover text-left group"
          >
            <div className="flex items-start justify-between">
              <Icon size={20} className={`${color} mb-3`} />
              <ArrowRight size={16} className="text-forge-muted group-hover:text-forge-text transition-colors" />
            </div>
            <div className="font-semibold text-forge-text text-sm">{label}</div>
            <div className="text-xs text-forge-muted mt-0.5">{desc}</div>
          </button>
        ))}
      </div>

      {/* Radar chart + Activity feed */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <div className="section-header flex items-center gap-2">
              <TrendingUp size={16} className="text-forge-accent" />
              Capability Overview
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#1a2540" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#4a5568', fontSize: 12, fontFamily: 'JetBrains Mono' }} />
                  <Radar name="Score" dataKey="value" stroke="#00d4ff" fill="#00d4ff" fillOpacity={0.15} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card">
            <div className="section-header flex items-center gap-2">
              <Activity size={16} className="text-forge-green" />
              Recent Activity
            </div>
            <div className="space-y-2 overflow-y-auto max-h-52">
              {data.recent_activity?.length > 0 ? (
                data.recent_activity.map((event, i) => (
                  <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-forge-border last:border-0">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-forge-green flex-shrink-0" />
                      <span className="text-forge-text">{EVENT_LABELS[event.event_type] || event.event_type}</span>
                      {event.metadata?.module_slug && (
                        <span className="text-forge-muted">— {event.metadata.module_slug}</span>
                      )}
                      {event.metadata?.score != null && (
                        <span className="text-forge-accent font-mono">{event.metadata.score}%</span>
                      )}
                    </div>
                    <span className="text-forge-muted font-mono flex-shrink-0 ml-2">{timeAgo(event.timestamp)}</span>
                  </div>
                ))
              ) : (
                <p className="text-forge-muted text-xs font-mono py-4 text-center">
                  No activity yet — start a module to begin
                </p>
              )}
            </div>
          </div>
        </div>
      )}
      {/* AI Threat Briefing */}
      {briefing && (
        <div className="card mt-6" style={{borderColor: briefing.threat_level === 'HIGH' || briefing.threat_level === 'CRITICAL' ? '#ef444440' : '#1e3a5f'}}>
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-yellow-400 flex-shrink-0" />
              <span className="font-mono font-bold text-forge-text text-sm">AI Daily Threat Briefing</span>
              <span className="text-xs font-mono text-forge-muted">{briefing.date}</span>
            </div>
            <span className={`text-xs font-mono px-2 py-0.5 rounded border flex-shrink-0 ${
              briefing.threat_level === 'CRITICAL' ? 'text-red-400 border-red-800 bg-red-900/20' :
              briefing.threat_level === 'HIGH' ? 'text-orange-400 border-orange-800 bg-orange-900/20' :
              briefing.threat_level === 'MODERATE' ? 'text-yellow-400 border-yellow-800 bg-yellow-900/20' :
              'text-green-400 border-green-800 bg-green-900/20'
            }`}>{briefing.threat_level}</span>
          </div>
          <p className="text-sm font-semibold text-forge-text mb-2">{briefing.headline}</p>
          <p className="text-xs text-forge-muted mb-3 leading-relaxed">{briefing.summary}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-3">
            {briefing.top_threats?.map((t, i) => (
              <div key={i} className="bg-forge-bg border border-forge-border rounded-lg p-2.5">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${t.severity === 'HIGH' ? 'bg-red-400' : t.severity === 'MEDIUM' ? 'bg-yellow-400' : 'bg-green-400'}`} />
                  <span className="text-xs font-semibold text-forge-text">{t.threat}</span>
                </div>
                <p className="text-xs text-forge-muted">{t.description}</p>
              </div>
            ))}
          </div>
          <div className="flex items-start gap-2 p-2.5 bg-forge-accent/5 border border-forge-accent/20 rounded-lg">
            <span className="text-forge-accent text-xs font-mono font-bold flex-shrink-0">ACTION:</span>
            <span className="text-xs text-forge-text">{briefing.action_of_the_day}</span>
          </div>
        </div>
      )}

      {/* Badges */}
      {badges && badges.earned_count > 0 && (
        <div className="card mt-6">
          <div className="section-header flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">🏆</span>
              <span>My Badges</span>
              <span className="text-xs font-mono text-forge-muted">({badges.earned_count}/{badges.total})</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            {badges.badges.map((b, i) => (
              <div key={i} title={b.description}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs transition-all ${
                  b.earned
                    ? 'border-forge-accent/30 bg-forge-accent/5 text-forge-text'
                    : 'border-forge-border bg-forge-bg text-forge-muted opacity-40'
                }`}>
                <span className="text-lg">{b.icon}</span>
                <div>
                  <div className="font-semibold">{b.name}</div>
                  {b.earned_at && <div className="text-forge-muted font-mono text-xs">{new Date(b.earned_at).toLocaleDateString('en-GB')}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Threat Intelligence Feed */}
      <div className="card mt-6">
        <div className="section-header flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-red-400" />
            <span>Live Threat Intelligence</span>
          </div>
          {threats && (
            <div className="flex items-center gap-2 text-xs font-mono text-forge-muted">
              <span className="text-green-400">{threats.sources?.ncsc || 0} NCSC</span>
              <span>·</span>
              <span className="text-blue-400">{threats.sources?.cisa || 0} CISA</span>
              <span>·</span>
              <span className="text-red-400">{threats.sources?.cve || 0} CVEs</span>
            </div>
          )}
        </div>
        {!threats ? (
          <p className="text-forge-muted text-xs font-mono py-4 text-center animate-pulse">Loading threat feed...</p>
        ) : (
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {threats.items.map((item, i) => (
              <a key={i} href={item.link} target="_blank" rel="noreferrer"
                className="flex items-start gap-3 p-3 rounded-lg border border-forge-border hover:border-forge-accent/40 hover:bg-forge-accent/5 transition-all group">
                <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                  item.source === 'NCSC' ? 'bg-green-400' :
                  item.source === 'CISA' ? 'bg-blue-400' : 'bg-red-400'
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={`text-xs font-mono px-1.5 py-0.5 rounded border flex-shrink-0 ${
                      item.source === 'NCSC' ? 'text-green-400 border-green-800 bg-green-900/20' :
                      item.source === 'CISA' ? 'text-blue-400 border-blue-800 bg-blue-900/20' :
                      'text-red-400 border-red-800 bg-red-900/20'
                    }`}>{item.source}</span>
                    {item.score && <span className="text-xs font-mono text-red-400">CVSS {item.score}</span>}
                  </div>
                  <p className="text-xs text-forge-text truncate group-hover:text-forge-accent transition-colors">{item.title}</p>
                  {item.description && <p className="text-xs text-forge-muted mt-0.5 line-clamp-1">{item.description}</p>}
                </div>
                <ExternalLink size={12} className="text-forge-muted group-hover:text-forge-accent flex-shrink-0 mt-1 transition-colors" />
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
