import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Terminal, Clock, Target, CheckCircle, ChevronRight } from 'lucide-react'
import api from '../utils/api'

const categoryColors = {
  phishing: 'text-forge-accent',
  ransomware: 'text-forge-red',
  cloud: 'text-forge-yellow',
  social_engineering: 'text-forge-orange',
}

const DiffBadge = ({ d }) => {
  const cls = { beginner: 'badge-green', intermediate: 'badge-yellow', advanced: 'badge-red' }
  return <span className={cls[d] || 'badge-blue'}>{d}</span>
}

export default function Simulations() {
  const [scenarios, setScenarios] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/simulations/scenarios').then(r => setScenarios(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20">
      <div className="text-forge-accent font-mono text-sm animate-pulse">Loading scenarios...</div>
    </div>
  )

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <Terminal size={14} className="text-forge-accent" />
          <span>PREPIQ / SIMULATIONS</span>
        </div>
        <h1 className="text-2xl font-bold text-forge-text">Attack Simulations</h1>
        <p className="text-forge-muted text-sm mt-1">Hands-on cyber incident scenarios in isolated environments</p>
      </div>

      <div className="terminal mb-8 text-xs">
        <span className="text-forge-muted">$ </span>
        <span className="text-forge-green">prepiq</span>
        <span className="text-forge-muted"> --list-scenarios --env isolated --safe</span>
        <br />
        <span className="text-forge-muted">Found {scenarios.length} scenario(s). All sessions expire after 2 hours.</span>
      </div>

      <div className="grid gap-4">
        {scenarios.map((s) => (
          <div key={s.id} className="card-hover group" onClick={() => navigate(`/simulations/${s.id}/play`)}>
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4 flex-1">
                <div className={`mt-0.5 ${categoryColors[s.category] || 'text-forge-accent'}`}>
                  <Terminal size={20} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-forge-text">{s.title}</span>
                    <DiffBadge d={s.difficulty} />
                    {s.completed && <CheckCircle size={14} className="text-forge-green" />}
                  </div>
                  <p className="text-sm text-forge-muted mb-3">{s.description}</p>
                  <div className="flex flex-wrap gap-3">
                    <div className="flex items-center gap-1.5 text-xs text-forge-muted font-mono">
                      <Clock size={12} />
                      ~{s.duration_minutes} min
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-forge-muted font-mono">
                      <Target size={12} />
                      {s.objectives?.length} objectives
                    </div>
                    {s.best_score != null && (
                      <div className="text-xs font-mono text-forge-green">
                        Best: {s.best_score}%
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <ChevronRight size={18} className="text-forge-muted group-hover:text-forge-accent transition-colors flex-shrink-0 mt-1" />
            </div>
          </div>
        ))}
      </div>

      {scenarios.length === 0 && (
        <div className="text-center py-20 text-forge-muted font-mono text-sm">
          No scenarios available yet.
        </div>
      )}
    </div>
  )
}
