import { useEffect, useState } from 'react'
import { Shield, CheckCircle, Circle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'

const COLOURS = {
  blue: { bar: 'bg-blue-400', badge: 'text-blue-400 border-blue-800 bg-blue-900/20', glow: 'shadow-blue-900/30' },
  purple: { bar: 'bg-purple-400', badge: 'text-purple-400 border-purple-800 bg-purple-900/20', glow: 'shadow-purple-900/30' },
  orange: { bar: 'bg-orange-400', badge: 'text-orange-400 border-orange-800 bg-orange-900/20', glow: 'shadow-orange-900/30' },
  green: { bar: 'bg-green-400', badge: 'text-green-400 border-green-800 bg-green-900/20', glow: 'shadow-green-900/30' },
  yellow: { bar: 'bg-yellow-400', badge: 'text-yellow-400 border-yellow-800 bg-yellow-900/20', glow: 'shadow-yellow-900/30' },
}

const ICONS = {
  GB: '🇬🇧', lock: '🔒', bank: '💳', shield: '🏦', EU: '🇪🇺'
}

function FrameworkCard({ fw }) {
  const [expanded, setExpanded] = useState(false)
  const navigate = useNavigate()
  const c = COLOURS[fw.colour] || COLOURS.blue

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="text-2xl">{ICONS[fw.icon] || '🔒'}</div>
          <div>
            <h3 className="font-bold text-forge-text">{fw.name}</h3>
            <p className="text-xs text-forge-muted mt-0.5">{fw.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <span className={`text-xs font-mono px-2 py-1 rounded border ${c.badge}`}>
            {fw.status === 'compliant' ? 'Compliant' : fw.status === 'in_progress' ? 'In Progress' : 'Not Started'}
          </span>
          <span className="text-2xl font-bold font-mono text-forge-text">{fw.percent}%</span>
        </div>
      </div>

      <div className="w-full bg-forge-border rounded-full h-2 mb-3">
        <div className={`${c.bar} h-2 rounded-full transition-all duration-500`} style={{width: fw.percent + '%'}} />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-forge-muted font-mono">{fw.completed}/{fw.total} modules completed</span>
        <button onClick={() => setExpanded(e => !e)} className="flex items-center gap-1 text-xs text-forge-muted hover:text-forge-accent transition-colors">
          {expanded ? <><ChevronUp size={13} />Hide modules</> : <><ChevronDown size={13} />Show modules</>}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 space-y-2 border-t border-forge-border pt-4">
          {fw.modules.map((m, i) => (
            <div key={i} className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 min-w-0">
                {m.completed
                  ? <CheckCircle size={14} className="text-green-400 flex-shrink-0" />
                  : <Circle size={14} className="text-forge-muted flex-shrink-0" />}
                <span className={`text-xs truncate ${m.completed ? 'text-forge-text' : 'text-forge-muted'}`}>{m.title}</span>
              </div>
              {!m.completed && (
                <button onClick={() => navigate('/learning/' + m.slug)}
                  className="text-xs text-forge-accent hover:underline flex-shrink-0 flex items-center gap-1">
                  Start <ExternalLink size={10} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ComplianceTracker() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/compliance/status').then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20">
      <div className="text-forge-accent font-mono text-sm animate-pulse">Loading compliance data...</div>
    </div>
  )

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <Shield size={14} className="text-forge-accent" />
          <span>PREPIQ / COMPLIANCE</span>
        </div>
        <h1 className="text-2xl font-bold text-forge-text">UK Regulatory Compliance Tracker</h1>
        <p className="text-forge-muted text-sm mt-1">Track your progress against UK and EU cybersecurity regulatory frameworks</p>
      </div>

      {data && (
        <>
          <div className="card mb-8 bg-forge-accent/5 border-forge-accent/20">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-mono text-forge-muted mb-1">Overall Compliance Score</div>
                <div className="text-4xl font-bold font-mono text-forge-accent">{data.overall_compliance}%</div>
                <div className="text-xs text-forge-muted mt-1">Across {data.frameworks.length} regulatory frameworks</div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {data.frameworks.map(fw => (
                  <div key={fw.id} className="text-center">
                    <div className="text-lg">{ICONS[fw.icon]}</div>
                    <div className="text-xs font-mono text-forge-accent">{fw.percent}%</div>
                    <div className="text-xs text-forge-muted">{fw.name.split(' ')[0]}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {data.frameworks.map(fw => <FrameworkCard key={fw.id} fw={fw} />)}
          </div>
        </>
      )}
    </div>
  )
}
