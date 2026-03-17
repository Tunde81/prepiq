import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Lightbulb, CheckCircle, Terminal, Target } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../utils/api'

const ACTIONS_MAP = {
  check_sender: 'Check Sender Domain',
  inspect_headers: 'Inspect Email Headers',
  verify_out_of_band: 'Verify via Phone/Separate Channel',
  contact_ceo_directly: 'Contact CEO Directly',
  report_to_it: 'Report to IT/Security Team',
  report_to_security_team: 'Report to Security Team',
  do_not_click: 'Do Not Click Any Links',
  isolate_machine: 'Isolate the Machine from Network',
  disconnect_network: 'Disconnect Network Cable/Wi-Fi',
  preserve_logs: 'Preserve System Logs',
  take_memory_snapshot: 'Take Memory Snapshot',
  notify_ir_team: 'Notify Incident Response Team',
  check_network_shares: 'Check Affected Network Shares',
  review_access_logs: 'Review Access Logs',
  restore_from_backup: 'Restore from Clean Backup',
  verify_backup_integrity: 'Verify Backup Integrity',
  check_bucket_policy: 'Review S3 Bucket Policy',
  review_acls: 'Review Bucket ACLs',
  assess_bucket_contents: 'Assess Data in Bucket',
  identify_gdpr_impact: 'Identify GDPR Impact',
  check_dpa_2018: 'Check UK DPA 2018 Obligations',
  notify_dpo: 'Notify Data Protection Officer',
  enable_block_public_access: 'Enable Block Public Access',
  remove_public_acls: 'Remove Public ACLs',
  apply_restrictive_bucket_policy: 'Apply Restrictive Bucket Policy',
  enable_aws_config_rules: 'Enable AWS Config Rules',
  enable_security_hub: 'Enable AWS Security Hub',
  set_scp_policy: 'Set Service Control Policy',
}

