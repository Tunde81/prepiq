import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'

const FEATURES = [
  {
    icon: '🇬🇧',
    title: 'UK SME Cyber Health Index',
    desc: 'Benchmark your cyber posture against UK industry peers across 10 domains. Aligned to NCSC Cyber Essentials, UK GDPR, and FCA SYSC 13.',
    badge: 'New',
    badgeColor: '#00d4ff',
  },
  {
    icon: '⚡',
    title: 'Cyber Incident Simulator',
    desc: '6 realistic UK scenarios — ransomware, BEC, insider threat, cloud misconfiguration, supply chain attack, and DDoS. Tabletop, timed challenges, and AI debrief.',
    badge: 'New',
    badgeColor: '#00d4ff',
  },
  {
    icon: '🎣',
    title: 'Phishing Simulation',
    desc: 'Send simulated phishing campaigns using 8 UK-relevant templates. Track click rates, report rates, and serve teachable moment training to staff who click.',
    badge: null,
    badgeColor: null,
  },
  {
    icon: '📋',
    title: 'Learning Modules',
    desc: 'Structured cybersecurity courses with quizzes, certificates, and badges. Covers GDPR, Cyber Essentials, FCA compliance, and threat awareness.',
    badge: null,
    badgeColor: null,
  },
  {
    icon: '🤖',
    title: 'CyberCoach AI',
    desc: 'AI-powered cybersecurity mentor available 24/7. Ask anything about threats, compliance, or best practice. Powered by Claude.',
    badge: null,
    badgeColor: null,
  },
  {
    icon: '📊',
    title: 'Board-Ready Reports',
    desc: 'Generate professional PDF reports for board-level briefings, compliance evidence, and regulatory submissions. Exportable in one click.',
    badge: null,
    badgeColor: null,
  },
]

const STATS = [
  { value: '10', label: 'Cyber Domains Assessed' },
  { value: '6', label: 'Incident Scenarios' },
  { value: '8', label: 'Phishing Templates' },
  { value: '35', label: 'Assessment Questions' },
]

const FRAMEWORKS = [
  { name: 'NCSC Cyber Essentials', color: '#00d4ff' },
  { name: 'UK GDPR', color: '#00ff88' },
  { name: 'FCA SYSC 13', color: '#ffd700' },
  { name: 'NIST CSF', color: '#818cf8' },
  { name: 'ISO 27001', color: '#f97316' },
  { name: 'DORA', color: '#ec4899' },
]

const TESTIMONIALS = [
  {
    quote: "PrepIQ gave us a clear picture of where we stood against NCSC Cyber Essentials. The Health Index report went straight to our board.",
    name: "Head of IT",
    org: "UK Professional Services Firm",
  },
  {
    quote: "The phishing simulator caught three members of staff who had never failed a test before. The teachable moment page was exactly the right response.",
    name: "Security Manager",
    org: "UK Fintech",
  },
  {
    quote: "Running the ransomware scenario before our annual DR test was invaluable. The AI debrief identified gaps we had not considered.",
    name: "CISO",
    org: "UK Healthcare Organisation",
  },
]

