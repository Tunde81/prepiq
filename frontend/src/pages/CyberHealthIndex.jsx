import React, { useState, useEffect, useRef } from 'react';

// ─── Colour palette & domain config ──────────────────────────────────────────

const TIER_CONFIG = {
  secure:   { label: 'Secure',   color: '#10b981', bg: '#064e3b', icon: '🛡️' },
  low:      { label: 'Low Risk', color: '#34d399', bg: '#065f46', icon: '✅' },
  medium:   { label: 'Medium Risk', color: '#fbbf24', bg: '#78350f', icon: '⚠️' },
  high:     { label: 'High Risk',   color: '#f97316', bg: '#7c2d12', icon: '🔶' },
  critical: { label: 'Critical',    color: '#ef4444', bg: '#7f1d1d', icon: '🚨' },
};

const DOMAIN_LABELS = {
  governance:       'Governance',
  asset_management: 'Asset Management',
  access_control:   'Access Control',
  network_security: 'Network Security',
  incident_response:'Incident Response',
  supply_chain:     'Supply Chain',
  staff_awareness:  'Staff Awareness',
  data_protection:  'Data Protection',
  patching:         'Patching',
  backup_recovery:  'Backup & Recovery',
};

const DOMAIN_ICONS = {
  governance: '📋', asset_management: '🖥️', access_control: '🔑',
  network_security: '🌐', incident_response: '🚒', supply_chain: '🔗',
  staff_awareness: '👥', data_protection: '🔒', patching: '🩹',
  backup_recovery: '💾',
};

const SECTOR_OPTIONS = [
  'Financial Services', 'Professional Services', 'Retail', 'Healthcare',
  'Technology', 'Education', 'Manufacturing', 'Charity/NGO', 'Other',
];

// ─── API helpers ─────────────────────────────────────────────────────────────

const API = async (path, method = 'GET', body = null) => {
  const token = JSON.parse(localStorage.getItem('prepiq-auth') || '{}')?.state?.token;
  const res = await fetch(`/api/health-index${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
};

// ─── Subcomponents ────────────────────────────────────────────────────────────

const ScoreRing = ({ score, size = 120, tier }) => {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score || 0));
  const offset = circ - (pct / 100) * circ;
  const cfg = TIER_CONFIG[tier] || TIER_CONFIG.medium;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={cfg.color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={offset}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: 'stroke-dashoffset 1.2s ease' }} />
      <text x="50%" y="44%" textAnchor="middle" dominantBaseline="middle"
        fill="white" fontSize={size * 0.22} fontWeight="700">{Math.round(pct)}</text>
      <text x="50%" y="66%" textAnchor="middle" dominantBaseline="middle"
        fill={cfg.color} fontSize={size * 0.1} fontWeight="600">/ 100</text>
    </svg>
  );
};

const RadarChart = ({ domainScores }) => {
  const domains = Object.keys(DOMAIN_LABELS);
  const n = domains.length;
  const cx = 180, cy = 180, r = 130;
  const angles = domains.map((_, i) => (i / n) * 2 * Math.PI - Math.PI / 2);

  const getPoint = (angle, radius) => ({
    x: cx + radius * Math.cos(angle),
    y: cy + radius * Math.sin(angle),
  });

  const gridLevels = [20, 40, 60, 80, 100];
  const dataPoints = domains.map((d, i) => {
    const score = domainScores?.[d] ?? 0;
    return getPoint(angles[i], (score / 100) * r);
  });
  const dataPath = dataPoints.map((p, i) =>
    `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';

  return (
    <svg viewBox="0 0 360 360" style={{ width: '100%', maxWidth: 340 }}>
      {gridLevels.map(level => {
        const pts = angles.map(a => getPoint(a, (level / 100) * r));
        const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';
        return <path key={level} d={path} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />;
      })}
      {angles.map((angle, i) => {
        const end = getPoint(angle, r);
        return <line key={i} x1={cx} y1={cy} x2={end.x} y2={end.y}
          stroke="rgba(255,255,255,0.1)" strokeWidth="1" />;
      })}
      <path d={dataPath} fill="rgba(99,102,241,0.25)" stroke="#6366f1" strokeWidth="2" />
      {dataPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="4" fill="#6366f1" />
      ))}
      {domains.map((d, i) => {
        const lp = getPoint(angles[i], r + 18);
        return (
          <text key={d} x={lp.x} y={lp.y} textAnchor="middle" dominantBaseline="middle"
            fill="rgba(255,255,255,0.7)" fontSize="9" fontWeight="500">
            {DOMAIN_LABELS[d]?.split(' ')[0]}
          </text>
        );
      })}
    </svg>
  );
};