export default function SimulationPlay() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentStep, setCurrentStep] = useState(0)
  const [feedback, setFeedback] = useState(null)
  const [hint, setHint] = useState(null)
  const [completed, setCompleted] = useState(false)
  const [finalScore, setFinalScore] = useState(null)
  const [actionTaken, setActionTaken] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    api.post(`/simulations/scenarios/${id}/start`)
      .then(r => setSession(r.data))
      .catch(e => { toast.error('Failed to start simulation'); navigate('/simulations') })
      .finally(() => setLoading(false))
  }, [id])

  const takeAction = async (action, useHint = false) => {
    if (!session || submitting) return
    setSubmitting(true)
    try {
      const res = await api.post('/simulations/action', {
        session_id: session.session_id,
        step: currentStep,
        action,
        use_hint: useHint,
      })
      setFeedback(res.data.feedback)
      if (res.data.hint) setHint(res.data.hint)
      if (res.data.completed) {
        setCompleted(true)
        setFinalScore(res.data.score)
      } else {
        setCurrentStep(res.data.next_step)
        setActionTaken(true)
      }
    } catch {
      toast.error('Failed to submit action')
    } finally {
      setSubmitting(false)
    }
  }

  const requestHint = async () => {
    const step = session?.scenario?.steps?.[currentStep]
    const correct = step?.correct_actions?.[0]
    if (!correct) return toast.error('No hint available')
    await takeAction(correct, true)
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20">
      <div className="text-forge-accent font-mono text-sm animate-pulse">Initialising simulation environment...</div>
    </div>
  )

  const scenario = session?.scenario
  const steps = scenario?.steps || []
  const step = steps[currentStep]
  const progress = steps.length > 0 ? ((currentStep) / steps.length) * 100 : 0

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <button onClick={() => navigate('/simulations')} className="flex items-center gap-2 text-forge-muted hover:text-forge-text text-sm mb-6 transition-colors">
        <ArrowLeft size={14} />
        Back to Scenarios
      </button>

      {/* Header */}
      <div className="card mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-forge-muted text-xs font-mono mb-1">
              <Terminal size={12} />
              SIMULATION ACTIVE
            </div>
            <h1 className="text-xl font-bold text-forge-text">{scenario?.title}</h1>
          </div>
          {!completed && (
            <div className="text-right">
              <div className="text-xs text-forge-muted font-mono">Step {currentStep + 1} of {steps.length}</div>
              <div className="w-32 h-1.5 bg-forge-border rounded-full mt-2 overflow-hidden">
                <div className="h-full bg-forge-accent rounded-full transition-all" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Objectives */}
      {currentStep === 0 && !actionTaken && !completed && (
        <div className="card mb-6">
          <div className="flex items-center gap-2 text-forge-accent text-sm font-mono mb-3">
            <Target size={14} />
            Learning Objectives
          </div>
          <ul className="space-y-2">
            {scenario?.objectives?.map((obj, i) => (
              <li key={i} className="flex gap-2 text-xs text-forge-muted">
                <span className="text-forge-accent">▸</span>
                {obj}
              </li>
            ))}
          </ul>
        </div>
      )}

      {completed ? (
        /* Completion screen */
        <div className="card text-center py-10">
          <CheckCircle size={48} className="text-forge-green mx-auto mb-4" />
          <h2 className="text-2xl font-bold font-mono text-forge-green mb-2">Simulation Complete</h2>
          <div className="text-5xl font-bold font-mono text-forge-accent my-4">{finalScore}%</div>
          <p className="text-forge-muted text-sm mb-8">
            {finalScore >= 80 ? 'Excellent work! You demonstrated strong incident response skills.' :
             finalScore >= 60 ? 'Good effort. Review the hints and try again to improve.' :
             'Keep practising. Use hints to guide your decisions next time.'}
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate('/simulations')} className="btn-ghost">View All Scenarios</button>
            <button onClick={() => window.location.reload()} className="btn-primary">Try Again</button>
          </div>
        </div>
      ) : step ? (
        /* Active step */
        <div className="space-y-4">
          <div className="card">
            <div className="text-xs font-mono text-forge-accent mb-3">STEP {currentStep + 1} — {step.title?.toUpperCase()}</div>
            <p className="text-forge-text text-sm leading-relaxed">{step.description}</p>

            {feedback && (
              <div className="mt-4 p-3 rounded-lg bg-forge-green/5 border border-forge-green/20 text-xs text-forge-green font-mono">
                ✓ {feedback}
              </div>
            )}

            {hint && (
              <div className="mt-3 p-3 rounded-lg bg-forge-yellow/5 border border-forge-yellow/20 flex gap-2 text-xs text-forge-yellow">
                <Lightbulb size={14} className="flex-shrink-0 mt-0.5" />
                {hint}
              </div>
            )}
          </div>

          {/* Action buttons */}
          {!actionTaken ? (
            <div className="card">
              <div className="text-xs font-mono text-forge-muted mb-3">SELECT YOUR ACTION:</div>
              <div className="grid gap-2">
                {step.correct_actions?.concat(
                  Object.keys(ACTIONS_MAP).filter(a => !step.correct_actions.includes(a)).slice(0, 3)
                ).sort(() => Math.random() - 0.5).map((action) => (
                  <button
                    key={action}
                    onClick={() => takeAction(action)}
                    disabled={submitting}
                    className="text-left px-4 py-3 rounded-lg border border-forge-border text-sm text-forge-muted hover:border-forge-accent hover:text-forge-text transition-all"
                  >
                    <span className="font-mono text-forge-accent mr-2">$</span>
                    {ACTIONS_MAP[action] || action}
                  </button>
                ))}
              </div>
              <button
                onClick={requestHint}
                disabled={submitting}
                className="mt-3 flex items-center gap-1.5 text-xs text-forge-muted hover:text-forge-yellow transition-colors font-mono"
              >
                <Lightbulb size={12} />
                Use hint (−5 points)
              </button>
            </div>
          ) : (
            <button
              onClick={() => { setActionTaken(false); setFeedback(null); setHint(null) }}
              className="btn-primary"
            >
              Continue →
            </button>
          )}
        </div>
      ) : null}
    </div>
  )
}
