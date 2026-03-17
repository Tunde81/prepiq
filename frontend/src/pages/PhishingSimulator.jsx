import { useState, useEffect } from 'react'
import api from '../utils/api'
import toast from 'react-hot-toast'

const CATEGORY_LABELS = {
  hmrc: '🏛️ HMRC', nhs: '🏥 NHS', natwest: '🏦 NatWest',
  microsoft: '💻 Microsoft', dvla: '🚗 DVLA', it_helpdesk: '🖥️ IT Helpdesk',
  hr: '👔 HR', ceo_fraud: '👤 CEO Fraud', delivery: '📦 Delivery', linkedin: '💼 LinkedIn'
}
const DIFFICULTY_CONFIG = {
  easy: { color: '#10b981', label: 'Easy' },
  medium: { color: '#fbbf24', label: 'Medium' },
  hard: { color: '#ef4444', label: 'Hard' }
}
const STATUS_CONFIG = {
  draft: { color: '#6366f1', label: 'Draft' },
  active: { color: '#fbbf24', label: 'Active' },
  completed: { color: '#10b981', label: 'Completed' },
  paused: { color: '#6b7280', label: 'Paused' }
}

const card = { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: 24 }

export default function PhishingSimulator() {
  const [view, setView] = useState('dashboard') // dashboard | templates | create | campaign
  const [stats, setStats] = useState(null)
  const [campaigns, setCampaigns] = useState([])
  const [templates, setTemplates] = useState([])
  const [selectedCampaign, setSelectedCampaign] = useState(null)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [form, setForm] = useState({ name: '', template_id: null, emails: '', names: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadDashboard()
    api.get('/phishing/templates').then(r => setTemplates(r.data)).catch(() => {})
  }, [])

  const loadDashboard = () => {
    api.get('/phishing/stats').then(r => setStats(r.data)).catch(() => {})
    api.get('/phishing/campaigns').then(r => setCampaigns(r.data)).catch(() => {})
  }

  const handleCreate = async () => {
    if (!form.name || !form.template_id) return toast.error('Please fill in all fields')
    const emails = form.emails.split(/[\n,]/).map(e => e.trim()).filter(Boolean)
    const names = form.names.split(/[\n,]/).map(n => n.trim()).filter(Boolean)
    if (emails.length === 0) return toast.error('Please enter at least one target email')
    setLoading(true)
    try {
      await api.post('/phishing/campaigns', {
        name: form.name, template_id: form.template_id,
        target_emails: emails, target_names: names.length ? names : null
      })
      toast.success('Campaign created successfully')
      setForm({ name: '', template_id: null, emails: '', names: '' })
      setView('dashboard')
      loadDashboard()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create campaign')
    }
    setLoading(false)
  }

  const handleSend = async (campaignId) => {
    if (!window.confirm('Send phishing emails to all targets now?')) return
    setLoading(true)
    try {
      const r = await api.post(`/phishing/campaigns/${campaignId}/send`)
      toast.success(`Sent ${r.data.sent} emails`)
      loadDashboard()
      if (selectedCampaign?.id === campaignId) {
        const r2 = await api.get(`/phishing/campaigns/${campaignId}`)
        setSelectedCampaign(r2.data)
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Send failed')
    }
    setLoading(false)
  }

  const handleDelete = async (campaignId) => {
    if (!window.confirm('Delete this campaign?')) return
    await api.delete(`/phishing/campaigns/${campaignId}`)
    toast.success('Campaign deleted')
    setSelectedCampaign(null)
    setView('dashboard')
    loadDashboard()
  }

  const viewCampaign = async (id) => {
    const r = await api.get(`/phishing/campaigns/${id}`)
    setSelectedCampaign(r.data)
    setView('campaign')
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0f1117', fontFamily: "'DM Sans','Inter',system-ui,sans-serif", padding: '28px 20px' }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ color: 'white', fontSize: 24, fontWeight: 800, margin: 0 }}>🎣 Phishing Simulator</h1>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13, margin: '4px 0 0' }}>PrepIQ · Send simulated phishing campaigns and track staff resilience</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {['dashboard', 'templates', 'create'].map(v => (
              <button key={v} onClick={() => setView(v)} style={{
                padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
                background: view === v ? '#6366f1' : 'rgba(255,255,255,0.06)',
                color: 'white', fontWeight: 600, fontSize: 13, textTransform: 'capitalize'
              }}>{v === 'create' ? '+ New Campaign' : v.charAt(0).toUpperCase() + v.slice(1)}</button>
            ))}
          </div>
        </div>

        {/* Dashboard */}
        {view === 'dashboard' && (
          <div>
            {/* KPI strip */}
            {stats && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: 12, marginBottom: 24 }}>
                {[
                  { label: 'Campaigns', value: stats.total_campaigns, color: '#6366f1' },
                  { label: 'Emails Sent', value: stats.total_sent, color: '#818cf8' },
                  { label: 'Clicked', value: stats.total_clicked, color: '#ef4444' },
                  { label: 'Reported', value: stats.total_reported, color: '#10b981' },
                  { label: 'Avg Click Rate', value: `${stats.avg_click_rate}%`, color: '#fbbf24' },
                  { label: 'Avg Report Rate', value: `${stats.avg_report_rate}%`, color: '#34d399' },
                ].map(k => (
                  <div key={k.label} style={{ ...card, padding: '16px 20px' }}>
                    <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, margin: '0 0 4px' }}>{k.label}</p>
                    <p style={{ color: k.color, fontSize: 26, fontWeight: 800, margin: 0 }}>{k.value}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Campaigns table */}
            <div style={card}>
              <h3 style={{ color: 'white', fontWeight: 700, marginBottom: 16 }}>Campaigns</h3>
              {campaigns.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <p style={{ color: 'rgba(255,255,255,0.3)', marginBottom: 16 }}>No campaigns yet</p>
                  <button onClick={() => setView('create')} style={{ background: '#6366f1', color: 'white', border: 'none', padding: '10px 20px', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}>Create First Campaign</button>
                </div>
              ) : campaigns.map(c => {
                const sc = STATUS_CONFIG[c.status] || STATUS_CONFIG.draft
                return (
                  <div key={c.id} onClick={() => viewCampaign(c.id)} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '14px 0', borderBottom: '1px solid rgba(255,255,255,0.06)',
                    cursor: 'pointer', gap: 12, flexWrap: 'wrap'
                  }}>
                    <div>
                      <p style={{ color: 'white', fontWeight: 600, fontSize: 14, margin: 0 }}>{c.name}</p>
                      <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, margin: '2px 0 0' }}>{c.template} · {c.total_sent} sent</p>
                    </div>
                    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                      <div style={{ textAlign: 'center' }}>
                        <p style={{ color: '#ef4444', fontWeight: 700, fontSize: 16, margin: 0 }}>{c.click_rate}%</p>
                        <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 10, margin: 0 }}>clicked</p>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <p style={{ color: '#10b981', fontWeight: 700, fontSize: 16, margin: 0 }}>{c.report_rate}%</p>
                        <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 10, margin: 0 }}>reported</p>
                      </div>
                      <span style={{ background: sc.color + '22', color: sc.color, padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600 }}>{sc.label}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Templates */}
        {view === 'templates' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: 16 }}>
            {templates.map(t => {
              const dc = DIFFICULTY_CONFIG[t.difficulty] || DIFFICULTY_CONFIG.medium
              return (
                <div key={t.id} style={{ ...card, cursor: 'pointer', transition: 'border-color 0.2s' }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = dc.color + '60'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
                  onClick={() => setSelectedTemplate(selectedTemplate?.id === t.id ? null : t)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13 }}>{CATEGORY_LABELS[t.category] || t.category}</span>
                    <span style={{ background: dc.color + '22', color: dc.color, padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600 }}>{dc.label}</span>
                  </div>
                  <h3 style={{ color: 'white', fontWeight: 700, fontSize: 15, marginBottom: 6 }}>{t.name}</h3>
                  <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, marginBottom: 12 }}>{t.description}</p>
                  <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, marginBottom: 4 }}>From: {t.sender_name} &lt;{t.sender_email}&gt;</p>
                  <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11 }}>Subject: {t.subject}</p>
                  {selectedTemplate?.id === t.id && t.red_flags && (
                    <div style={{ marginTop: 12, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, padding: 12 }}>
                      <p style={{ color: '#ef4444', fontSize: 11, fontWeight: 700, marginBottom: 6 }}>🚩 Red Flags</p>
                      {t.red_flags.map((f, i) => <p key={i} style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, margin: '2px 0' }}>• {f}</p>)}
                    </div>
                  )}
                  <button onClick={e => { e.stopPropagation(); setForm(f => ({ ...f, template_id: t.id })); setView('create') }}
                    style={{ marginTop: 12, width: '100%', padding: '8px 0', borderRadius: 8, background: '#6366f1', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>
                    Use This Template →
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Create Campaign */}
        {view === 'create' && (
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <div style={card}>
              <h2 style={{ color: 'white', fontWeight: 700, marginBottom: 24 }}>New Phishing Campaign</h2>
              <label style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>Campaign Name</label>
              <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Q1 2025 Staff Awareness Test"
                style={{ width: '100%', padding: '10px 14px', borderRadius: 8, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: 'white', fontSize: 14, marginBottom: 20, boxSizing: 'border-box', outline: 'none' }} />

              <label style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>Phishing Template</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 20 }}>
                {templates.map(t => {
                  const dc = DIFFICULTY_CONFIG[t.difficulty] || DIFFICULTY_CONFIG.medium
                  return (
                    <div key={t.id} onClick={() => setForm(f => ({ ...f, template_id: t.id }))}
                      style={{
                        padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                        border: '1px solid', transition: 'all 0.15s',
                        borderColor: form.template_id === t.id ? '#6366f1' : 'rgba(255,255,255,0.08)',
                        background: form.template_id === t.id ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.03)',
                      }}>
                      <p style={{ color: 'white', fontWeight: 600, fontSize: 12, margin: 0 }}>{t.name}</p>
                      <p style={{ color: dc.color, fontSize: 11, margin: '2px 0 0' }}>{CATEGORY_LABELS[t.category]} · {dc.label}</p>
                    </div>
                  )
                })}
              </div>

              <label style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                Target Emails <span style={{ color: 'rgba(255,255,255,0.3)', fontWeight: 400 }}>(one per line or comma-separated)</span>
              </label>
              <textarea value={form.emails} onChange={e => setForm(f => ({ ...f, emails: e.target.value }))}
                placeholder="john.smith@company.com&#10;jane.doe@company.com"
                rows={5}
                style={{ width: '100%', padding: '10px 14px', borderRadius: 8, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: 'white', fontSize: 13, marginBottom: 16, boxSizing: 'border-box', outline: 'none', resize: 'vertical', fontFamily: 'monospace' }} />

              <label style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                Target Names <span style={{ color: 'rgba(255,255,255,0.3)', fontWeight: 400 }}>(optional — same order as emails)</span>
              </label>
              <textarea value={form.names} onChange={e => setForm(f => ({ ...f, names: e.target.value }))}
                placeholder="John Smith&#10;Jane Doe"
                rows={3}
                style={{ width: '100%', padding: '10px 14px', borderRadius: 8, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: 'white', fontSize: 13, marginBottom: 24, boxSizing: 'border-box', outline: 'none', resize: 'vertical', fontFamily: 'monospace' }} />

              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={handleCreate} disabled={loading}
                  style={{ flex: 1, padding: '12px 0', borderRadius: 8, background: '#6366f1', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 15 }}>
                  {loading ? 'Creating…' : 'Create Campaign →'}
                </button>
                <button onClick={() => setView('dashboard')}
                  style={{ padding: '12px 20px', borderRadius: 8, background: 'rgba(255,255,255,0.06)', color: 'white', border: '1px solid rgba(255,255,255,0.12)', cursor: 'pointer', fontWeight: 600 }}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Campaign Detail */}
        {view === 'campaign' && selectedCampaign && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 8 }}>
              <div>
                <button onClick={() => setView('dashboard')} style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.6)', border: '1px solid rgba(255,255,255,0.1)', padding: '6px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13, marginBottom: 8 }}>← Back</button>
                <h2 style={{ color: 'white', fontWeight: 700, fontSize: 20, margin: 0 }}>{selectedCampaign.name}</h2>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                {selectedCampaign.status === 'draft' && (
                  <button onClick={() => handleSend(selectedCampaign.id)} disabled={loading}
                    style={{ background: '#6366f1', color: 'white', border: 'none', padding: '10px 20px', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}>
                    🚀 Send Campaign
                  </button>
                )}
                <button onClick={() => handleDelete(selectedCampaign.id)}
                  style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)', padding: '10px 20px', borderRadius: 8, cursor: 'pointer', fontWeight: 600 }}>
                  Delete
                </button>
              </div>
            </div>

            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))', gap: 12, marginBottom: 20 }}>
              {[
                { label: 'Sent', value: selectedCampaign.stats.total_sent, color: '#818cf8' },
                { label: 'Clicked', value: selectedCampaign.stats.total_clicked, color: '#ef4444' },
                { label: 'Reported', value: selectedCampaign.stats.total_reported, color: '#10b981' },
                { label: 'Click Rate', value: `${selectedCampaign.stats.click_rate}%`, color: '#fbbf24' },
                { label: 'Report Rate', value: `${selectedCampaign.stats.report_rate}%`, color: '#34d399' },
              ].map(k => (
                <div key={k.label} style={{ ...card, padding: '14px 18px', textAlign: 'center' }}>
                  <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11, textTransform: 'uppercase', margin: '0 0 4px' }}>{k.label}</p>
                  <p style={{ color: k.color, fontSize: 24, fontWeight: 800, margin: 0 }}>{k.value}</p>
                </div>
              ))}
            </div>

            {/* Red flags */}
            {selectedCampaign.template?.red_flags && (
              <div style={{ ...card, marginBottom: 20, borderColor: 'rgba(239,68,68,0.2)' }}>
                <p style={{ color: '#ef4444', fontWeight: 700, marginBottom: 10 }}>🚩 Template Red Flags — {selectedCampaign.template.name}</p>
                {selectedCampaign.template.red_flags.map((f, i) => (
                  <p key={i} style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, margin: '4px 0' }}>• {f}</p>
                ))}
              </div>
            )}

            {/* Targets table */}
            <div style={card}>
              <h3 style={{ color: 'white', fontWeight: 700, marginBottom: 16 }}>Targets ({selectedCampaign.targets.length})</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    {['Name', 'Email', 'Status', 'Clicked', 'Reported', 'Training'].map(h => (
                      <th key={h} style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, textAlign: 'left', paddingBottom: 10, paddingRight: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {selectedCampaign.targets.map(t => {
                    const statusColors = { pending: '#6b7280', sent: '#818cf8', clicked: '#ef4444', reported: '#10b981', ignored: '#6b7280' }
                    return (
                      <tr key={t.id} style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                        <td style={{ padding: '10px 12px 10px 0', color: 'white', fontSize: 13 }}>{t.name || '—'}</td>
                        <td style={{ padding: '10px 12px 10px 0', color: 'rgba(255,255,255,0.6)', fontSize: 13 }}>{t.email}</td>
                        <td style={{ padding: '10px 12px 10px 0' }}>
                          <span style={{ background: (statusColors[t.status] || '#6b7280') + '22', color: statusColors[t.status] || '#6b7280', padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600, textTransform: 'capitalize' }}>{t.status}</span>
                        </td>
                        <td style={{ padding: '10px 12px 10px 0', color: 'rgba(255,255,255,0.4)', fontSize: 12 }}>{t.clicked_at ? new Date(t.clicked_at).toLocaleTimeString('en-GB') : '—'}</td>
                        <td style={{ padding: '10px 12px 10px 0', color: 'rgba(255,255,255,0.4)', fontSize: 12 }}>{t.reported_at ? new Date(t.reported_at).toLocaleTimeString('en-GB') : '—'}</td>
                        <td style={{ padding: '10px 0', color: t.training_completed ? '#10b981' : 'rgba(255,255,255,0.3)', fontSize: 12 }}>{t.training_completed ? '✓ Done' : '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
