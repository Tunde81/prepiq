import { useEffect, useState } from 'react'
import { Settings, Users, BookOpen, BarChart2, Plus, Edit2, Eye, EyeOff, X, Save, Terminal, Sparkles, Loader, Upload, FileQuestion } from 'lucide-react'
import api from '../utils/api'

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-forge-surface border border-forge-border rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-forge-border flex-shrink-0">
          <h2 className="font-mono font-bold text-forge-text">{title}</h2>
          <button onClick={onClose} className="p-1.5 text-forge-muted hover:text-forge-text rounded-lg hover:bg-forge-border transition-colors"><X size={16} /></button>
        </div>
        <div className="overflow-y-auto flex-1 px-6 py-4">{children}</div>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div className="mb-4">
      <label className="block text-xs font-mono text-forge-muted uppercase tracking-wider mb-1.5">{label}</label>
      {children}
    </div>
  )
}

function Input({ ...props }) {
  return <input {...props} className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text placeholder-forge-muted focus:outline-none focus:border-forge-accent transition-colors" />
}

function Textarea({ ...props }) {
  return <textarea {...props} rows={3} className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text placeholder-forge-muted focus:outline-none focus:border-forge-accent transition-colors resize-none" />
}

function Select({ children, ...props }) {
  return (
    <select {...props} className="w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-sm text-forge-text focus:outline-none focus:border-forge-accent transition-colors">
      {children}
    </select>
  )
}

const EMPTY_MODULE = { title: '', slug: '', description: '', category: 'awareness', difficulty: 'beginner', duration_minutes: 15, order_index: 0, is_published: false }

function ModuleForm({ initial, onSave, onClose }) {
  const [form, setForm] = useState(initial || EMPTY_MODULE)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const [generating, setGenerating] = useState(false)
  const [topic, setTopic] = useState('')

  const generateWithAI = async () => {
    if (!topic.trim()) return
    setGenerating(true)
    try {
      const res = await api.post('/coach/generate', { topic, type: 'module' })
      setForm(f => ({ ...f, ...res.data }))
    } catch (e) { console.error(e) }
    finally { setGenerating(false) }
  }

  const handleSave = async () => {
    if (!form.title || !form.slug) return setError('Title and slug are required')
    setSaving(true); setError('')
    try {
      initial?.id ? await api.put('/admin/modules/' + initial.id, form) : await api.post('/admin/modules', form)
      onSave()
    } catch (e) { setError(e.response?.data?.detail || 'Save failed') }
    finally { setSaving(false) }
  }

  return (
    <>
      <div className="flex gap-2 mb-5 p-3 bg-forge-accent/5 border border-forge-accent/20 rounded-xl">
        <Input value={topic} onChange={e => setTopic(e.target.value)} onKeyDown={e => e.key === 'Enter' && generateWithAI()} placeholder="Enter topic to auto-fill with AI (e.g. Social Engineering)..." />
        <button onClick={generateWithAI} disabled={generating || !topic.trim()} className="flex items-center gap-2 px-4 py-2 bg-forge-accent text-forge-bg rounded-lg text-sm font-mono font-bold disabled:opacity-40 whitespace-nowrap hover:opacity-90 transition-all">
          {generating ? <Loader size={13} className="animate-spin" /> : <Sparkles size={13} />}{generating ? 'Generating...' : 'Generate'}
        </button>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Title"><Input value={form.title} onChange={e => { set('title', e.target.value); set('slug', e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')) }} placeholder="e.g. Phishing Awareness" /></Field>
        <Field label="Slug"><Input value={form.slug} onChange={e => set('slug', e.target.value)} placeholder="e.g. phishing-awareness" /></Field>
      </div>
      <Field label="Description"><Textarea value={form.description} onChange={e => set('description', e.target.value)} placeholder="Brief description..." /></Field>
      <div className="grid grid-cols-3 gap-4">
        <Field label="Category"><Select value={form.category} onChange={e => set('category', e.target.value)}><option value="awareness">Awareness</option><option value="technical">Technical</option><option value="compliance">Compliance</option><option value="incident-response">Incident Response</option></Select></Field>
        <Field label="Difficulty"><Select value={form.difficulty} onChange={e => set('difficulty', e.target.value)}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></Select></Field>
        <Field label="Duration (mins)"><Input type="number" value={form.duration_minutes} onChange={e => set('duration_minutes', parseInt(e.target.value))} min={5} max={120} /></Field>
      </div>
      <label className="flex items-center gap-2 cursor-pointer mt-2">
        <input type="checkbox" checked={form.is_published} onChange={e => set('is_published', e.target.checked)} className="w-4 h-4 rounded accent-forge-accent" />
        <span className="text-sm text-forge-text">Published</span>
      </label>
      {error && <p className="mt-3 text-xs text-red-400 font-mono">{error}</p>}
      <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-forge-border">
        <button onClick={onClose} className="px-4 py-2 text-sm text-forge-muted border border-forge-border rounded-lg">Cancel</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2"><Save size={14} />{saving ? 'Saving...' : 'Save Module'}</button>
      </div>
    </>
  )
}

