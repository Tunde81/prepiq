import { useEffect, useState } from 'react'
import { Shield, Users, BookOpen, Award, Building2, Globe, TrendingUp, CheckCircle, Zap, FileCheck } from 'lucide-react'

const STAT_CARDS = [
  { key: 'users_trained', label: 'Users Trained', icon: Users, colour: 'text-blue-400', bg: 'bg-blue-900/20 border-blue-800/30' },
  { key: 'modules_available', label: 'Learning Modules', icon: BookOpen, colour: 'text-forge-accent', bg: 'bg-forge-accent/10 border-forge-accent/20' },
  { key: 'lessons_available', label: 'Lessons Available', icon: FileCheck, colour: 'text-purple-400', bg: 'bg-purple-900/20 border-purple-800/30' },
  { key: 'module_completions', label: 'Modules Completed', icon: Award, colour: 'text-green-400', bg: 'bg-green-900/20 border-green-800/30' },
  { key: 'risk_assessments', label: 'Risk Assessments', icon: Shield, colour: 'text-yellow-400', bg: 'bg-yellow-900/20 border-yellow-800/30' },
  { key: 'organisations', label: 'Organisations', icon: Building2, colour: 'text-orange-400', bg: 'bg-orange-900/20 border-orange-800/30' },
  { key: 'hours_of_content', label: 'Hours of Content', icon: TrendingUp, colour: 'text-red-400', bg: 'bg-red-900/20 border-red-800/30' },
  { key: 'frameworks_covered', label: 'Regulatory Frameworks', icon: Globe, colour: 'text-indigo-400', bg: 'bg-indigo-900/20 border-indigo-800/30' },
]

const FRAMEWORKS = [
  { name: 'Cyber Essentials', icon: '🇬🇧', desc: 'UK government-backed scheme' },
  { name: 'UK GDPR', icon: '🔒', desc: 'Data protection regulation' },
  { name: 'DORA', icon: '💳', desc: 'Digital Operational Resilience Act' },
  { name: 'FCA Cyber Resilience', icon: '🏦', desc: 'Financial Conduct Authority' },
  { name: 'NIS2 Directive', icon: '🇪🇺', desc: 'Network & Information Security' },
]

const FEATURES = [
  { icon: '🤖', title: 'AI-Powered Learning', desc: 'CyberCoach AI assistant, AI-generated modules and personalised learning paths' },
  { icon: '🎯', title: 'Role-Based Paths', desc: 'Tailored curricula for CFOs, IT Managers, SME owners, HR and more' },
  { icon: '📊', title: 'Compliance Tracking', desc: 'Real-time mapping of progress to FCA, DORA, GDPR, NIS2 and Cyber Essentials' },
  { icon: '🏢', title: 'Organisation Health', desc: 'Team-wide cyber health scoring and weakest area identification' },
  { icon: '📋', title: 'Board Reporting', desc: 'AI-generated executive PDF reports suitable for board packs' },
  { icon: '⚡', title: 'Threat Intelligence', desc: 'Live NCSC and CVE threat feeds integrated into the learning experience' },
]

