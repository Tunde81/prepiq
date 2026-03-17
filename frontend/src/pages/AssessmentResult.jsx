import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Download, ArrowLeft, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import api from '../utils/api'

const maturityConfig = {
  critical: { color: 'text-forge-red', bg: 'bg-red-900/20 border-red-800/30', label: 'Critical Risk' },
  low: { color: 'text-forge-orange', bg: 'bg-orange-900/20 border-orange-800/30', label: 'Low Maturity' },
  medium: { color: 'text-forge-yellow', bg: 'bg-yellow-900/20 border-yellow-800/30', label: 'Developing' },
  high: { color: 'text-forge-accent', bg: 'bg-blue-900/20 border-blue-800/30', label: 'Managed' },
  advanced: { color: 'text-forge-green', bg: 'bg-green-900/20 border-green-800/30', label: 'Advanced' },
}

const barColor = (score) => {
  if (score < 25) return '#ff4444'
  if (score < 50) return '#ff8800'
  if (score < 65) return '#ffd700'
  if (score < 80) return '#00d4ff'
  return '#00ff88'
}

export default function AssessmentResult() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/assessment/${id}`).then(r => setResult(r.data)).finally(() => setLoading(false))
  }, [id])

  const downloadReport = () => {
    window.open(`/api/assessment/${id}/report`, '_blank')
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20">
      <div className="text-forge-accent font-mono text-sm animate-pulse">Loading results...</div>
    </div>
  )

  if (!result) return <div className="p-8 text-forge-muted">Assessment not found.</div>

  const mc = maturityConfig[result.maturity_level] || maturityConfig.medium
  const domainData = Object.values(result.domain_scores || {}).map(d => ({
    name: d.name.split(' ')[0], // Shorten for chart
    fullName: d.name,
    score: d.score,
  }))

  const radarData = Object.values(result.domain_scores || {}).map(d => ({
    subject: d.name.split(' ')[0],
    value: d.score,
  }))

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <button onClick={() => navigate('/assessment')} className="flex items-center gap-2 text-forge-muted hover:text-forge-text text-sm transition-colors">
          <ArrowLeft size={14} />
          New Assessment
        </button>
        <button onClick={downloadReport} className="btn-primary flex items-center gap-2">
          <Download size={14} />
          Download PDF Report
        </button>
      </div>

      {/* Overall score */}
      <div className={`card border mb-6 ${mc.bg}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-forge-muted mb-1">CYBER MATURITY SCORE</div>
            <div className={`text-5xl font-bold font-mono ${mc.color}`}>{result.overall_score}</div>
            <div className={`text-sm font-semibold mt-1 ${mc.color}`}>{mc.label}</div>
            <div className="text-xs text-forge-muted mt-1">{result.organisation_name} · {result.organisation_sector}</div>
          </div>
          <div className="w-40 h-40">
            <ResponsiveContainer>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#1a2540" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#4a5568', fontSize: 9 }} />
                <Radar dataKey="value" stroke="#00d4ff" fill="#00d4ff" fillOpacity={0.15} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Domain bar chart */}
      <div className="card mb-6">
        <div className="section-header">Domain Scores</div>
        <div className="h-56">
          <ResponsiveContainer>
            <BarChart data={domainData} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
              <XAxis dataKey="name" tick={{ fill: '#4a5568', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#4a5568', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#0d1321', border: '1px solid #1a2540', borderRadius: 8, fontSize: 12 }}
                formatter={(v, n, props) => [`${v.toFixed(1)}%`, props.payload.fullName]}
              />
              <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                {domainData.map((entry, i) => (
                  <Cell key={i} fill={barColor(entry.score)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top risks */}
      <div className="card mb-6">
        <div className="section-header flex items-center gap-2">
          <AlertTriangle size={16} className="text-forge-red" />
          Priority Risks & Recommendations
        </div>
        <div className="space-y-4">
          {result.top_risks?.map((risk, i) => (
            <div key={i} className={`p-4 rounded-lg border ${
              risk.severity === 'Critical' ? 'border-red-800/30 bg-red-900/10' :
              risk.severity === 'High' ? 'border-orange-800/30 bg-orange-900/10' :
              'border-yellow-800/30 bg-yellow-900/10'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-forge-text text-sm">{risk.domain}</span>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-mono ${
                    risk.severity === 'Critical' ? 'text-forge-red' :
                    risk.severity === 'High' ? 'text-forge-orange' : 'text-forge-yellow'
                  }`}>{risk.severity}</span>
                  <span className="text-xs text-forge-muted font-mono">{risk.score?.toFixed(1)}%</span>
                </div>
              </div>
              <p className="text-xs text-forge-muted leading-relaxed">{risk.recommendation}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Next steps */}
      <div className="card">
        <div className="section-header flex items-center gap-2">
          <TrendingUp size={16} className="text-forge-green" />
          Recommended Next Steps
        </div>
        <div className="grid md:grid-cols-2 gap-3">
          {[
            { label: 'Start Learning Modules', desc: 'Build knowledge in your weakest domains', to: '/learning' },
            { label: 'Run Attack Simulations', desc: 'Practice incident response skills hands-on', to: '/simulations' },
            { label: 'Download Full Report', desc: 'Share with leadership and your security team', action: downloadReport },
            { label: 'Reassess in 90 Days', desc: 'Track your improvement over time', to: '/assessment' },
          ].map((item, i) => (
            <button
              key={i}
              onClick={item.action || (() => navigate(item.to))}
              className="card-hover text-left"
            >
              <div className="font-medium text-forge-text text-sm">{item.label}</div>
              <div className="text-xs text-forge-muted mt-0.5">{item.desc}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