const DomainBar = ({ domain, score, benchmarkP50 }) => {
  const cfg = score >= 65 ? { color: '#10b981' } : score >= 40 ? { color: '#fbbf24' } : { color: '#ef4444' };
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: 13 }}>
          {DOMAIN_ICONS[domain]} {DOMAIN_LABELS[domain]}
        </span>
        <span style={{ color: cfg.color, fontWeight: 700, fontSize: 13 }}>
          {score != null ? `${Math.round(score)}` : '–'}
        </span>
      </div>
      <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 8, position: 'relative' }}>
        <div style={{
          background: cfg.color, height: '100%', borderRadius: 4,
          width: `${score || 0}%`, transition: 'width 1s ease',
        }} />
        {benchmarkP50 && (
          <div style={{
            position: 'absolute', top: -3, left: `${benchmarkP50}%`,
            width: 2, height: 14, background: 'rgba(255,255,255,0.35)', borderRadius: 1,
          }} title={`Sector median: ${benchmarkP50}`} />
        )}
      </div>
    </div>
  );
};

const LikertInput = ({ value, onChange }) => {
  const labels = ['Never', 'Rarely', 'Sometimes', 'Usually', 'Always'];
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
      {[1, 2, 3, 4, 5].map(v => (
        <button key={v} onClick={() => onChange(String(v))}
          style={{
            padding: '8px 14px', borderRadius: 8, border: '1px solid',
            borderColor: value === String(v) ? '#6366f1' : 'rgba(255,255,255,0.12)',
            background: value === String(v) ? '#6366f1' : 'transparent',
            color: 'white', cursor: 'pointer', fontSize: 13, transition: 'all 0.15s',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
          }}>
          <span style={{ fontWeight: 700 }}>{v}</span>
          <span style={{ fontSize: 10, opacity: 0.7 }}>{labels[v - 1]}</span>
        </button>
      ))}
    </div>
  );
};

const BooleanInput = ({ value, onChange }) => (
  <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
    {['yes', 'partial', 'no'].map(v => {
      const colors = { yes: '#10b981', partial: '#fbbf24', no: '#ef4444' };
      const labels = { yes: '✓ Yes', partial: '⊘ Partial', no: '✗ No' };
      return (
        <button key={v} onClick={() => onChange(v)}
          style={{
            padding: '8px 20px', borderRadius: 8, border: '1px solid',
            borderColor: value === v ? colors[v] : 'rgba(255,255,255,0.12)',
            background: value === v ? colors[v] + '22' : 'transparent',
            color: value === v ? colors[v] : 'rgba(255,255,255,0.6)',
            cursor: 'pointer', fontSize: 13, fontWeight: 600, transition: 'all 0.15s',
          }}>
          {labels[v]}
        </button>
      );
    })}
  </div>
);

// ─── Phase 1: Intake form ─────────────────────────────────────────────────────

