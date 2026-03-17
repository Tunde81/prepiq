import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, ChevronRight, CheckCircle, Circle, Clock, Target, Loader, RefreshCw } from 'lucide-react'
import api from '../utils/api'

export default function LearningPaths() {
  const [roles, setRoles] = useState([])
  const [sectors, setSectors] = useState([])
  const [role, setRole] = useState('')
  const [sector, setSector] = useState('')
  const [level, setLevel] = useState('beginner')
  const [path, setPath] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/paths/roles').then(r => {
      setRoles(r.data.roles)
      setSectors(r.data.sectors)
      setRole(r.data.roles[0])
      setSector(r.data.sectors[0])
    })
  }, [])

  const generate = async () => {
    if (!role || !sector) return
    setGenerating(true)
    setError('')
    setPath(null)
    try {
      const res = await api.post('/paths/generate', { role, sector, experience_level: level })
      setPath(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to generate path')
    } finally {
      setGenerating(false)
    }
  }

  const diffColour = (d) => {
    if (d === 'beginner') return 'text-green-400 border-green-800 bg-green-900/20'
    if (d === 'intermediate') return 'text-yellow-400 border-yellow-800 bg-yellow-900/20'
    return 'text-red-400 border-red-800 bg-red-900/20'
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <Sparkles size={14} className="text-forge-accent" />
          <span>PREPIQ / LEARNING PATHS</span>
        </div>
        <h1 className="text-2xl font-bold text-forge-text">AI Personalised Learning Paths</h1>
        <p className="text-forge-muted text-sm mt-1">Get a tailored cybersecurity curriculum based on your role and sector</p>
      </div>

      {/* Path Generator */}
      <div className="card mb-8">
        <h2 className="font-mono font-bold text-forge-text mb-4">Generate Your Path</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs font-mono text-forge-muted uppercase tracking-wider mb-1.5">Your Role</label>
            <select value={role} onChange={e => setRole(e.target.value)}
              className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text focus:outline-none focus:border-forge-accent transition-colors">
              {roles.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-mono text-forge-muted uppercase tracking-wider mb-1.5">Your Sector</label>
            <select value={sector} onChange={e => setSector(e.target.value)}
              className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text focus:outline-none focus:border-forge-accent transition-colors">
              {sectors.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-mono text-forge-muted uppercase tracking-wider mb-1.5">Experience Level</label>
            <select value={level} onChange={e => setLevel(e.target.value)}
              className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text focus:outline-none focus:border-forge-accent transition-colors">
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>
        <button onClick={generate} disabled={generating}
          className="btn-primary flex items-center gap-2">
          {generating ? <Loader size={15} className="animate-spin" /> : <Sparkles size={15} />}
          {generating ? 'Generating your path...' : 'Generate My Learning Path'}
        </button>
        {error && <p className="mt-3 text-xs text-red-400 font-mono">{error}</p>}
      </div>

      {/* Generated Path */}
      {path && (
        <div>
          <div className="card mb-6 bg-forge-accent/5 border-forge-accent/20">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h2 className="font-bold text-forge-text text-lg">{path.path_title}</h2>
                <p className="text-forge-muted text-sm mt-1">{path.path_description}</p>
              </div>
              <button onClick={generate} className="p-2 text-forge-muted hover:text-forge-accent rounded-lg hover:bg-forge-border transition-colors flex-shrink-0" title="Regenerate">
                <RefreshCw size={14} />
              </button>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="text-xl font-bold font-mono text-forge-accent">{path.percent_complete}%</div>
                <div className="text-xs text-forge-muted">Complete</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold font-mono text-forge-text">{path.completed_count}/{path.total_count}</div>
                <div className="text-xs text-forge-muted">Modules</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold font-mono text-forge-text">{path.estimated_hours}h</div>
                <div className="text-xs text-forge-muted">Est. Duration</div>
              </div>
            </div>
            <div className="w-full bg-forge-border rounded-full h-2 mb-4">
              <div className="bg-forge-accent h-2 rounded-full transition-all duration-500" style={{width: path.percent_complete + '%'}} />
            </div>
            {path.priority_focus && (
              <div className="flex items-start gap-2 p-3 bg-forge-border/50 rounded-lg">
                <Target size={14} className="text-forge-accent flex-shrink-0 mt-0.5" />
                <p className="text-xs text-forge-muted"><span className="text-forge-accent font-semibold">Priority: </span>{path.priority_focus}</p>
              </div>
            )}
          </div>

          {path.next_module && (
            <div className="card mb-6 border-forge-accent/30 bg-forge-accent/5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-mono text-forge-accent mb-1">NEXT UP</div>
                  <div className="font-semibold text-forge-text">{path.next_module.title}</div>
                  <div className="text-xs text-forge-muted mt-0.5">{path.next_module.reason}</div>
                </div>
                <button onClick={() => navigate('/learning/' + path.next_module.slug)}
                  className="btn-primary flex items-center gap-2 flex-shrink-0">
                  Start <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {path.modules.map((m, i) => (
              <div key={m.id} onClick={() => !m.completed && navigate('/learning/' + m.slug)}
                className={`card flex items-center gap-4 transition-all ${!m.completed ? 'cursor-pointer hover:border-forge-accent/40' : 'opacity-75'}`}>
                <div className="w-8 h-8 rounded-full border flex items-center justify-center flex-shrink-0 font-mono text-sm font-bold
                  ${m.completed ? 'border-green-800 bg-green-900/20 text-green-400' : 'border-forge-border text-forge-muted'}">
                  {m.completed ? <CheckCircle size={16} className="text-green-400" /> : <span>{i + 1}</span>}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold text-sm ${m.completed ? 'text-forge-muted line-through' : 'text-forge-text'}`}>{m.title}</span>
                    <span className={`text-xs font-mono px-1.5 py-0.5 rounded border ${diffColour(m.difficulty)}`}>{m.difficulty}</span>
                  </div>
                  <p className="text-xs text-forge-muted mt-0.5">{m.reason}</p>
                </div>
                <div className="flex items-center gap-1 text-xs text-forge-muted flex-shrink-0">
                  <Clock size={11} />
                  <span>{m.duration_minutes}m</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
