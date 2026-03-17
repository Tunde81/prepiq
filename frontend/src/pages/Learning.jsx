import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Clock, ChevronRight, CheckCircle, PlayCircle } from 'lucide-react'
import api from '../utils/api'

const DifficultyBadge = ({ level }) => {
  const cls = { beginner: 'badge-green', intermediate: 'badge-yellow', advanced: 'badge-red' }
  return <span className={cls[level] || 'badge-blue'}>{level}</span>
}

const StatusIcon = ({ status }) => {
  if (status === 'completed') return <CheckCircle size={16} className="text-forge-green" />
  if (status === 'in_progress') return <PlayCircle size={16} className="text-forge-accent" />
  return <div className="w-4 h-4 rounded-full border border-forge-border" />
}

export default function Learning() {
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/learning/modules').then(r => setModules(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20">
      <div className="text-forge-accent font-mono text-sm animate-pulse">Loading modules...</div>
    </div>
  )

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <BookOpen size={14} className="text-forge-accent" />
          <span>PREPIQ / LEARNING</span>
        </div>
        <h1 className="text-2xl font-bold text-forge-text">Learning Modules</h1>
        <p className="text-forge-muted text-sm mt-1">Master cyber fundamentals through structured, practical content</p>
      </div>

      <div className="space-y-3">
        {modules.map((mod, i) => (
          <button
            key={mod.id}
            onClick={() => navigate(`/learning/${mod.slug}`)}
            className="w-full card-hover text-left group"
          >
            <div className="flex items-center gap-5">
              {/* Number */}
              <div className="w-10 h-10 rounded-lg bg-forge-border flex items-center justify-center font-mono text-sm text-forge-accent flex-shrink-0">
                {String(i + 1).padStart(2, '0')}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-forge-text text-sm">{mod.title}</span>
                  <DifficultyBadge level={mod.difficulty} />
                </div>
                <p className="text-xs text-forge-muted truncate">{mod.description}</p>
              </div>

              {/* Meta */}
              <div className="flex items-center gap-4 flex-shrink-0">
                <div className="hidden md:flex items-center gap-1.5 text-xs text-forge-muted font-mono">
                  <Clock size={12} />
                  {mod.duration_minutes}m
                </div>
                <StatusIcon status={mod.progress?.status} />
                {mod.progress?.status === 'in_progress' && (
                  <div className="hidden md:block w-20">
                    <div className="h-1 bg-forge-border rounded-full overflow-hidden">
                      <div className="h-full bg-forge-accent rounded-full" style={{ width: `${mod.progress.percent}%` }} />
                    </div>
                    <div className="text-xs text-forge-muted font-mono text-right mt-0.5">{mod.progress.percent}%</div>
                  </div>
                )}
                {mod.progress?.status === 'completed' && mod.progress?.quiz_score != null && (
                  <div className="text-xs font-mono text-forge-green hidden md:block">Quiz: {mod.progress.quiz_score}%</div>
                )}
                <ChevronRight size={16} className="text-forge-muted group-hover:text-forge-accent transition-colors" />
              </div>
            </div>
          </button>
        ))}
      </div>

      {modules.length === 0 && (
        <div className="text-center py-20 text-forge-muted font-mono text-sm">
          No modules available yet.
        </div>
      )}
    </div>
  )
}