const IntakeForm = ({ onStart, loading }) => {
  const [form, setForm] = useState({
    employee_count: '', sector: '', has_it_team: null, has_cyber_insurance: null,
  });
  const valid = form.employee_count && form.sector &&
    form.has_it_team !== null && form.has_cyber_insurance !== null;

  return (
    <div style={{ maxWidth: 560, margin: '0 auto' }}>
      <div style={{
        background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)',
        borderRadius: 16, padding: 32,
      }}>
        <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
          Before we start
        </h2>
        <p style={{ color: 'rgba(255,255,255,0.55)', marginBottom: 28, fontSize: 14 }}>
          Answer four quick questions so we can benchmark your results against similar UK organisations.
        </p>

        <label style={labelStyle}>Organisation size</label>
        <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
          {['<10', '10-49', '50-249'].map(v => (
            <button key={v} onClick={() => setForm(f => ({ ...f, employee_count: v }))}
              style={chipStyle(form.employee_count === v)}>
              {v} employees
            </button>
          ))}
        </div>

        <label style={labelStyle}>Primary sector</label>
        <select value={form.sector}
          onChange={e => setForm(f => ({ ...f, sector: e.target.value }))}
          style={selectStyle}>
          <option value="" style={{background:"#1a2035",color:"white"}}>Select sector…</option>
          {SECTOR_OPTIONS.map(s => <option key={s} value={s} style={{background:"#1a2035",color:"white"}}>{s}</option>)}
        </select>

        <label style={labelStyle}>Do you have a dedicated IT team or person?</label>
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          {[['yes', true], ['no', false]].map(([label, val]) => (
            <button key={label} onClick={() => setForm(f => ({ ...f, has_it_team: val }))}
              style={chipStyle(form.has_it_team === val)}>{label === 'yes' ? 'Yes' : 'No'}</button>
          ))}
        </div>

        <label style={labelStyle}>Do you hold cyber insurance?</label>
        <div style={{ display: 'flex', gap: 8, marginBottom: 32 }}>
          {[['yes', true], ['no', false]].map(([label, val]) => (
            <button key={label} onClick={() => setForm(f => ({ ...f, has_cyber_insurance: val }))}
              style={chipStyle(form.has_cyber_insurance === val)}>{label === 'yes' ? 'Yes' : 'No'}</button>
          ))}
        </div>

        <button onClick={() => onStart(form)} disabled={!valid || loading}
          style={{
            width: '100%', padding: '14px 0', borderRadius: 10,
            background: valid ? '#6366f1' : 'rgba(255,255,255,0.06)',
            color: 'white', border: 'none', cursor: valid ? 'pointer' : 'not-allowed',
            fontWeight: 700, fontSize: 15, transition: 'all 0.2s',
          }}>
          {loading ? 'Starting…' : 'Start Assessment →'}
        </button>
      </div>
    </div>
  );
};

// ─── Phase 2: Question wizard ─────────────────────────────────────────────────