export default function ImpactDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/impact/stats')
      .then(r => r.json())
      .then(d => setStats(d))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{background:'#0a0e1a', minHeight:'100vh', color:'#e2e8f0', fontFamily:'system-ui,sans-serif'}}>

      {/* Hero */}
      <div style={{borderBottom:'1px solid #1e3a5f', padding:'0 40px'}}>
        <div style={{maxWidth:'1100px', margin:'0 auto', padding:'40px 0 32px'}}>
          <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:'20px'}}>
            <div>
              <div style={{color:'#00d4ff', fontFamily:'monospace', fontWeight:'bold', fontSize:'28px', letterSpacing:'4px', marginBottom:'4px'}}>PREPIQ</div>
              <div style={{color:'#6b7280', fontSize:'13px'}}>UK National Cyber Preparedness Learning Platform</div>
            </div>
            <a href="/dashboard" style={{background:'#00d4ff', color:'#0a0e1a', padding:'10px 24px', borderRadius:'8px', textDecoration:'none', fontWeight:'bold', fontSize:'14px', fontFamily:'monospace'}}>
              Launch Platform →
            </a>
          </div>
        </div>
      </div>

      <div style={{maxWidth:'1100px', margin:'0 auto', padding:'60px 40px'}}>

        {/* Title */}
        <div style={{textAlign:'center', marginBottom:'60px'}}>
          <h1 style={{fontSize:'42px', fontWeight:'bold', color:'#ffffff', marginBottom:'16px', lineHeight:'1.2'}}>
            Preparing the UK for<br /><span style={{color:'#00d4ff'}}>Cyber Threats</span>
          </h1>
          <p style={{color:'#9ca3af', fontSize:'18px', maxWidth:'600px', margin:'0 auto', lineHeight:'1.6'}}>
            PrepIQ is the UK's national cyber preparedness learning platform, delivering AI-powered cybersecurity education mapped to UK regulatory frameworks.
          </p>
        </div>

        {/* Stats Grid */}
        <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(220px, 1fr))', gap:'16px', marginBottom:'60px'}}>
          {STAT_CARDS.map(card => (
            <div key={card.key} style={{background:'#0d1626', border:'1px solid #1e3a5f', borderRadius:'12px', padding:'24px', textAlign:'center'}}>
              <div style={{fontSize:'36px', fontWeight:'bold', fontFamily:'monospace', color:'#00d4ff', marginBottom:'4px'}}>
                {loading ? '—' : (stats?.[card.key] ?? '—')}
                {card.key === 'hours_of_content' && !loading ? 'h' : ''}
              </div>
              <div style={{color:'#6b7280', fontSize:'13px'}}>{card.label}</div>
            </div>
          ))}
        </div>

        {/* Regulatory Frameworks */}
        <div style={{marginBottom:'60px'}}>
          <h2 style={{fontSize:'24px', fontWeight:'bold', color:'#ffffff', marginBottom:'8px', textAlign:'center'}}>Regulatory Frameworks Covered</h2>
          <p style={{color:'#6b7280', textAlign:'center', marginBottom:'32px', fontSize:'14px'}}>PrepIQ maps all learning content to UK and EU cybersecurity regulations</p>
          <div style={{display:'flex', flexWrap:'wrap', gap:'12px', justifyContent:'center'}}>
            {FRAMEWORKS.map((fw, i) => (
              <div key={i} style={{background:'#0d1626', border:'1px solid #1e3a5f', borderRadius:'12px', padding:'16px 24px', display:'flex', alignItems:'center', gap:'12px'}}>
                <span style={{fontSize:'24px'}}>{fw.icon}</span>
                <div>
                  <div style={{fontWeight:'bold', color:'#e2e8f0', fontSize:'14px'}}>{fw.name}</div>
                  <div style={{color:'#6b7280', fontSize:'12px'}}>{fw.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Platform Features */}
        <div style={{marginBottom:'60px'}}>
          <h2 style={{fontSize:'24px', fontWeight:'bold', color:'#ffffff', marginBottom:'8px', textAlign:'center'}}>Platform Capabilities</h2>
          <p style={{color:'#6b7280', textAlign:'center', marginBottom:'32px', fontSize:'14px'}}>Unique features designed for UK organisations, SMEs, councils and citizens</p>
          <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(300px, 1fr))', gap:'16px'}}>
            {FEATURES.map((f, i) => (
              <div key={i} style={{background:'#0d1626', border:'1px solid #1e3a5f', borderRadius:'12px', padding:'24px', display:'flex', gap:'16px'}}>
                <span style={{fontSize:'28px', flexShrink:0}}>{f.icon}</span>
                <div>
                  <div style={{fontWeight:'bold', color:'#e2e8f0', marginBottom:'4px'}}>{f.title}</div>
                  <div style={{color:'#6b7280', fontSize:'13px', lineHeight:'1.5'}}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div style={{background:'linear-gradient(135deg, #0d1f3c, #0a0e1a)', border:'1px solid #00d4ff30', borderRadius:'16px', padding:'48px', textAlign:'center'}}>
          <h2 style={{fontSize:'28px', fontWeight:'bold', color:'#ffffff', marginBottom:'12px'}}>Start Your Cyber Preparedness Journey</h2>
          <p style={{color:'#9ca3af', marginBottom:'32px', fontSize:'16px'}}>Free access to UK-focused cybersecurity training, compliance tracking and AI-powered learning paths.</p>
          <div style={{display:'flex', gap:'16px', justifyContent:'center', flexWrap:'wrap'}}>
            <a href="/dashboard" style={{background:'#00d4ff', color:'#0a0e1a', padding:'14px 32px', borderRadius:'8px', textDecoration:'none', fontWeight:'bold', fontSize:'15px', fontFamily:'monospace'}}>
              Get Started Free →
            </a>
            <a href="/compliance" style={{background:'transparent', color:'#00d4ff', padding:'14px 32px', borderRadius:'8px', textDecoration:'none', fontWeight:'bold', fontSize:'15px', fontFamily:'monospace', border:'1px solid #00d4ff40'}}>
              View Compliance Tracker
            </a>
          </div>
        </div>

        {/* Footer */}
        <div style={{textAlign:'center', marginTop:'48px', color:'#4b5563', fontSize:'12px', borderTop:'1px solid #1e3a5f', paddingTop:'24px'}}>
          PrepIQ · Fa3Tech Limited · prepiq.fa3tech.io · info@fa3tech.io · Built for the UK
        </div>
      </div>
    </div>
  )
}
