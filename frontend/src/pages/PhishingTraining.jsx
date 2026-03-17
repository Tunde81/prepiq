import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../utils/api'

const CATEGORY_LABELS = {
  hmrc: 'HMRC', nhs: 'NHS', natwest: 'NatWest', microsoft: 'Microsoft',
  dvla: 'DVLA', it_helpdesk: 'IT Helpdesk', hr: 'HR',
  ceo_fraud: 'CEO Fraud', delivery: 'Delivery', linkedin: 'LinkedIn'
}

export default function PhishingTraining() {
  const { token } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/phishing/training/${token}`)
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [token])

  if (loading) return (
    <div style={{ minHeight: '100vh', background: '#0f1117', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: 'rgba(255,255,255,0.4)' }}>Loading...</p>
    </div>
  )

  if (!data) return (
    <div style={{ minHeight: '100vh', background: '#0f1117', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: 'rgba(255,255,255,0.4)' }}>Training content not found.</p>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: '#0f1117', fontFamily: "'DM Sans','Inter',system-ui,sans-serif", padding: '40px 20px' }}>
      <div style={{ maxWidth: 680, margin: '0 auto' }}>

        {/* Alert banner */}
        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 16, padding: 28, marginBottom: 24, textAlign: 'center' }}>
          <p style={{ fontSize: 48, margin: '0 0 12px' }}>🎣</p>
          <h1 style={{ color: '#ef4444', fontWeight: 800, fontSize: 24, margin: '0 0 8px' }}>
            You clicked a simulated phishing email
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 15, margin: 0 }}>
            This was a security awareness test run by your organisation via PrepIQ.
            No real data was captured. This is a learning opportunity.
          </p>
        </div>

        {/* Campaign info */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: 24, marginBottom: 20 }}>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Simulation Details</p>
          <p style={{ color: 'white', fontWeight: 700, fontSize: 16, margin: '0 0 4px' }}>{data.template_name}</p>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13, margin: 0 }}>
            Category: {CATEGORY_LABELS[data.category] || data.category} &nbsp;·&nbsp;
            Difficulty: <span style={{ color: data.difficulty === 'easy' ? '#10b981' : data.difficulty === 'hard' ? '#ef4444' : '#fbbf24', fontWeight: 600 }}>
              {data.difficulty?.charAt(0).toUpperCase() + data.difficulty?.slice(1)}
            </span>
          </p>
        </div>

        {/* Red flags */}
        {data.red_flags && data.red_flags.length > 0 && (
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: 24, marginBottom: 20 }}>
            <h2 style={{ color: 'white', fontWeight: 700, fontSize: 17, marginBottom: 16 }}>
              🚩 Red Flags You Should Have Spotted
            </h2>
            {data.red_flags.map((flag, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: i < data.red_flags.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
                <span style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', width: 24, height: 24, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 12, flexShrink: 0 }}>{i + 1}</span>
                <p style={{ color: 'rgba(255,255,255,0.75)', fontSize: 14, lineHeight: 1.5, margin: 0 }}>{flag}</p>
              </div>
            ))}
          </div>
        )}

        {/* What to do next time */}
        <div style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 16, padding: 24, marginBottom: 20 }}>
          <h2 style={{ color: '#10b981', fontWeight: 700, fontSize: 17, marginBottom: 16 }}>✅ What To Do Next Time</h2>
          {[
            { title: 'Check the sender domain', detail: 'Hover over the sender name to reveal the full email address. Legitimate companies use their own domains — not lookalike variations.' },
            { title: 'Do not click links under pressure', detail: 'Urgency, fear, and deadlines are manipulation tactics. Pause and verify through a separate channel before clicking anything.' },
            { title: 'Report suspicious emails', detail: 'Use the Report Phishing button in your email client or forward to your IT security team. Early reporting protects your whole organisation.' },
            { title: 'When in doubt, go direct', detail: 'If an email claims to be from HMRC, Microsoft, or your bank — go directly to their official website rather than clicking any link.' },
          ].map((tip, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
              <span style={{ background: 'rgba(16,185,129,0.2)', color: '#10b981', width: 24, height: 24, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 12, flexShrink: 0 }}>{i + 1}</span>
              <div>
                <p style={{ color: 'white', fontWeight: 600, fontSize: 14, margin: '0 0 2px' }}>{tip.title}</p>
                <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 13, lineHeight: 1.5, margin: 0 }}>{tip.detail}</p>
              </div>
            </div>
          ))}
        </div>

        {/* NCSC link */}
        <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 16, padding: 20, textAlign: 'center' }}>
          <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, margin: '0 0 12px' }}>
            Want to learn more about spotting phishing attacks?
          </p>
          <a href="https://www.ncsc.gov.uk/guidance/phishing" target="_blank" rel="noopener noreferrer"
            style={{ background: '#6366f1', color: 'white', padding: '10px 24px', borderRadius: 8, textDecoration: 'none', fontWeight: 600, fontSize: 14, display: 'inline-block' }}>
            NCSC Phishing Guidance →
          </a>
          <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12, margin: '12px 0 0' }}>
            This training has been recorded. Your organisation will use this to improve security awareness.
          </p>
        </div>

      </div>
    </div>
  )
}