const EMPTY_SCENARIO = { title: '', slug: '', description: '', category: 'phishing', difficulty: 'beginner', duration_minutes: 20, objectives: [], hints: [], steps: [], is_published: false }

function ScenarioForm({ initial, onSave, onClose }) {
  const [form, setForm] = useState(initial || EMPTY_SCENARIO)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [objInput, setObjInput] = useState('')
  const [hintInput, setHintInput] = useState('')
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const [generating, setGenerating] = useState(false)
  const [topic, setTopic] = useState('')
  const generateWithAI = async () => {
    if (!topic.trim()) return
    setGenerating(true)
    try {
      const res = await api.post('/coach/generate', { topic, type: 'scenario' })
      setForm(f => ({ ...f, ...res.data }))
    } catch (e) { console.error(e) }
    finally { setGenerating(false) }
  }
  const addObj = () => { if (objInput.trim()) { set('objectives', [...form.objectives, objInput.trim()]); setObjInput('') } }
  const addHint = () => { if (hintInput.trim()) { set('hints', [...form.hints, hintInput.trim()]); setHintInput('') } }

  const handleSave = async () => {
    if (!form.title || !form.slug) return setError('Title and slug are required')
    setSaving(true); setError('')
    try {
      initial?.id ? await api.put('/admin/scenarios/' + initial.id, form) : await api.post('/admin/scenarios', form)
      onSave()
    } catch (e) { setError(e.response?.data?.detail || 'Save failed') }
    finally { setSaving(false) }
  }

  return (
    <>
      <div className="flex gap-2 mb-5 p-3 bg-forge-accent/5 border border-forge-accent/20 rounded-xl">
        <Input value={topic} onChange={e => setTopic(e.target.value)} onKeyDown={e => e.key === 'Enter' && generateWithAI()} placeholder="Enter topic to auto-fill with AI (e.g. Ransomware Attack)..." />
        <button onClick={generateWithAI} disabled={generating || !topic.trim()} className="flex items-center gap-2 px-4 py-2 bg-forge-accent text-forge-bg rounded-lg text-sm font-mono font-bold disabled:opacity-40 whitespace-nowrap hover:opacity-90 transition-all">
          {generating ? <Loader size={13} className="animate-spin" /> : <Sparkles size={13} />}{generating ? 'Generating...' : 'Generate'}
        </button>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Title"><Input value={form.title} onChange={e => { set('title', e.target.value); set('slug', e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')) }} placeholder="e.g. Ransomware Response" /></Field>
        <Field label="Slug"><Input value={form.slug} onChange={e => set('slug', e.target.value)} placeholder="e.g. ransomware-response" /></Field>
      </div>
      <Field label="Description"><Textarea value={form.description} onChange={e => set('description', e.target.value)} placeholder="What will users learn..." /></Field>
      <div className="grid grid-cols-3 gap-4">
        <Field label="Category"><Select value={form.category} onChange={e => set('category', e.target.value)}><option value="phishing">Phishing</option><option value="ransomware">Ransomware</option><option value="cloud">Cloud Security</option><option value="social-engineering">Social Engineering</option><option value="incident-response">Incident Response</option></Select></Field>
        <Field label="Difficulty"><Select value={form.difficulty} onChange={e => set('difficulty', e.target.value)}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></Select></Field>
        <Field label="Duration (mins)"><Input type="number" value={form.duration_minutes} onChange={e => set('duration_minutes', parseInt(e.target.value))} min={5} max={120} /></Field>
      </div>
      <Field label="Learning Objectives">
        <div className="flex gap-2 mb-2">
          <Input value={objInput} onChange={e => setObjInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && addObj()} placeholder="Add objective and press Enter" />
          <button onClick={addObj} className="px-3 py-2 bg-forge-accent/10 border border-forge-accent/30 text-forge-accent rounded-lg text-sm">Add</button>
        </div>
        {form.objectives.map((o, i) => (
          <div key={i} className="flex items-center justify-between bg-forge-bg border border-forge-border rounded-lg px-3 py-1.5 text-xs text-forge-text mb-1">
            <span>- {o}</span>
            <button onClick={() => set('objectives', form.objectives.filter((_, idx) => idx !== i))} className="text-forge-muted hover:text-red-400"><X size={12} /></button>
          </div>
        ))}
      </Field>
      <Field label="Hints">
        <div className="flex gap-2 mb-2">
          <Input value={hintInput} onChange={e => setHintInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && addHint()} placeholder="Add a hint and press Enter" />
          <button onClick={addHint} className="px-3 py-2 bg-forge-accent/10 border border-forge-accent/30 text-forge-accent rounded-lg text-sm">Add</button>
        </div>
        {form.hints.map((h, i) => (
          <div key={i} className="flex items-center justify-between bg-forge-bg border border-forge-border rounded-lg px-3 py-1.5 text-xs text-forge-text mb-1">
            <span>{h}</span>
            <button onClick={() => set('hints', form.hints.filter((_, idx) => idx !== i))} className="text-forge-muted hover:text-red-400"><X size={12} /></button>
          </div>
        ))}
      </Field>
      <label className="flex items-center gap-2 cursor-pointer mt-2">
        <input type="checkbox" checked={form.is_published} onChange={e => set('is_published', e.target.checked)} className="w-4 h-4 rounded accent-forge-accent" />
        <span className="text-sm text-forge-text">Published</span>
      </label>
      {error && <p className="mt-3 text-xs text-red-400 font-mono">{error}</p>}
      <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-forge-border">
        <button onClick={onClose} className="px-4 py-2 text-sm text-forge-muted border border-forge-border rounded-lg">Cancel</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2"><Save size={14} />{saving ? 'Saving...' : 'Save Scenario'}</button>
      </div>
    </>
  )
}

