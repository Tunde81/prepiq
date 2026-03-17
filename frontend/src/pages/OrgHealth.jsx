import { useEffect, useState } from 'react'
import { Building2, Users, Trophy, AlertTriangle, Copy, CheckCheck, Plus, LogIn, TrendingUp } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'

function HealthGauge({ score }) {
  const colour = score >= 70 ? 'text-green-400' : score >= 40 ? 'text-yellow-400' : 'text-red-400'
  const label = score >= 70 ? 'Good' : score >= 40 ? 'Fair' : 'Needs Attention'
  return (
    <div className="text-center">
      <div className={`text-5xl font-bold font-mono ${colour}`}>{score}</div>
      <div className={`text-sm font-mono mt-1 ${colour}`}>{label}</div>
      <div className="text-xs text-forge-muted mt-1">Cyber Health Score</div>
    </div>
  )
}

export default function OrgHealth() {
  const [org, setOrg] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [joining, setJoining] = useState(false)
  const [orgName, setOrgName] = useState('')
  const [sector, setSector] = useState('Financial Services / Banking')
  const [size, setSize] = useState('SME')
  const [inviteInput, setInviteInput] = useState('')
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = async () => {
    try {
      const r = await api.get('/organisations/my')
      setOrg(r.data)
      if (r.data) {
        const h = await api.get('/organisations/health')
        setHealth(h.data)
      }
    } catch (e) {}
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const createOrg = async () => {
    if (!orgName.trim()) return
    setCreating(true); setError('')
    try {
      await api.post('/organisations/create', { name: orgName, sector, size })
      await load()
    } catch (e) { setError(e.response?.data?.detail || 'Failed to create') }
    finally { setCreating(false) }
  }

  const joinOrg = async () => {
    if (!inviteInput.trim()) return
    setJoining(true); setError('')
    try {
      await api.post('/organisations/join', { invite_code: inviteInput.toUpperCase() })
      await load()
    } catch (e) { setError(e.response?.data?.detail || 'Invalid invite code') }
    finally { setJoining(false) }
  }

  const copyCode = () => {
    navigator.clipboard.writeText(org.invite_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) return <div className="flex items-center justify-center h-full p-20"><div className="text-forge-accent font-mono text-sm animate-pulse">Loading...</div></div>

  if (!org) return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <Building2 size={14} className="text-forge-accent" /><span>PREPIQ / ORGANISATION</span>
        </div>
        <h1 className="text-2xl font-bold text-forge-text">Organisation</h1>
        <p className="text-forge-muted text-sm mt-1">Create or join an organisation to track your team's cyber health</p>
      </div>
      {error && <p className="mb-4 text-xs text-red-400 font-mono">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-bold text-forge-text mb-4 flex items-center gap-2"><Plus size={16} className="text-forge-accent" />Create Organisation</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-mono text-forge-muted uppercase tracking-wider mb-1">Organisation Name</label>
              <input value={orgName} onChange={e => setOrgName(e.target.value)} placeholder="e.g. Acme Financial Ltd"
                className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text focus:outline-none focus:border-forge-accent transition-colors" />
            </div>
            <div>
              <label className="block text-xs font-mono text-forge-muted uppercase tracking-wider mb-1">Sector</label>
              <select value={sector} onChange={e => setSector(e.target.value)}
                className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text focus:outline-none focus:border-forge-accent transition-colors">
                {['Financial Services / Banking','Healthcare / NHS','Legal Services','Education','Retail / E-commerce','Local Government / Council','Technology / SaaS','Manufacturing','Professional Services','Charity / Non-profit'].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-mono text-forge-muted uppercase tracking-wider mb-1">Size</label>
              <select value={size} onChange={e => setSize(e.target.value)}
                className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text focus:outline-none focus:border-forge-accent transition-colors">
                {['SME','LARGE','SCHOOL','COUNCIL'].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <button onClick={createOrg} disabled={creating || !orgName.trim()} className="btn-primary w-full">
              {creating ? 'Creating...' : 'Create Organisation'}
            </button>
          </div>
        </div>
        <div className="card">
          <h2 className="font-bold text-forge-text mb-4 flex items-center gap-2"><LogIn size={16} className="text-forge-accent" />Join Organisation</h2>
          <p className="text-xs text-forge-muted mb-4">Enter the 8-character invite code shared by your organisation admin.</p>
          <input value={inviteInput} onChange={e => setInviteInput(e.target.value.toUpperCase())} placeholder="e.g. ABC12345" maxLength={8}
            className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text font-mono focus:outline-none focus:border-forge-accent transition-colors mb-3" />
          <button onClick={joinOrg} disabled={joining || inviteInput.length !== 8} className="btn-primary w-full">
            {joining ? 'Joining...' : 'Join Organisation'}
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <Building2 size={14} className="text-forge-accent" /><span>PREPIQ / ORGANISATION</span>
        </div>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-forge-text">{org.name}</h1>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-forge-border rounded-lg">
            <span className="text-xs font-mono text-forge-muted">Invite:</span>
            <span className="text-sm font-mono text-forge-accent font-bold">{org.invite_code}</span>
            <button onClick={copyCode} className="text-forge-muted hover:text-forge-accent transition-colors">
              {copied ? <CheckCheck size={14} className="text-green-400" /> : <Copy size={14} />}
            </button>
          </div>
        </div>
        <p className="text-forge-muted text-sm mt-1">{org.sector} · {org.size} · {org.member_count} members</p>
      </div>

      {health && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="card md:col-span-1 flex items-center justify-center py-6">
              <HealthGauge score={health.health_score} />
            </div>
            <div className="card flex flex-col justify-center">
              <div className="stat-label">Avg Progress</div>
              <div className="stat-value">{health.avg_progress}%</div>
              <div className="w-full bg-forge-border rounded-full h-1.5 mt-2">
                <div className="bg-forge-accent h-1.5 rounded-full" style={{width: health.avg_progress + '%'}} />
              </div>
            </div>
            <div className="card flex flex-col justify-center">
              <div className="stat-label">Avg Risk Score</div>
              <div className="stat-value">{health.avg_risk_score ?? '—'}</div>
              <div className="text-xs text-forge-muted font-mono mt-1">{health.avg_risk_score ? 'out of 100' : 'No assessments yet'}</div>
            </div>
            <div className="card flex flex-col justify-center">
              <div className="stat-label">Total Completions</div>
              <div className="stat-value">{health.total_completions}</div>
              <div className="text-xs text-forge-muted font-mono mt-1">across {health.member_count} members</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <div className="section-header flex items-center gap-2 mb-4">
                <Users size={15} className="text-forge-accent" />Team Progress
              </div>
              <div className="space-y-3">
                {health.members.map((m, i) => (
                  <div key={m.id} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-forge-accent/10 border border-forge-accent/20 flex items-center justify-center flex-shrink-0">
                      <span className="text-xs font-mono text-forge-accent">{i + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-forge-text truncate">{m.name}</span>
                        <span className="text-xs font-mono text-forge-accent">{m.progress_percent}%</span>
                      </div>
                      <div className="w-full bg-forge-border rounded-full h-1">
                        <div className="bg-forge-accent h-1 rounded-full" style={{width: m.progress_percent + '%'}} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="section-header flex items-center gap-2 mb-4">
                <AlertTriangle size={15} className="text-red-400" />Weakest Areas
              </div>
              <div className="space-y-3">
                {health.weakest_areas.map((w, i) => (
                  <div key={i} className="flex items-center justify-between gap-3 cursor-pointer hover:text-forge-accent transition-colors"
                    onClick={() => navigate('/learning/' + w.slug)}>
                    <span className="text-xs text-forge-text truncate">{w.title}</span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <div className="w-16 bg-forge-border rounded-full h-1">
                        <div className="bg-red-400 h-1 rounded-full" style={{width: w.completion_rate + '%'}} />
                      </div>
                      <span className="text-xs font-mono text-red-400">{w.completion_rate}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