function AnimatedCounter({ target, suffix = '' }) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    const num = parseInt(target)
    const step = Math.ceil(num / 40)
    const timer = setInterval(() => {
      setCount(c => {
        if (c + step >= num) { clearInterval(timer); return num }
        return c + step
      })
    }, 30)
    return () => clearInterval(timer)
  }, [target])
  return <span>{count}{suffix}</span>
}

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [impact, setImpact] = useState(null)

  useEffect(() => {
    fetch('/api/impact/stats')
      .then(r => r.json())
      .then(setImpact)
      .catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-forge-bg text-forge-text" style={{
      backgroundImage: 'radial-gradient(ellipse at 20% 10%, rgba(0,212,255,0.06) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(0,255,136,0.04) 0%, transparent 50%)'
    }}>

      {/* Nav */}
      <nav style={{ borderBottom: '1px solid #1a2540', background: 'rgba(8,12,20,0.95)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 50 }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 24px', height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: '#00d4ff', fontFamily: 'monospace', fontWeight: 800, fontSize: 20, letterSpacing: 4 }}>PREPIQ</span>
            <span style={{ background: 'rgba(0,212,255,0.1)', color: '#00d4ff', fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 20, border: '1px solid rgba(0,212,255,0.3)', fontFamily: 'monospace' }}>v1.0</span>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <Link to="/login" style={{ color: 'rgba(226,232,240,0.7)', textDecoration: 'none', fontSize: 14, padding: '8px 16px', borderRadius: 8, transition: 'color 0.2s' }}
              onMouseEnter={e => e.target.style.color = '#00d4ff'}
              onMouseLeave={e => e.target.style.color = 'rgba(226,232,240,0.7)'}>
              Sign In
            </Link>
            <Link to="/register" style={{ background: '#00d4ff', color: '#080c14', fontWeight: 700, fontSize: 14, padding: '8px 20px', borderRadius: 8, textDecoration: 'none', fontFamily: 'monospace', transition: 'opacity 0.2s' }}
              onMouseEnter={e => e.target.style.opacity = '0.85'}
              onMouseLeave={e => e.target.style.opacity = '1'}>
              Get Started Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '96px 24px 80px', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 20, padding: '6px 16px', marginBottom: 32 }}>
          <span style={{ color: '#00d4ff', fontSize: 12, fontFamily: 'monospace', fontWeight: 600 }}>🇬🇧 Built for UK Organisations</span>
        </div>
        <h1 style={{ fontSize: 'clamp(36px, 6vw, 64px)', fontWeight: 800, lineHeight: 1.1, marginBottom: 24, color: '#e2e8f0' }}>
          The UK's Cyber Preparedness<br />
          <span style={{ color: '#00d4ff' }}>Learning Platform</span>
        </h1>
        <p style={{ fontSize: 18, color: '#94a3b8', lineHeight: 1.7, maxWidth: 620, margin: '0 auto 40px', fontWeight: 400, fontFamily: 'Source Sans 3, sans-serif' }}>
          PrepIQ helps UK SMEs and financial services organisations assess, train, simulate, and report on cyber security — aligned to NCSC, UK GDPR, FCA, and DORA.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/register" style={{
            background: '#00d4ff', color: '#080c14', fontWeight: 700, fontSize: 16,
            padding: '14px 36px', borderRadius: 10, textDecoration: 'none',
            fontFamily: 'monospace', boxShadow: '0 0 24px rgba(0,212,255,0.3)',
            transition: 'all 0.2s', display: 'inline-block'
          }}
            onMouseEnter={e => { e.target.style.boxShadow = '0 0 40px rgba(0,212,255,0.5)'; e.target.style.transform = 'translateY(-1px)' }}
            onMouseLeave={e => { e.target.style.boxShadow = '0 0 24px rgba(0,212,255,0.3)'; e.target.style.transform = 'translateY(0)' }}>
            Start Free Assessment →
          </Link>
          <Link to="/login" style={{
            background: 'transparent', color: '#e2e8f0', fontWeight: 600, fontSize: 16,
            padding: '14px 36px', borderRadius: 10, textDecoration: 'none',
            border: '1px solid #1a2540', transition: 'border-color 0.2s', display: 'inline-block'
          }}
            onMouseEnter={e => e.target.style.borderColor = '#00d4ff'}
            onMouseLeave={e => e.target.style.borderColor = '#1a2540'}>
            Sign In
          </Link>
        </div>

        {/* Framework badges */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginTop: 48 }}>
          {FRAMEWORKS.map(f => (
            <span key={f.name} style={{
              background: f.color + '12', color: f.color,
              border: `1px solid ${f.color}30`, borderRadius: 20,
              padding: '4px 14px', fontSize: 12, fontWeight: 600, fontFamily: 'Source Sans 3, sans-serif'
            }}>{f.name}</span>
          ))}
        </div>
      </section>

      {/* Stats */}
      <section style={{ borderTop: '1px solid #1a2540', borderBottom: '1px solid #1a2540', background: 'rgba(13,19,33,0.5)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 32 }}>
          {STATS.map(s => (
            <div key={s.label} style={{ textAlign: 'center' }}>
              <p style={{ color: '#00d4ff', fontSize: 44, fontWeight: 800, fontFamily: 'monospace', margin: '0 0 6px' }}>
                <AnimatedCounter target={s.value} />+
              </p>
              <p style={{ color: '#94a3b8', fontSize: 12, margin: 0, textTransform: 'uppercase', letterSpacing: 1.5, fontFamily: 'Source Sans 3, sans-serif', fontWeight: 500 }}>{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '96px 24px' }}>
        <div style={{ textAlign: 'center', marginBottom: 64 }}>
          <p style={{ color: '#00d4ff', fontFamily: 'monospace', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>Platform Features</p>
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 40px)', fontWeight: 800, color: '#e2e8f0', margin: '0 0 16px' }}>Everything your organisation needs</h2>
          <p style={{ color: '#94a3b8', fontSize: 16, maxWidth: 520, margin: '0 auto', fontFamily: 'Source Sans 3, sans-serif' }}>One platform for assessment, training, simulation, and reporting — built specifically for the UK regulatory environment.</p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
          {FEATURES.map(f => (
            <div key={f.title} style={{
              background: '#0d1321', border: '1px solid #1a2540', borderRadius: 16,
              padding: 28, transition: 'border-color 0.2s, transform 0.2s', cursor: 'default'
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = '#00d4ff40'; e.currentTarget.style.transform = 'translateY(-2px)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = '#1a2540'; e.currentTarget.style.transform = 'translateY(0)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                <span style={{ fontSize: 32 }}>{f.icon}</span>
                {f.badge && (
                  <span style={{ background: f.badgeColor + '18', color: f.badgeColor, border: `1px solid ${f.badgeColor}40`, borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700, fontFamily: 'monospace' }}>{f.badge}</span>
                )}
              </div>
              <h3 style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 16, marginBottom: 8 }}>{f.title}</h3>
              <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.65, margin: 0, fontFamily: 'Source Sans 3, sans-serif' }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Health Index highlight */}
      <section style={{ background: 'rgba(13,19,33,0.7)', borderTop: '1px solid #1a2540', borderBottom: '1px solid #1a2540' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '80px 24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64, alignItems: 'center' }}>
          <div>
            <p style={{ color: '#00d4ff', fontFamily: 'monospace', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>🇬🇧 UK SME Cyber Health Index</p>
            <h2 style={{ fontSize: 'clamp(24px, 3vw, 36px)', fontWeight: 800, color: '#e2e8f0', marginBottom: 20, lineHeight: 1.2 }}>Know where you stand. Fix what matters.</h2>
            <p style={{ color: '#94a3b8', fontSize: 15, fontFamily: 'Source Sans 3, sans-serif', lineHeight: 1.7, marginBottom: 24 }}>35 questions across 10 cybersecurity domains. Get a scored benchmark report, risk tier, and prioritised action plan — benchmarked against UK SMEs in your sector.</p>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 32px' }}>
              {['Scored 0-100 with risk tier (Critical to Secure)', 'Benchmarked against 8 UK industry sectors', 'Top 5 priority recommendations with effort ratings', 'Exportable PDF report for board and compliance evidence'].map(item => (
                <li key={item} style={{ display: 'flex', gap: 10, marginBottom: 10, color: '#94a3b8', fontSize: 14, fontFamily: 'Source Sans 3, sans-serif' }}>
                  <span style={{ color: '#00ff88', flexShrink: 0 }}>✓</span> {item}
                </li>
              ))}
            </ul>
            <Link to="/register" style={{ background: '#00d4ff', color: '#080c14', fontWeight: 700, fontSize: 14, padding: '12px 28px', borderRadius: 8, textDecoration: 'none', fontFamily: 'monospace', display: 'inline-block' }}>
              Run Your Free Assessment →
            </Link>
          </div>
          <div style={{ background: '#080c14', border: '1px solid #1a2540', borderRadius: 16, padding: 32 }}>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <p style={{ color: '#00d4ff', fontFamily: 'monospace', fontSize: 11, textTransform: 'uppercase', letterSpacing: 2, margin: '0 0 8px' }}>Sample Score Card</p>
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <svg width="140" height="140" viewBox="0 0 140 140">
                  <circle cx="70" cy="70" r="54" fill="none" stroke="#1a2540" strokeWidth="10" />
                  <circle cx="70" cy="70" r="54" fill="none" stroke="#00d4ff" strokeWidth="10" strokeLinecap="round"
                    strokeDasharray="339" strokeDashoffset="102" transform="rotate(-90 70 70)" />
                  <text x="70" y="65" textAnchor="middle" fill="#e2e8f0" fontSize="28" fontWeight="800" fontFamily="monospace">70</text>
                  <text x="70" y="82" textAnchor="middle" fill="#00d4ff" fontSize="11">/ 100</text>
                </svg>
              </div>
              <p style={{ color: '#00d4ff', fontWeight: 700, margin: '8px 0 4px', fontFamily: 'monospace' }}>LOW RISK</p>
              <p style={{ color: '#94a3b8', fontSize: 13, margin: 0, fontFamily: 'Source Sans 3, sans-serif' }}>Better than 68% of UK Technology SMEs</p>
            </div>
            {[
              { domain: 'Access Control', score: 82, color: '#00ff88' },
              { domain: 'Network Security', score: 65, color: '#00d4ff' },
              { domain: 'Staff Awareness', score: 70, color: '#00d4ff' },
              { domain: 'Incident Response', score: 48, color: '#ffd700' },
              { domain: 'Patching', score: 35, color: '#ff4444' },
            ].map(d => (
              <div key={d.domain} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                  <span style={{ color: '#94a3b8', fontSize: 13, fontFamily: 'Source Sans 3, sans-serif' }}>{d.domain}</span>
                  <span style={{ color: d.color, fontSize: 12, fontWeight: 700, fontFamily: 'monospace' }}>{d.score}</span>
                </div>
                <div style={{ background: '#1a2540', borderRadius: 4, height: 5 }}>
                  <div style={{ background: d.color, height: '100%', borderRadius: 4, width: `${d.score}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Live Impact Stats */}
      {impact && (
      <section style={{ background: 'rgba(0,255,136,0.03)', borderTop: '1px solid rgba(0,255,136,0.1)', borderBottom: '1px solid rgba(0,255,136,0.1)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '72px 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <p style={{ color: '#00ff88', fontFamily: 'monospace', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 2, marginBottom: 12 }}>Live Platform Impact</p>
            <h2 style={{ fontSize: 'clamp(24px, 3vw, 36px)', fontWeight: 800, color: '#e2e8f0', margin: '0 0 12px' }}>Real usage. Real impact.</h2>
            <p style={{ color: '#94a3b8', fontSize: 15, margin: 0, fontFamily: 'Source Sans 3, sans-serif' }}>UK organisations actively using PrepIQ to improve their cyber resilience</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
            {[
              { value: impact.users_trained, label: 'Users Trained', icon: '👥', color: '#00d4ff' },
              { value: impact.organisations, label: 'Organisations', icon: '🏢', color: '#00ff88' },
              { value: impact.module_completions, label: 'Module Completions', icon: '✅', color: '#6366f1' },
              { value: impact.risk_assessments, label: 'Risk Assessments', icon: '🛡️', color: '#ffd700' },
              { value: impact.modules_available, label: 'Learning Modules', icon: '📚', color: '#f97316' },
              { value: impact.frameworks_covered, label: 'Frameworks Covered', icon: '⚖️', color: '#ec4899' },
            ].map(k => (
              <div key={k.label} style={{ background: '#0d1321', border: '1px solid #1a2540', borderRadius: 14, padding: '24px 20px', textAlign: 'center' }}>
                <p style={{ fontSize: 28, margin: '0 0 8px' }}>{k.icon}</p>
                <p style={{ color: k.color, fontSize: 36, fontWeight: 800, margin: '0 0 6px', fontFamily: 'monospace' }}>{k.value.toLocaleString()}</p>
                <p style={{ color: '#94a3b8', fontSize: 13, margin: 0, fontFamily: 'Source Sans 3, sans-serif' }}>{k.label}</p>
              </div>
            ))}
          </div>
          <p style={{ textAlign: 'center', color: '#4a5568', fontSize: 12, marginTop: 24, fontFamily: 'Source Sans 3, sans-serif' }}>
            Data updates in real time · Last updated {new Date(impact.last_updated).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
          </p>
        </div>
      </section>
      )}

      {/* Testimonials */}
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '96px 24px' }}>
        <div style={{ textAlign: 'center', marginBottom: 56 }}>
          <h2 style={{ fontSize: 'clamp(24px, 3vw, 36px)', fontWeight: 800, color: '#e2e8f0', margin: '0 0 12px' }}>Trusted by UK security teams</h2>
          <p style={{ color: '#94a3b8', fontSize: 15, fontFamily: 'Source Sans 3, sans-serif' }}>From SMEs to regulated financial services firms</p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
          {TESTIMONIALS.map((t, i) => (
            <div key={i} style={{ background: '#0d1321', border: '1px solid #1a2540', borderRadius: 16, padding: 28 }}>
              <p style={{ color: '#00d4ff', fontSize: 24, margin: '0 0 12px' }}>"</p>
              <p style={{ color: '#cbd5e1', fontSize: 14, lineHeight: 1.7, margin: '0 0 20px', fontStyle: 'italic', fontFamily: 'Source Sans 3, sans-serif' }}>{t.quote}</p>
              <div>
                <p style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 13, margin: '0 0 2px' }}>{t.name}</p>
                <p style={{ color: '#94a3b8', fontSize: 12, margin: 0, fontFamily: 'Source Sans 3, sans-serif' }}>{t.org}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{ background: 'rgba(0,212,255,0.04)', borderTop: '1px solid rgba(0,212,255,0.15)', borderBottom: '1px solid rgba(0,212,255,0.15)' }}>
        <div style={{ maxWidth: 700, margin: '0 auto', padding: '96px 24px', textAlign: 'center' }}>
          <h2 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 800, color: '#e2e8f0', marginBottom: 16 }}>
            Start your free cyber health assessment
          </h2>
          <p style={{ color: '#94a3b8', fontSize: 16, lineHeight: 1.7, marginBottom: 40, maxWidth: 520, margin: '0 auto 40px' }}>
            Join UK organisations using PrepIQ to assess their cyber posture, train their teams, and demonstrate compliance with NCSC, FCA, and UK GDPR requirements.
          </p>
          <Link to="/register" style={{
            background: '#00d4ff', color: '#080c14', fontWeight: 700, fontSize: 16,
            padding: '16px 48px', borderRadius: 10, textDecoration: 'none',
            fontFamily: 'monospace', boxShadow: '0 0 32px rgba(0,212,255,0.4)',
            display: 'inline-block', transition: 'all 0.2s'
          }}
            onMouseEnter={e => { e.target.style.boxShadow = '0 0 48px rgba(0,212,255,0.6)'; e.target.style.transform = 'translateY(-2px)' }}
            onMouseLeave={e => { e.target.style.boxShadow = '0 0 32px rgba(0,212,255,0.4)'; e.target.style.transform = 'translateY(0)' }}>
            Create Free Account →
          </Link>
          <p style={{ color: '#94a3b8', fontSize: 14, marginTop: 16 }}>No credit card required · Free assessment included</p>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid #1a2540', padding: '40px 24px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <span style={{ color: '#00d4ff', fontFamily: 'monospace', fontWeight: 800, letterSpacing: 3 }}>PREPIQ</span>
            <p style={{ color: '#94a3b8', fontSize: 14, margin: '4px 0 0', fontFamily: 'Source Sans 3, sans-serif' }}>UK National Cyber Preparedness Learning Platform</p>
            <p style={{ color: '#94a3b8', fontSize: 14, margin: '4px 0 0', fontFamily: 'Source Sans 3, sans-serif' }}>A product of <a href="https://www.fa3tech.io" style={{ color: '#00d4ff', textDecoration: 'none' }}>Fa3Tech Limited</a></p>
          </div>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            {[
              { label: 'Sign In', to: '/login' },
              { label: 'Register', to: '/register' },
              { label: 'Health Index', to: '/health-index' },
              { label: 'Simulator', to: '/simulator' },
            ].map(l => (
              <Link key={l.label} to={l.to} style={{ color: '#94a3b8', textDecoration: 'none', fontSize: 15, transition: 'color 0.2s', fontFamily: 'Source Sans 3, sans-serif' }}
                onMouseEnter={e => e.target.style.color = '#00d4ff'}
                onMouseLeave={e => e.target.style.color = '#4a5568'}>
                {l.label}
              </Link>
            ))}
          </div>
          <p style={{ color: '#94a3b8', fontSize: 14, margin: 0, fontFamily: 'Source Sans 3, sans-serif' }}>© 2025 Fa3Tech Limited. All rights reserved.</p>
        </div>
      </footer>

    </div>
  )
}