const QuestionWizard = ({ questions, assessmentId, onComplete }) => {
  const domains = Object.keys(questions);
  const [domainIdx, setDomainIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [saving, setSaving] = useState(false);
  const [completing, setCompleting] = useState(false);

  const currentDomain = domains[domainIdx];
  const domainQuestions = questions[currentDomain] || [];
  const totalDomains = domains.length;

  const domainAnswered = domainQuestions.filter(q => answers[q.id]).length;
  const domainComplete = domainAnswered === domainQuestions.length;

  const saveAndNext = async () => {
    setSaving(true);
    const domainAnswers = domainQuestions
      .filter(q => answers[q.id])
      .map(q => ({ question_id: q.id, answer_value: answers[q.id] }));
    try {
      await API(`/assessment/${assessmentId}/answers`, 'POST', { answers: domainAnswers });
    } catch (e) { console.error(e); }
    setSaving(false);
    if (domainIdx < totalDomains - 1) {
      setDomainIdx(d => d + 1);
    } else {
      setCompleting(true);
      try {
        const result = await API(`/assessment/${assessmentId}/complete`, 'POST');
        onComplete(result);
      } catch (e) {
        alert('Error completing assessment: ' + e.message);
        setCompleting(false);
      }
    }
  };

  const progress = ((domainIdx) / totalDomains) * 100;

  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>
      {/* Progress */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13 }}>
            Domain {domainIdx + 1} of {totalDomains}
          </span>
          <span style={{ color: '#6366f1', fontSize: 13, fontWeight: 600 }}>
            {DOMAIN_ICONS[currentDomain]} {DOMAIN_LABELS[currentDomain]}
          </span>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 6 }}>
          <div style={{
            background: '#6366f1', height: '100%', borderRadius: 4,
            width: `${progress}%`, transition: 'width 0.4s ease',
          }} />
        </div>
        <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
          {domains.map((d, i) => (
            <div key={d} title={DOMAIN_LABELS[d]} style={{
              flex: 1, height: 4, borderRadius: 2,
              background: i < domainIdx ? '#6366f1' : i === domainIdx ? '#818cf8' : 'rgba(255,255,255,0.08)',
              transition: 'background 0.3s',
            }} />
          ))}
        </div>
      </div>

      {/* Questions */}
      <div style={{
        background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 16, padding: 32,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
          <span style={{ fontSize: 24 }}>{DOMAIN_ICONS[currentDomain]}</span>
          <h3 style={{ color: 'white', fontWeight: 700, fontSize: 18, margin: 0 }}>
            {DOMAIN_LABELS[currentDomain]}
          </h3>
          <span style={{
            marginLeft: 'auto', background: 'rgba(99,102,241,0.15)',
            color: '#818cf8', padding: '2px 10px', borderRadius: 20, fontSize: 12,
          }}>
            {domainAnswered}/{domainQuestions.length} answered
          </span>
        </div>

        {domainQuestions.map((q, idx) => (
          <div key={q.id} style={{
            marginBottom: 28, paddingBottom: 28,
            borderBottom: idx < domainQuestions.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none',
          }}>
            <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: 14, lineHeight: 1.6, marginBottom: 4 }}>
              <strong style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12 }}>Q{idx + 1}. </strong>
              {q.question_text}
            </p>
            {q.help_text && (
              <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 12, marginBottom: 4 }}>
                {q.help_text}
              </p>
            )}
            {(q.ncsc_reference || q.fca_reference) && (
              <div style={{ display: 'flex', gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
                {q.ncsc_reference && (
                  <span style={refBadge('#0ea5e9')}>📘 {q.ncsc_reference}</span>
                )}
                {q.fca_reference && (
                  <span style={refBadge('#8b5cf6')}>⚖️ {q.fca_reference}</span>
                )}
              </div>
            )}
            {q.answer_type === 'likert5' ? (
              <LikertInput value={answers[q.id] || ''} onChange={v => setAnswers(a => ({ ...a, [q.id]: v }))} />
            ) : (
              <BooleanInput value={answers[q.id] || ''} onChange={v => setAnswers(a => ({ ...a, [q.id]: v }))} />
            )}
          </div>
        ))}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
          <button onClick={() => setDomainIdx(d => Math.max(0, d - 1))}
            disabled={domainIdx === 0}
            style={{ ...navBtn, opacity: domainIdx === 0 ? 0.3 : 1 }}>
            ← Previous
          </button>
          <button onClick={saveAndNext} disabled={!domainComplete || saving || completing}
            style={{
              ...navBtn,
              background: domainComplete ? '#6366f1' : 'rgba(255,255,255,0.06)',
              opacity: !domainComplete ? 0.5 : 1,
            }}>
            {saving || completing
              ? (completing ? 'Calculating score…' : 'Saving…')
              : domainIdx === totalDomains - 1
              ? 'Complete Assessment 🎯'
              : 'Next Domain →'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Phase 3: Score card ──────────────────────────────────────────────────────

const ScoreCard = ({ result, onViewDashboard, onExportPdf }) => {
  const cfg = TIER_CONFIG[result.risk_tier] || TIER_CONFIG.medium;

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      {/* Hero score */}
      <div style={{
        background: `linear-gradient(135deg, ${cfg.bg} 0%, rgba(17,24,39,0.9) 100%)`,
        border: `1px solid ${cfg.color}40`, borderRadius: 20, padding: 40,
        textAlign: 'center', marginBottom: 24,
      }}>
        <p style={{ color: cfg.color, fontWeight: 600, fontSize: 13, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 16 }}>
          {cfg.icon} UK SME Cyber Health Index
        </p>
        <ScoreRing score={result.overall_score} tier={result.risk_tier} size={160} />
        <h1 style={{ color: 'white', fontSize: 28, fontWeight: 800, margin: '16px 0 4px' }}>
          {cfg.label}
        </h1>
        {result.benchmark_percentile && (
          <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 14 }}>
            Better than <strong style={{ color: cfg.color }}>{result.benchmark_percentile}%</strong> of UK SMEs in your sector
          </p>
        )}
      </div>

      {/* Domain breakdown */}
      <div style={{
        background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 16, padding: 28, marginBottom: 24,
      }}>
        <h3 style={{ color: 'white', fontWeight: 700, marginBottom: 20 }}>Domain Breakdown</h3>
        {Object.entries(result.domain_scores || {}).map(([domain, score]) => (
          <DomainBar key={domain} domain={domain} score={score} />
        ))}
      </div>

      {/* Top recommendations */}
      <div style={{
        background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 16, padding: 28, marginBottom: 28,
      }}>
        <h3 style={{ color: 'white', fontWeight: 700, marginBottom: 20 }}>
          🎯 Top Priority Actions
        </h3>
        {(result.recommendations || []).map((rec, i) => {
          const effortColor = { low: '#10b981', medium: '#fbbf24', high: '#f97316' }[rec.effort] || '#6366f1';
          const impactColor = { high: '#10b981', critical: '#6366f1', medium: '#fbbf24' }[rec.impact] || '#6366f1';
          return (
            <div key={i} style={{
              background: 'rgba(255,255,255,0.03)', borderRadius: 12,
              padding: '16px 20px', marginBottom: 12,
              borderLeft: `3px solid ${TIER_CONFIG[
                rec.score >= 65 ? 'low' : rec.score >= 40 ? 'medium' : 'critical'
              ]?.color || '#6366f1'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                <div>
                  <p style={{ color: 'white', fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                    <span style={{ color: 'rgba(255,255,255,0.35)', marginRight: 6 }}>#{i + 1}</span>
                    {rec.title}
                  </p>
                  <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13, lineHeight: 1.5 }}>{rec.detail}</p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flexShrink: 0 }}>
                  <span style={{ ...pillStyle, background: effortColor + '22', color: effortColor }}>
                    {rec.effort} effort
                  </span>
                  <span style={{ ...pillStyle, background: impactColor + '22', color: impactColor }}>
                    {rec.impact} impact
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', gap: 12 }}>
        <button onClick={onViewDashboard}
          style={{ flex: 1, padding: '14px 0', borderRadius: 10,
            background: '#6366f1', color: 'white', border: 'none',
            fontWeight: 700, fontSize: 15, cursor: 'pointer' }}>
          View Full Dashboard
        </button>
        <button onClick={onExportPdf}
          style={{ padding: '14px 20px', borderRadius: 10,
            background: 'rgba(255,255,255,0.06)', color: 'white',
            border: '1px solid rgba(255,255,255,0.15)',
            fontWeight: 700, fontSize: 15, cursor: 'pointer' }}>
          Export PDF
        </button>
      </div>
    </div>
  );
};

// ─── Phase 4: Dashboard ───────────────────────────────────────────────────────

const Dashboard = ({ onRunNew }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API('/dashboard').then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', padding: 60 }}>Loading dashboard…</div>;
  if (!data?.latest?.overall_score) return (
    <div style={{ textAlign: 'center', padding: 60 }}>
      <p style={{ color: 'rgba(255,255,255,0.4)', marginBottom: 20 }}>No completed assessments yet.</p>
      <button onClick={onRunNew} style={{ ...navBtn, background: '#6366f1' }}>Run Your First Assessment →</button>
    </div>
  );

  const { latest, history, benchmarks } = data;
  const cfg = TIER_CONFIG[latest.risk_tier] || TIER_CONFIG.medium;

  return (
    <div>
      {/* KPI strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Health Score', value: `${Math.round(latest.overall_score)}`, unit: '/ 100', color: cfg.color },
          { label: 'Risk Tier', value: cfg.label, unit: cfg.icon, color: cfg.color },
          { label: 'Sector Percentile', value: latest.benchmark_percentile ? `${latest.benchmark_percentile}th` : 'N/A', unit: 'percentile', color: '#818cf8' },
          { label: 'Assessments Run', value: history.length, unit: 'total', color: '#34d399' },
        ].map(kpi => (
          <div key={kpi.label} style={{
            background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 14, padding: '20px 24px',
          }}>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>{kpi.label}</p>
            <p style={{ color: kpi.color, fontSize: 28, fontWeight: 800, margin: 0 }}>{kpi.value}</p>
            <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12, margin: 0 }}>{kpi.unit}</p>
          </div>
        ))}
      </div>

      {/* Radar + Domain bars */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <div style={cardStyle}>
          <h4 style={cardTitle}>Domain Radar</h4>
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <RadarChart domainScores={latest.domain_scores} />
          </div>
        </div>
        <div style={cardStyle}>
          <h4 style={cardTitle}>Domain Scores vs Sector Median</h4>
          {Object.entries(latest.domain_scores || {}).map(([domain, score]) => (
            <DomainBar key={domain} domain={domain} score={score}
              benchmarkP50={benchmarks?.['overall']?.p50 || null} />
          ))}
        </div>
      </div>

      {/* Score history */}
      {history.length > 1 && (
        <div style={{ ...cardStyle, marginBottom: 24 }}>
          <h4 style={cardTitle}>Score History</h4>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 80, padding: '0 8px' }}>
            {history.map((h, i) => {
              const htcfg = TIER_CONFIG[h.tier] || TIER_CONFIG.medium;
              return (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                  <span style={{ color: htcfg.color, fontSize: 11, fontWeight: 700 }}>{Math.round(h.score)}</span>
                  <div style={{
                    width: '100%', background: htcfg.color, borderRadius: '4px 4px 0 0',
                    height: `${(h.score / 100) * 60}px`, transition: 'height 0.6s ease',
                  }} />
                  <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: 10 }}>{h.date}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h4 style={{ ...cardTitle, margin: 0 }}>Priority Recommendations</h4>
          <button onClick={onRunNew} style={{
            background: '#6366f1', color: 'white', border: 'none',
            padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 600,
          }}>
            Re-run Assessment
          </button>
        </div>
        {(latest.recommendations || []).slice(0, 3).map((rec, i) => (
          <div key={i} style={{
            display: 'flex', gap: 12, padding: '12px 0',
            borderBottom: i < 2 ? '1px solid rgba(255,255,255,0.06)' : 'none',
          }}>
            <span style={{
              background: '#6366f1', color: 'white', borderRadius: 8,
              width: 28, height: 28, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontWeight: 700, fontSize: 13, flexShrink: 0,
            }}>{i + 1}</span>
            <div>
              <p style={{ color: 'white', fontWeight: 600, fontSize: 13, marginBottom: 2 }}>{rec.title}</p>
              <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 12 }}>{rec.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Styles ───────────────────────────────────────────────────────────────────

const labelStyle = { display: 'block', color: 'rgba(255,255,255,0.6)', fontSize: 13, fontWeight: 600, marginBottom: 8 };
const chipStyle = (active) => ({
  padding: '8px 16px', borderRadius: 8, border: '1px solid',
  borderColor: active ? '#6366f1' : 'rgba(255,255,255,0.12)',
  background: active ? 'rgba(99,102,241,0.2)' : 'transparent',
  color: active ? '#a5b4fc' : 'rgba(255,255,255,0.55)',
  cursor: 'pointer', fontSize: 13, fontWeight: 600, transition: 'all 0.15s',
});
const selectStyle = {
  width: '100%', padding: '10px 14px', borderRadius: 8,
  background: '#1a2035', border: '1px solid rgba(255,255,255,0.2)',
  color: 'white', fontSize: 14, marginBottom: 20, outline: 'none',
};
const navBtn = {
  padding: '10px 22px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)',
  background: 'transparent', color: 'white', cursor: 'pointer', fontSize: 14, fontWeight: 600,
};
const refBadge = (color) => ({
  background: color + '18', color: color, fontSize: 11, fontWeight: 600,
  padding: '2px 8px', borderRadius: 4, border: `1px solid ${color}30`,
});
const pillStyle = {
  padding: '3px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600,
  whiteSpace: 'nowrap', textAlign: 'center',
};
const cardStyle = {
  background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 16, padding: 24,
};
const cardTitle = { color: 'white', fontWeight: 700, fontSize: 15, marginBottom: 16 };

// ─── Main component ───────────────────────────────────────────────────────────

export default function CyberHealthIndex() {
  const [phase, setPhase] = useState('intro'); // intro | questions | result | dashboard
  const [questions, setQuestions] = useState({});
  const [assessmentId, setAssessmentId] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Auto-load dashboard if there's a completed assessment
  useEffect(() => {
    API('/dashboard').then(d => {
      if (d?.latest?.overall_score) setPhase('dashboard');
    }).catch(() => {});
  }, []);

  const handleStart = async (formData) => {
    setLoading(true);
    setError(null);
    try {
      const [questionsData, sessionData] = await Promise.all([
        API('/questions'),
        API('/assessment/start', 'POST', formData),
      ]);
      setQuestions(questionsData.domains);
      setAssessmentId(sessionData.assessment_id);
      setPhase('questions');
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh', background: '#0f1117',
      fontFamily: "'DM Sans', 'Inter', system-ui, sans-serif",
      padding: '32px 20px',
    }}>
      {/* Header */}
      <div style={{ maxWidth: 800, margin: '0 auto 32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ color: 'white', fontSize: 24, fontWeight: 800, margin: 0 }}>
              🇬🇧 UK SME Cyber Health Index
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13, margin: '4px 0 0' }}>
              PrepIQ · Benchmark your cyber posture against UK industry peers
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {['dashboard', 'intro'].includes(phase) && phase !== 'dashboard' && (
              <button onClick={() => setPhase('dashboard')}
                style={{ ...navBtn, fontSize: 13 }}>View Dashboard</button>
            )}
            {phase === 'dashboard' && (
              <button onClick={() => setPhase('intro')}
                style={{ ...navBtn, background: '#6366f1', border: 'none', fontSize: 13 }}>
                + New Assessment
              </button>
            )}
          </div>
        </div>

        {/* Phase tabs */}
        <div style={{ display: 'flex', gap: 4, marginTop: 20, background: 'rgba(255,255,255,0.04)', borderRadius: 10, padding: 4 }}>
          {[
            { id: 'intro', label: '1. Setup' },
            { id: 'questions', label: '2. Assessment' },
            { id: 'result', label: '3. Score Card' },
            { id: 'dashboard', label: '4. Dashboard' },
          ].map(tab => (
            <button key={tab.id}
              onClick={() => {
                if (tab.id === 'dashboard') setPhase('dashboard');
                if (tab.id === 'result' && result) setPhase('result');
              }}
              style={{
                flex: 1, padding: '8px 0', borderRadius: 7, border: 'none',
                background: phase === tab.id ? 'rgba(99,102,241,0.3)' : 'transparent',
                color: phase === tab.id ? '#a5b4fc' : 'rgba(255,255,255,0.3)',
                fontWeight: phase === tab.id ? 700 : 400, fontSize: 13,
                cursor: 'pointer', transition: 'all 0.15s',
              }}>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        {error && (
          <div style={{ background: '#7f1d1d', border: '1px solid #ef4444', borderRadius: 10, padding: '12px 16px', marginBottom: 20, color: '#fca5a5', fontSize: 14 }}>
            ⚠️ {error}
          </div>
        )}

        {phase === 'intro' && <IntakeForm onStart={handleStart} loading={loading} />}
        {phase === 'questions' && questions && assessmentId && (
          <QuestionWizard
            questions={questions}
            assessmentId={assessmentId}
            onComplete={(r) => { setResult(r); setPhase('result'); }}
          />
        )}
        {phase === 'result' && result && (
          <ScoreCard result={result} onViewDashboard={() => setPhase('dashboard')}
            onExportPdf={async () => {
              const token = JSON.parse(localStorage.getItem('prepiq-auth') || '{}')?.state?.token;
              const res = await fetch(`/api/health-index/assessment/${assessmentId}/export-pdf`, {
                headers: { Authorization: `Bearer ${token}` }
              });
              if (!res.ok) { alert('Export failed — please try again'); return; }
              const blob = await res.blob();
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `PrepIQ_Health_Index_${assessmentId}.pdf`;
              a.click();
              URL.revokeObjectURL(url);
            }}
          />
        )}
        {phase === 'dashboard' && (
          <Dashboard onRunNew={() => setPhase('intro')} />
        )}
      </div>
    </div>
  );
}
