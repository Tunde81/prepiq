import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ClipboardCheck, ChevronRight, ChevronLeft, Info } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../utils/api'

const SCORE_LABELS = [
  { value: 0, label: 'Not implemented', color: 'text-forge-red' },
  { value: 1, label: 'Partially implemented', color: 'text-forge-orange' },
  { value: 2, label: 'Mostly implemented', color: 'text-forge-yellow' },
  { value: 3, label: 'Fully implemented', color: 'text-forge-green' },
]

export default function Assessment() {
  const [domains, setDomains] = useState([])
  const [step, setStep] = useState(0) // 0 = intro, 1..N = domains, N+1 = submit
  const [orgName, setOrgName] = useState('')
  const [orgSector, setOrgSector] = useState('')
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/assessment/domains').then(r => setDomains(r.data)).finally(() => setLoading(false))
  }, [])

  const setAnswer = (questionId, score) => {
    setAnswers(prev => ({ ...prev, [String(questionId)]: score }))
  }

  const currentDomain = domains[step - 1]
  const totalDomains = domains.length
  const progress = step === 0 ? 0 : Math.round((step / (totalDomains + 1)) * 100)

  const domainComplete = (domain) => domain?.questions?.every(q => answers[String(q.id)] !== undefined)

  const handleSubmit = async () => {
    if (!orgName) return toast.error('Please enter your organisation name')
    const totalQ = domains.reduce((sum, d) => sum + d.questions.length, 0)
    if (Object.keys(answers).length < totalQ) return toast.error('Please answer all questions')

    setSubmitting(true)
    try {
      const res = await api.post('/assessment/submit', {
        organisation_name: orgName,
        organisation_sector: orgSector,
        answers,
      })
      toast.success('Assessment complete!')
      navigate(`/assessment/result/${res.data.id}`)
    } catch {
      toast.error('Failed to submit assessment')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20">
      <div className="text-forge-accent font-mono text-sm animate-pulse">Loading assessment...</div>
    </div>
  )

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <ClipboardCheck size={14} className="text-forge-accent" />
          <span>PREPIQ / RISK ASSESSMENT</span>
        </div>
        <h1 className="text-2xl font-bold text-forge-text">Cyber Risk Assessment</h1>
        <p className="text-forge-muted text-sm mt-1">8-domain assessment · ~15 minutes · Generates PDF report</p>
      </div>

      {/* Progress */}
      {step > 0 && (
        <div className="mb-6">
          <div className="flex justify-between text-xs font-mono text-forge-muted mb-2">
            <span>Domain {step} of {totalDomains}</span>
            <span>{progress}% complete</span>
          </div>
          <div className="h-1.5 bg-forge-border rounded-full overflow-hidden">
            <div className="h-full bg-forge-accent rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {/* Step 0: Intro */}
      {step === 0 && (
        <div className="card">
          <h2 className="font-semibold text-forge-text mb-4">Organisation Details</h2>
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-xs font-mono text-forge-muted mb-1.5 uppercase tracking-wider">Organisation Name *</label>
              <input value={orgName} onChange={e => setOrgName(e.target.value)} className="input-field" placeholder="Acme Ltd" />
            </div>
            <div>
              <label className="block text-xs font-mono text-forge-muted mb-1.5 uppercase tracking-wider">Sector</label>
              <select value={orgSector} onChange={e => setOrgSector(e.target.value)} className="input-field">
                <option value="">Select sector</option>
                {['Financial Services', 'Healthcare', 'Education', 'Retail', 'Manufacturing', 'Technology', 'Public Sector', 'Professional Services', 'Other'].map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="bg-forge-border/30 rounded-lg p-4 mb-6 text-xs text-forge-muted space-y-1">
            <p>✓ 8 domains — Network, Identity, Data, IR, Endpoints, Awareness, Vulnerability, Third-Party</p>
            <p>✓ Each question scored 0 (not implemented) to 3 (fully implemented)</p>
            <p>✓ PDF report generated at the end for sharing with stakeholders</p>
          </div>
          <button onClick={() => { if (!orgName) return toast.error('Enter organisation name'); setStep(1) }} className="btn-primary flex items-center gap-2">
            Start Assessment <ChevronRight size={16} />
          </button>
        </div>
      )}

      {/* Domain steps */}
      {step > 0 && step <= totalDomains && currentDomain && (
        <div className="card">
          <div className="mb-6">
            <div className="text-xs font-mono text-forge-accent mb-1">DOMAIN {step}/{totalDomains}</div>
            <h2 className="text-lg font-bold text-forge-text">{currentDomain.name}</h2>
            <p className="text-sm text-forge-muted mt-1">{currentDomain.description}</p>
          </div>

          <div className="space-y-6">
            {currentDomain.questions.map((q, qi) => (
              <div key={q.id}>
                <div className="flex items-start gap-2 mb-3">
                  <span className="text-forge-accent font-mono text-xs mt-0.5 flex-shrink-0">Q{qi + 1}</span>
                  <p className="text-sm text-forge-text">{q.text}</p>
                </div>
                {q.guidance && (
                  <div className="flex gap-1.5 text-xs text-forge-muted mb-3 ml-5">
                    <Info size={11} className="flex-shrink-0 mt-0.5" />
                    {q.guidance}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-2 ml-5">
                  {SCORE_LABELS.map(({ value, label, color }) => (
                    <button
                      key={value}
                      onClick={() => setAnswer(q.id, value)}
                      className={`text-left px-3 py-2 rounded-lg border text-xs transition-all ${
                        answers[String(q.id)] === value
                          ? 'border-forge-accent bg-forge-accent/10 text-forge-accent'
                          : 'border-forge-border text-forge-muted hover:border-forge-accent/50'
                      }`}
                    >
                      <span className="font-mono mr-1">{value}</span>
                      <span className={answers[String(q.id)] === value ? '' : color}>{label}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between mt-8">
            <button onClick={() => setStep(s => s - 1)} className="btn-ghost flex items-center gap-2">
              <ChevronLeft size={16} /> Previous
            </button>
            <button
              onClick={() => {
                if (!domainComplete(currentDomain)) return toast.error('Please answer all questions in this domain')
                setStep(s => s + 1)
              }}
              className="btn-primary flex items-center gap-2"
            >
              {step < totalDomains ? 'Next Domain' : 'Review & Submit'} <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Submit review */}
      {step === totalDomains + 1 && (
        <div className="card">
          <h2 className="font-semibold text-forge-text mb-4">Ready to Submit</h2>
          <div className="space-y-2 mb-6">
            {domains.map((d, i) => (
              <div key={d.id} className="flex items-center justify-between text-sm">
                <span className="text-forge-muted">{d.name}</span>
                <span className="text-forge-green font-mono text-xs">✓ Complete</span>
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => setStep(totalDomains)} className="btn-ghost flex items-center gap-2">
              <ChevronLeft size={16} /> Back
            </button>
            <button onClick={handleSubmit} className="btn-primary flex-1" disabled={submitting}>
              {submitting ? 'Generating report...' : 'Generate Risk Report'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