function ContentTab() {
  const [subTab, setSubTab] = useState('modules')
  const [modules, setModules] = useState([])
  const [scenarios, setScenarios] = useState([])
  const [modal, setModal] = useState(null)

  const loadModules = () => api.get('/admin/modules').then(r => setModules(r.data)).catch(() => {})
  const loadScenarios = () => api.get('/admin/scenarios').then(r => setScenarios(r.data)).catch(() => {})
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')

  const handleScormUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setUploadMsg('')
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.post('/import/scorm', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      setUploadMsg('Imported: ' + res.data.module_title + ' (' + res.data.lessons_created + ' lessons)')
      loadModules()
    } catch (e) {
      setUploadMsg('Import failed: ' + (e.response?.data?.detail || 'Unknown error'))
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const [quizMsg, setQuizMsg] = useState('')
  const [generatingQuiz, setGeneratingQuiz] = useState(null)

  const generateQuiz = async (module) => {
    setGeneratingQuiz(module.id)
    setQuizMsg('')
    try {
      const res = await api.post('/coach/generate-quiz', { module_id: module.id, num_questions: 5 })
      setQuizMsg('Quiz generated for: ' + module.title + ' (' + res.data.created + ' questions)')
    } catch (e) {
      setQuizMsg('Quiz generation failed: ' + (e.response?.data?.detail || 'Unknown error'))
    } finally {
      setGeneratingQuiz(null)
    }
  }

  useEffect(() => { loadModules(); loadScenarios() }, [])

  const togglePublish = async (type, item) => {
    const ep = type === 'module' ? '/admin/modules/' + item.id : '/admin/scenarios/' + item.id
    await api.put(ep, { ...item, is_published: !item.is_published })
    type === 'module' ? loadModules() : loadScenarios()
  }

  const diffBadge = (d) => {
    const c = { beginner: 'text-green-400 bg-green-900/20 border-green-800', intermediate: 'text-yellow-400 bg-yellow-900/20 border-yellow-800', advanced: 'text-red-400 bg-red-900/20 border-red-800' }
    return <span className={'text-xs font-mono px-2 py-0.5 rounded border ' + (c[d] || 'text-forge-muted border-forge-border')}>{d}</span>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-1 bg-forge-bg border border-forge-border rounded-lg p-1">
          {[{ id: 'modules', Icon: BookOpen, label: 'Modules' }, { id: 'scenarios', Icon: Terminal, label: 'Simulations' }].map(({ id, Icon, label }) => (
            <button key={id} onClick={() => setSubTab(id)} className={'flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-mono transition-all ' + (subTab === id ? 'bg-forge-accent text-forge-bg font-bold' : 'text-forge-muted hover:text-forge-text')}>
              <Icon size={13} />{label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {subTab === 'modules' && (
            <label className={`flex items-center gap-2 px-4 py-2 border border-forge-accent/30 text-forge-accent rounded-lg text-sm font-mono cursor-pointer hover:bg-forge-accent/10 transition-all ${uploading ? 'opacity-50' : ''}`}>
              {uploading ? <Loader size={13} className="animate-spin" /> : <Upload size={13} />}
              {uploading ? 'Importing...' : 'Import SCORM'}
              <input type="file" accept=".zip" onChange={handleScormUpload} className="hidden" disabled={uploading} />
            </label>
          )}
          <button onClick={() => setModal({ type: subTab === 'modules' ? 'module' : 'scenario', data: null })} className="btn-primary flex items-center gap-2 text-sm">
            <Plus size={14} />New {subTab === 'modules' ? 'Module' : 'Scenario'}
          </button>
        </div>
        {uploadMsg && <p className={'text-xs font-mono mt-2 ' + (uploadMsg.startsWith('Import failed') ? 'text-red-400' : 'text-green-400')}>{uploadMsg}</p>}
        {quizMsg && <p className={'text-xs font-mono mt-2 ' + (quizMsg.startsWith('Quiz generation failed') ? 'text-red-400' : 'text-purple-400')}>{quizMsg}</p>}
      </div>

      {subTab === 'modules' && (
        <div className="space-y-3">
          {modules.length === 0 && <p className="text-center py-12 text-forge-muted font-mono text-sm">No modules yet</p>}
          {modules.map(m => (
            <div key={m.id} className="card flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-10 h-10 rounded-lg bg-forge-accent/10 border border-forge-accent/20 flex items-center justify-center flex-shrink-0"><BookOpen size={16} className="text-forge-accent" /></div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-forge-text truncate">{m.title}</div>
                  <div className="text-xs text-forge-muted font-mono">{m.slug} · {m.duration_minutes}min</div>
                </div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                {diffBadge(m.difficulty)}
                <span className={'text-xs font-mono px-2 py-0.5 rounded border ' + (m.is_published ? 'text-green-400 bg-green-900/20 border-green-800' : 'text-forge-muted border-forge-border')}>{m.is_published ? 'Published' : 'Draft'}</span>
                <button onClick={() => togglePublish('module', m)} className="p-1.5 text-forge-muted hover:text-forge-accent rounded-lg hover:bg-forge-border transition-colors">{m.is_published ? <EyeOff size={14} /> : <Eye size={14} />}</button>
                <button onClick={() => generateQuiz(m)} disabled={generatingQuiz === m.id} className="p-1.5 text-forge-muted hover:text-purple-400 rounded-lg hover:bg-forge-border transition-colors" title="Generate Quiz">{generatingQuiz === m.id ? <Loader size={14} className="animate-spin" /> : <FileQuestion size={14} />}</button>
                <button onClick={() => setModal({ type: 'module', data: m })} className="p-1.5 text-forge-muted hover:text-forge-accent rounded-lg hover:bg-forge-border transition-colors"><Edit2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      )}

      {subTab === 'scenarios' && (
        <div className="space-y-3">
          {scenarios.length === 0 && <p className="text-center py-12 text-forge-muted font-mono text-sm">No scenarios yet</p>}
          {scenarios.map(s => (
            <div key={s.id} className="card flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-10 h-10 rounded-lg bg-purple-900/20 border border-purple-800/30 flex items-center justify-center flex-shrink-0"><Terminal size={16} className="text-purple-400" /></div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-forge-text truncate">{s.title}</div>
                  <div className="text-xs text-forge-muted font-mono">{s.slug} · {s.duration_minutes}min · {s.objectives?.length || 0} objectives</div>
                </div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                {diffBadge(s.difficulty)}
                <span className={'text-xs font-mono px-2 py-0.5 rounded border ' + (s.is_published ? 'text-green-400 bg-green-900/20 border-green-800' : 'text-forge-muted border-forge-border')}>{s.is_published ? 'Published' : 'Draft'}</span>
                <button onClick={() => togglePublish('scenario', s)} className="p-1.5 text-forge-muted hover:text-forge-accent rounded-lg hover:bg-forge-border transition-colors">{s.is_published ? <EyeOff size={14} /> : <Eye size={14} />}</button>
                <button onClick={() => setModal({ type: 'scenario', data: s })} className="p-1.5 text-forge-muted hover:text-forge-accent rounded-lg hover:bg-forge-border transition-colors"><Edit2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal?.type === 'module' && <Modal title={modal.data ? 'Edit Module' : 'New Module'} onClose={() => setModal(null)}><ModuleForm initial={modal.data} onSave={() => { setModal(null); loadModules() }} onClose={() => setModal(null)} /></Modal>}
      {modal?.type === 'scenario' && <Modal title={modal.data ? 'Edit Scenario' : 'New Scenario'} onClose={() => setModal(null)}><ScenarioForm initial={modal.data} onSave={() => { setModal(null); loadScenarios() }} onClose={() => setModal(null)} /></Modal>}
    </div>
  )
}

export default function AdminPanel() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [tab, setTab] = useState('overview')

  useEffect(() => {
    api.get('/analytics/admin/platform').then(r => setStats(r.data)).catch(() => {})
    if (tab === 'users') api.get('/admin/users').then(r => setUsers(r.data)).catch(() => {})
  }, [tab])

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <Settings size={14} className="text-forge-accent" /><span>PREPIQ / ADMIN</span>
        </div>
        <h1 className="text-2xl font-bold text-forge-text">Admin Panel</h1>
      </div>
      <div className="flex gap-1 mb-8 border-b border-forge-border">
        {[{ id: 'overview', label: 'Overview', Icon: BarChart2 }, { id: 'users', label: 'Users', Icon: Users }, { id: 'content', label: 'Content', Icon: BookOpen }].map(({ id, label, Icon }) => (
          <button key={id} onClick={() => setTab(id)} className={'flex items-center gap-2 px-4 py-2.5 text-sm font-mono border-b-2 transition-all ' + (tab === id ? 'border-forge-accent text-forge-accent' : 'border-transparent text-forge-muted hover:text-forge-text')}>
            <Icon size={14} />{label}
          </button>
        ))}
      </div>

      {tab === 'overview' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Users', value: stats.users.total, sub: stats.users.active + ' active' },
            { label: 'Assessments Run', value: stats.assessments.total, sub: 'Avg: ' + stats.assessments.avg_score + '/100' },
            { label: 'Module Completions', value: stats.learning.module_completions },
            { label: 'Simulations Done', value: stats.simulations.completed },
          ].map(({ label, value, sub }) => (
            <div key={label} className="stat-card">
              <div className="stat-label">{label}</div>
              <div className="stat-value">{value ?? '0'}</div>
              {sub && <div className="text-xs text-forge-muted font-mono">{sub}</div>}
            </div>
          ))}
        </div>
      )}

      {tab === 'users' && (
        <>
        <div className="mb-4 grid grid-cols-3 gap-3">
          {[
            { label: 'Total Users', value: users.length, color: 'text-forge-accent' },
            { label: 'Verified', value: users.filter(u => u.is_verified).length, color: 'text-green-400' },
            { label: 'Pending Verification', value: users.filter(u => !u.is_verified).length, color: 'text-yellow-400' },
          ].map(stat => (
            <div key={stat.label} className="card py-3 px-4">
              <p className="text-xs font-mono text-forge-muted uppercase tracking-wider mb-1">{stat.label}</p>
              <p className={`text-2xl font-bold font-mono ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-forge-border text-left">
                {['ID', 'Name', 'Email', 'Role', 'Active', 'Verified', 'Joined', 'Last Login'].map(h => (
                  <th key={h} className="pb-3 text-xs font-mono text-forge-muted uppercase tracking-wider pr-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-forge-border">
              {users.map(u => (
                <tr key={u.id} className="text-forge-muted text-xs hover:bg-white/5 transition-colors">
                  <td className="py-3 pr-4 font-mono text-forge-accent">{u.id}</td>
                  <td className="py-3 pr-4 text-forge-text font-medium">{u.full_name || '-'}</td>
                  <td className="py-3 pr-4">{u.email}</td>
                  <td className="py-3 pr-4"><span className="badge-blue font-mono uppercase text-xs">{u.role}</span></td>
                  <td className="py-3 pr-4">
                    <span className={u.is_active ? 'text-green-400 font-mono' : 'text-red-400 font-mono'}>
                      {u.is_active ? '● Active' : '● Inactive'}
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    <span className={u.is_verified ? 'text-green-400 font-mono' : 'text-yellow-400 font-mono'}>
                      {u.is_verified ? '✓ Yes' : '⏳ Pending'}
                    </span>
                  </td>
                  <td className="py-3 pr-4">{new Date(u.created_at).toLocaleDateString('en-GB')}</td>
                  <td className="py-3">{u.last_login ? new Date(u.last_login).toLocaleDateString('en-GB') : <span className="text-forge-muted/40">Never</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {users.length === 0 && <p className="text-center py-8 text-forge-muted font-mono text-sm">No users found</p>}
        </div>
        </>
      )}

      {tab === 'content' && <ContentTab />}
    </div>
  )
}