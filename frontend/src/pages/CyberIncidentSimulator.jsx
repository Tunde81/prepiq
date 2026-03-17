import React, { useState, useEffect, useRef, useCallback } from 'react';

// ─── Config ───────────────────────────────────────────────────────────────────

const CATEGORY_CONFIG = {
  ransomware:               { icon: '🔐', color: '#ef4444', label: 'Ransomware' },
  phishing:                 { icon: '🎣', color: '#f97316', label: 'Phishing' },
  data_breach:              { icon: '💧', color: '#8b5cf6', label: 'Data Breach' },
  insider_threat:           { icon: '👤', color: '#ec4899', label: 'Insider Threat' },
  supply_chain:             { icon: '🔗', color: '#06b6d4', label: 'Supply Chain' },
  ddos:                     { icon: '🌊', color: '#3b82f6', label: 'DDoS' },
  business_email_compromise:{ icon: '✉️', color: '#fbbf24', label: 'BEC' },
  cloud_misconfiguration:   { icon: '☁️', color: '#10b981', label: 'Cloud Misconfig' },
};

const DIFFICULTY_CONFIG = {
  beginner:     { color: '#10b981', label: 'Beginner' },
  intermediate: { color: '#fbbf24', label: 'Intermediate' },
  advanced:     { color: '#ef4444', label: 'Advanced' },
};

const MODE_CONFIG = {
  tabletop:        { icon: '🗺️', label: 'Tabletop', desc: 'Choose-your-own-response scenario walkthrough' },
  timed_challenge: { icon: '⏱️', label: 'Timed Challenge', desc: 'Answer knowledge challenges against the clock' },
  ai_debrief:      { icon: '🤖', label: 'AI Debrief', desc: 'CyberCoach-led conversation debrief' },
};

// ─── API ──────────────────────────────────────────────────────────────────────

const API = async (path, method = 'GET', body = null) => {
  const token = JSON.parse(localStorage.getItem('prepiq-auth') || '{}')?.state?.token;
  const res = await fetch(`/api/simulator${path}`, {
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

const streamDebrief = async (sessionId, message, onChunk) => {
  const token = JSON.parse(localStorage.getItem('prepiq-auth') || '{}')?.state?.token;
  const res = await fetch(`/api/simulator/session/${sessionId}/debrief`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message }),
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value));
  }
};

// ─── Shared styles ────────────────────────────────────────────────────────────

const card = {
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 16, padding: 24,
};
const btn = (variant = 'default') => ({
  padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
  fontWeight: 600, fontSize: 14, transition: 'all 0.15s',
  ...(variant === 'primary'  ? { background: '#6366f1', color: 'white' } : {}),
  ...(variant === 'danger'   ? { background: '#ef4444', color: 'white' } : {}),
  ...(variant === 'success'  ? { background: '#10b981', color: 'white' } : {}),
  ...(variant === 'ghost'    ? { background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.7)', border: '1px solid rgba(255,255,255,0.1)' } : {}),
  ...(variant === 'default'  ? { background: 'rgba(255,255,255,0.06)', color: 'white', border: '1px solid rgba(255,255,255,0.12)' } : {}),
});

// ─── Scenario Library ─────────────────────────────────────────────────────────

const ScenarioCard = ({ scenario, onSelect }) => {
  const cat = CATEGORY_CONFIG[scenario.category] || { icon: '⚡', color: '#6366f1', label: scenario.category };
  const diff = DIFFICULTY_CONFIG[scenario.difficulty] || { color: '#6366f1', label: scenario.difficulty };
  return (
    <div style={{
      ...card, cursor: 'pointer', transition: 'border-color 0.2s, transform 0.15s',
      borderColor: 'rgba(255,255,255,0.08)',
    }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = cat.color + '60'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; e.currentTarget.style.transform = 'translateY(0)'; }}
      onClick={() => onSelect(scenario)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 22 }}>{cat.icon}</span>
          <span style={{ color: cat.color, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>
            {cat.label}
          </span>
        </div>
        <span style={{
          background: diff.color + '22', color: diff.color,
          padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
        }}>{diff.label}</span>
      </div>
      <h3 style={{ color: 'white', fontWeight: 700, fontSize: 15, marginBottom: 6 }}>{scenario.title}</h3>
      <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 13, lineHeight: 1.5, marginBottom: 12 }}>
        {scenario.synopsis.slice(0, 120)}…
      </p>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: 12 }}>⏱ ~{scenario.estimated_minutes} min</span>
        <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: 12 }}>📋 {scenario.phase_count} phases</span>
        {scenario.has_challenges && <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: 12 }}>⚡ Timed challenges</span>}
      </div>
    </div>
  );
};

// ─── Mode Selector ────────────────────────────────────────────────────────────

const ModeSelector = ({ scenario, onStart, onBack }) => {
  const [selectedMode, setSelectedMode] = useState(null);
  const cat = CATEGORY_CONFIG[scenario.category] || { icon: '⚡', color: '#6366f1' };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <button onClick={onBack} style={{ ...btn('ghost'), marginBottom: 20, fontSize: 13 }}>← Back to Scenarios</button>
      <div style={{ ...card, marginBottom: 20, borderColor: cat.color + '40' }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: 28 }}>{cat.icon}</span>
          <div>
            <h2 style={{ color: 'white', fontWeight: 800, fontSize: 18, margin: 0 }}>{scenario.title}</h2>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, margin: 0 }}>{scenario.synopsis}</p>
          </div>
        </div>
        {scenario.frameworks && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
            {scenario.frameworks.map(f => (
              <span key={f} style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8', padding: '2px 8px', borderRadius: 4, fontSize: 11 }}>{f}</span>
            ))}
          </div>
        )}
      </div>

      <h3 style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, fontWeight: 600, marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
        Select Mode
      </h3>
      {Object.entries(MODE_CONFIG).map(([mode, cfg]) => (
        <div key={mode} onClick={() => setSelectedMode(mode)}
          style={{
            ...card, cursor: 'pointer', marginBottom: 10,
            borderColor: selectedMode === mode ? '#6366f1' : 'rgba(255,255,255,0.08)',
            background: selectedMode === mode ? 'rgba(99,102,241,0.1)' : 'rgba(255,255,255,0.03)',
            transition: 'all 0.15s',
          }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ fontSize: 24 }}>{cfg.icon}</span>
            <div>
              <p style={{ color: 'white', fontWeight: 700, fontSize: 14, margin: 0 }}>{cfg.label}</p>
              <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 13, margin: 0 }}>{cfg.desc}</p>
            </div>
            {selectedMode === mode && <span style={{ marginLeft: 'auto', color: '#6366f1', fontSize: 18 }}>✓</span>}
          </div>
        </div>
      ))}

      <button onClick={() => onStart(selectedMode)} disabled={!selectedMode}
        style={{ ...btn('primary'), width: '100%', marginTop: 8, padding: '13px 0', fontSize: 15, opacity: selectedMode ? 1 : 0.4 }}>
        Launch Simulation →
      </button>
    </div>
  );
};

// ─── Tabletop Simulator ───────────────────────────────────────────────────────

const TabletopSimulator = ({ scenario, session, onComplete }) => {
  const [phaseIdx, setPhaseIdx] = useState(0);
  const [selectedChoice, setSelectedChoice] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [decisions, setDecisions] = useState([]);

  const phase = scenario.phases[phaseIdx];
  const isLast = phaseIdx === scenario.phases.length - 1;

  const submitDecision = async () => {
    setSubmitting(true);
    try {
      const result = await API(`/session/${session.session_id}/decision`, 'POST', {
        phase_id: phase.phase_id,
        choice_id: selectedChoice,
      });
      setFeedback(result);
      setDecisions(d => [...d, { phase_id: phase.phase_id, choice_id: selectedChoice, ...result }]);
    } catch (e) { alert(e.message); }
    setSubmitting(false);
  };

  const next = async () => {
    if (isLast) {
      const elapsed = Math.round((Date.now() - session._startTime) / 1000);
      const result = await API(`/session/${session.session_id}/complete?elapsed_seconds=${elapsed}`, 'POST');
      onComplete({ ...result, decisions });
    } else {
      setPhaseIdx(i => i + 1);
      setSelectedChoice(null);
      setFeedback(null);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      {/* Phase progress */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
        {scenario.phases.map((p, i) => (
          <div key={p.phase_id} style={{
            flex: 1, height: 4, borderRadius: 2,
            background: i < phaseIdx ? '#6366f1' : i === phaseIdx ? '#818cf8' : 'rgba(255,255,255,0.08)',
          }} />
        ))}
      </div>

      {/* Inject */}
      <div style={{ ...card, borderLeft: '3px solid #ef4444', marginBottom: 20 }}>
        <p style={{ color: '#ef4444', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
          🚨 Phase {phaseIdx + 1}: {phase.title}
        </p>
        <p style={{ color: 'rgba(255,255,255,0.85)', fontSize: 15, lineHeight: 1.7 }}>
          {feedback ? phase.inject : (phaseIdx === 0 ? scenario.initial_inject : phase.inject)}
        </p>
      </div>

      {/* Choices */}
      {!feedback && (
        <div style={{ marginBottom: 20 }}>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13, marginBottom: 12 }}>
            What do you do?
          </p>
          {phase.choices.map((choice, i) => (
            <div key={choice.id} onClick={() => setSelectedChoice(choice.id)}
              style={{
                ...card, cursor: 'pointer', marginBottom: 10,
                borderColor: selectedChoice === choice.id ? '#6366f1' : 'rgba(255,255,255,0.08)',
                background: selectedChoice === choice.id ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.03)',
                transition: 'all 0.15s',
              }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <span style={{
                  background: selectedChoice === choice.id ? '#6366f1' : 'rgba(255,255,255,0.08)',
                  color: 'white', borderRadius: 6, width: 26, height: 26,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700, flexShrink: 0,
                }}>{String.fromCharCode(65 + i)}</span>
                <p style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14, lineHeight: 1.5, margin: 0 }}>{choice.text}</p>
              </div>
            </div>
          ))}
          <button onClick={submitDecision} disabled={!selectedChoice || submitting}
            style={{ ...btn('primary'), marginTop: 8, opacity: selectedChoice ? 1 : 0.4 }}>
            {submitting ? 'Submitting…' : 'Submit Decision →'}
          </button>
        </div>
      )}

      {/* Feedback */}
      {feedback && (
        <div>
          <div style={{
            ...card, marginBottom: 16,
            borderColor: feedback.optimal ? '#10b981' : feedback.score >= 0.5 ? '#fbbf24' : '#ef4444',
            background: feedback.optimal ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.03)',
          }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 20 }}>{feedback.optimal ? '✅' : feedback.score >= 0.5 ? '⚠️' : '❌'}</span>
              <span style={{ fontWeight: 700, color: feedback.optimal ? '#10b981' : feedback.score >= 0.5 ? '#fbbf24' : '#ef4444', fontSize: 14 }}>
                {feedback.optimal ? 'Optimal Response' : feedback.score >= 0.5 ? 'Acceptable — but could be better' : 'Poor Response'}
              </span>
              <span style={{ marginLeft: 'auto', color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                Score: {Math.round(feedback.score * 100)}%
              </span>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.75)', fontSize: 14, lineHeight: 1.6, marginBottom: 8 }}>
              {feedback.feedback}
            </p>
            {feedback.consequence && (
              <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '10px 14px' }}>
                <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>What happened</p>
                <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, margin: 0 }}>{feedback.consequence}</p>
              </div>
            )}
          </div>
          <button onClick={next} style={{ ...btn('primary') }}>
            {isLast ? 'Complete Simulation 🎯' : 'Next Phase →'}
          </button>
        </div>
      )}
    </div>
  );
};

// ─── Timed Challenge ──────────────────────────────────────────────────────────

const TimedChallenge = ({ scenario, session, onComplete }) => {
  const challenges = scenario.timed_challenges || [];
  const [idx, setIdx] = useState(0);
  const [answer, setAnswer] = useState('');
  const [timeLeft, setTimeLeft] = useState(challenges[0]?.time_limit_seconds || 60);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState([]);
  const [hintShown, setHintShown] = useState(false);
  const intervalRef = useRef(null);
  const startTimeRef = useRef(Date.now());

  const challenge = challenges[idx];

  useEffect(() => {
    setTimeLeft(challenge?.time_limit_seconds || 60);
    setHintShown(false);
    startTimeRef.current = Date.now();
    intervalRef.current = setInterval(() => {
      setTimeLeft(t => {
        if (t <= 1) {
          clearInterval(intervalRef.current);
          handleTimeOut();
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(intervalRef.current);
  }, [idx]);

  const handleTimeOut = () => {
    if (!result) submitAnswer(true);
  };

  const submitAnswer = async (timedOut = false) => {
    clearInterval(intervalRef.current);
    setSubmitting(true);
    const elapsed = Math.round((Date.now() - startTimeRef.current) / 1000);
    try {
      const res = await API(`/session/${session.session_id}/challenge`, 'POST', {
        challenge_id: challenge.challenge_id,
        answer: timedOut ? '' : answer,
        time_taken_seconds: elapsed,
      });
      setResult({ ...res, timedOut });
      setResults(r => [...r, { ...res, timedOut, elapsed }]);
    } catch (e) { alert(e.message); }
    setSubmitting(false);
  };

  const next = async () => {
    if (idx < challenges.length - 1) {
      setIdx(i => i + 1);
      setAnswer('');
      setResult(null);
    } else {
      const totalElapsed = Math.round((Date.now() - session._startTime) / 1000);
      const res = await API(`/session/${session.session_id}/complete?elapsed_seconds=${totalElapsed}`, 'POST');
      onComplete({ ...res, challengeResults: results });
    }
  };

  const timerColor = timeLeft <= 10 ? '#ef4444' : timeLeft <= 20 ? '#fbbf24' : '#10b981';
  const timerPct = (timeLeft / (challenge?.time_limit_seconds || 60)) * 100;

  return (
    <div style={{ maxWidth: 620, margin: '0 auto' }}>
      {/* Progress */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13 }}>Challenge {idx + 1} of {challenges.length}</span>
        <span style={{ color: timerColor, fontWeight: 800, fontSize: 20, fontFamily: 'monospace' }}>
          {String(Math.floor(timeLeft / 60)).padStart(2, '0')}:{String(timeLeft % 60).padStart(2, '0')}
        </span>
      </div>
      <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 6, marginBottom: 24 }}>
        <div style={{ background: timerColor, height: '100%', borderRadius: 4, width: `${timerPct}%`, transition: 'width 1s linear, background 0.3s' }} />
      </div>

      {/* Question */}
      <div style={{ ...card, marginBottom: 16 }}>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>⚡ Timed Challenge</p>
        <p style={{ color: 'white', fontSize: 16, lineHeight: 1.6, fontWeight: 600 }}>{challenge?.task}</p>
        {hintShown && challenge?.hints?.[0] && (
          <div style={{ marginTop: 12, background: 'rgba(99,102,241,0.1)', borderRadius: 8, padding: '8px 12px' }}>
            <p style={{ color: '#818cf8', fontSize: 13, margin: 0 }}>💡 Hint: {challenge.hints[0]}</p>
          </div>
        )}
      </div>

      {!result && (
        <>
          <input
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && answer.trim() && submitAnswer()}
            placeholder="Type your answer…"
            style={{
              width: '100%', padding: '12px 16px', borderRadius: 10,
              background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
              color: 'white', fontSize: 15, outline: 'none', marginBottom: 12, boxSizing: 'border-box',
            }}
          />
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => submitAnswer()} disabled={!answer.trim() || submitting}
              style={{ ...btn('primary'), flex: 1, opacity: answer.trim() ? 1 : 0.4 }}>
              Submit Answer ↵
            </button>
            <button onClick={() => setHintShown(true)} disabled={hintShown}
              style={{ ...btn('ghost'), opacity: hintShown ? 0.3 : 1 }}>
              Hint
            </button>
          </div>
        </>
      )}

      {result && (
        <div>
          <div style={{
            ...card, marginBottom: 16,
            borderColor: result.correct ? '#10b981' : '#ef4444',
            background: result.correct ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
          }}>
            <p style={{ fontWeight: 700, color: result.correct ? '#10b981' : '#ef4444', marginBottom: 6 }}>
              {result.timedOut ? '⏰ Time\'s up!' : result.correct ? '✅ Correct!' : '❌ Incorrect'}
            </p>
            {!result.correct && result.correct_answer && (
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, marginBottom: 6 }}>
                Answer: <strong style={{ color: '#fbbf24' }}>{result.correct_answer}</strong>
              </p>
            )}
            {result.explanation && (
              <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 13, lineHeight: 1.5 }}>{result.explanation}</p>
            )}
          </div>
          <button onClick={next} style={{ ...btn('primary') }}>
            {idx < challenges.length - 1 ? 'Next Challenge →' : 'Finish & See Score 🎯'}
          </button>
        </div>
      )}
    </div>
  );
};

// ─── AI Debrief ───────────────────────────────────────────────────────────────

const AIDebrief = ({ scenario, session, onComplete }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamBuffer, setStreamBuffer] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    // Auto-start debrief
    startDebrief();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamBuffer]);

  const startDebrief = async () => {
    setStreaming(true);
    setStreamBuffer('');
    let full = '';
    try {
      await streamDebrief(session.session_id, '__init__', chunk => {
        full += chunk;
        setStreamBuffer(b => b + chunk);
      });
      setMessages([{ role: 'assistant', content: full }]);
      setStreamBuffer('');
    } catch (e) {
      setMessages([{ role: 'assistant', content: 'CyberCoach is unavailable. Please ensure ANTHROPIC_API_KEY is configured.' }]);
    }
    setStreaming(false);
  };

  const sendMessage = async () => {
    if (!input.trim() || streaming) return;
    const userMsg = input.trim();
    setInput('');
    setMessages(m => [...m, { role: 'user', content: userMsg }]);
    setStreaming(true);
    setStreamBuffer('');
    let full = '';
    try {
      await streamDebrief(session.session_id, userMsg, chunk => {
        full += chunk;
        setStreamBuffer(b => b + chunk);
      });
      setMessages(m => [...m, { role: 'assistant', content: full }]);
      setStreamBuffer('');
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: 'Error: ' + e.message }]);
    }
    setStreaming(false);
  };

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', display: 'flex', flexDirection: 'column', height: '75vh' }}>
      <div style={{ ...card, marginBottom: 12, padding: '12px 20px' }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ fontSize: 24 }}>🤖</span>
          <div>
            <p style={{ color: 'white', fontWeight: 700, fontSize: 14, margin: 0 }}>CyberCoach AI Debrief</p>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, margin: 0 }}>{scenario.title}</p>
          </div>
          <button onClick={onComplete} style={{ ...btn('ghost'), marginLeft: 'auto', fontSize: 12 }}>
            Finish Debrief
          </button>
        </div>
      </div>

      {/* Chat window */}
      <div style={{
        flex: 1, overflow: 'auto', padding: '16px 0',
        display: 'flex', flexDirection: 'column', gap: 12,
      }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '80%', padding: '12px 16px', borderRadius: 12,
              background: m.role === 'user' ? '#6366f1' : 'rgba(255,255,255,0.06)',
              color: 'white', fontSize: 14, lineHeight: 1.6,
              borderBottomRightRadius: m.role === 'user' ? 4 : 12,
              borderBottomLeftRadius: m.role === 'assistant' ? 4 : 12,
            }}>
              {m.role === 'assistant' && (
                <p style={{ color: '#818cf8', fontSize: 11, fontWeight: 700, marginBottom: 6 }}>🤖 CyberCoach</p>
              )}
              <p style={{ margin: 0 }}>{m.content}</p>
            </div>
          </div>
        ))}
        {streaming && streamBuffer && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{
              maxWidth: '80%', padding: '12px 16px', borderRadius: 12,
              background: 'rgba(255,255,255,0.06)', color: 'white', fontSize: 14, lineHeight: 1.6,
              borderBottomLeftRadius: 4,
            }}>
              <p style={{ color: '#818cf8', fontSize: 11, fontWeight: 700, marginBottom: 6 }}>🤖 CyberCoach</p>
              <p style={{ margin: 0 }}>{streamBuffer}<span style={{ animation: 'pulse 1s infinite', opacity: 0.5 }}>▊</span></p>
            </div>
          </div>
        )}
        {streaming && !streamBuffer && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', padding: '8px 16px' }}>
            <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>CyberCoach is thinking…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Ask a follow-up question…"
          disabled={streaming}
          style={{
            flex: 1, padding: '12px 16px', borderRadius: 10,
            background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
            color: 'white', fontSize: 14, outline: 'none',
            opacity: streaming ? 0.5 : 1,
          }}
        />
        <button onClick={sendMessage} disabled={!input.trim() || streaming}
          style={{ ...btn('primary'), opacity: input.trim() && !streaming ? 1 : 0.4 }}>
          Send
        </button>
      </div>
    </div>
  );
};

// ─── Results Screen ───────────────────────────────────────────────────────────

const ResultsScreen = ({ result, scenario, onLeaderboard, onRetry, onBack }) => {
  const overall = result.overall_score || 0;
  const tierColor = overall >= 80 ? '#10b981' : overall >= 60 ? '#fbbf24' : '#ef4444';
  const tierLabel = overall >= 80 ? 'Excellent' : overall >= 60 ? 'Competent' : 'Needs Improvement';

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div style={{ ...card, textAlign: 'center', marginBottom: 20, borderColor: tierColor + '40' }}>
        <p style={{ color: tierColor, fontSize: 48, margin: '0 0 8px' }}>
          {overall >= 80 ? '🏆' : overall >= 60 ? '✅' : '📚'}
        </p>
        <h2 style={{ color: 'white', fontWeight: 800, fontSize: 24, margin: '0 0 4px' }}>{tierLabel}</h2>
        <p style={{ color: tierColor, fontSize: 40, fontWeight: 900, margin: '0 0 8px' }}>
          {Math.round(overall)}<span style={{ fontSize: 20, opacity: 0.6 }}>/100</span>
        </p>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 14 }}>{scenario.title}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'Decision Score', value: result.decision_score, icon: '🗺️' },
          { label: 'Speed Score', value: result.speed_score, icon: '⚡' },
        ].map(kpi => kpi.value != null && (
          <div key={kpi.label} style={card}>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, marginBottom: 4 }}>{kpi.icon} {kpi.label}</p>
            <p style={{ color: 'white', fontSize: 28, fontWeight: 800, margin: 0 }}>{Math.round(kpi.value)}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button onClick={onLeaderboard} style={btn('ghost')}>🏅 Leaderboard</button>
        <button onClick={onRetry} style={btn('ghost')}>↩ Retry</button>
        <button onClick={onBack} style={{ ...btn('primary'), flex: 1 }}>← Back to Scenarios</button>
      </div>
    </div>
  );
};

// ─── Leaderboard ──────────────────────────────────────────────────────────────

const Leaderboard = ({ scenario, onBack }) => {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    API(`/leaderboard/${scenario.id}`).then(setRows).catch(console.error);
  }, [scenario.id]);

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <button onClick={onBack} style={{ ...btn('ghost'), marginBottom: 16, fontSize: 13 }}>← Back</button>
      <div style={card}>
        <h3 style={{ color: 'white', fontWeight: 700, marginBottom: 20 }}>🏅 {scenario.title} — Leaderboard</h3>
        {rows.length === 0 ? (
          <p style={{ color: 'rgba(255,255,255,0.4)', textAlign: 'center', padding: 20 }}>No scores yet — be the first!</p>
        ) : rows.map(r => (
          <div key={r.rank} style={{
            display: 'flex', gap: 12, alignItems: 'center', padding: '10px 0',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            background: r.is_current_user ? 'rgba(99,102,241,0.08)' : 'transparent',
            borderRadius: r.is_current_user ? 8 : 0, paddingLeft: r.is_current_user ? 8 : 0,
          }}>
            <span style={{
              width: 28, height: 28, borderRadius: 8,
              background: r.rank <= 3 ? ['#fbbf24', '#9ca3af', '#b45309'][r.rank - 1] : 'rgba(255,255,255,0.08)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontWeight: 800, fontSize: 13, flexShrink: 0,
            }}>{r.rank}</span>
            <span style={{ color: 'white', fontSize: 14, fontWeight: r.is_current_user ? 700 : 400, flex: 1 }}>
              {r.username} {r.is_current_user && '(you)'}
            </span>
            <span style={{ color: '#6366f1', fontWeight: 700 }}>{Math.round(r.overall_score)}</span>
            {r.elapsed_seconds && (
              <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12 }}>
                {Math.floor(r.elapsed_seconds / 60)}m {r.elapsed_seconds % 60}s
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

export default function CyberIncidentSimulator() {
  const [view, setView] = useState('library');  // library | mode | sim | result | leaderboard
  const [scenarios, setScenarios] = useState([]);
  const [selected, setSelected] = useState(null);
  const [session, setSession] = useState(null);
  const [mode, setMode] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ category: '', difficulty: '' });

  useEffect(() => {
    API('/scenarios').then(s => { setScenarios(s); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const handleSelectScenario = (scenario) => {
    setSelected(scenario);
    setView('mode');
  };

  const handleStartSim = async (selectedMode) => {
    setLoading(true);
    try {
      const s = await API('/session/start', 'POST', {
        scenario_id: selected.id,
        mode: selectedMode,
      });
      s._startTime = Date.now();
      setSession(s);
      setMode(selectedMode);
      setView('sim');
    } catch (e) { alert(e.message); }
    setLoading(false);
  };

  const handleComplete = (r) => {
    setResult(r);
    setView('result');
  };

  const filtered = scenarios.filter(s =>
    (!filter.category || s.category === filter.category) &&
    (!filter.difficulty || s.difficulty === filter.difficulty)
  );

  return (
    <div style={{
      minHeight: '100vh', background: '#0f1117',
      fontFamily: "'DM Sans', 'Inter', system-ui, sans-serif",
      padding: '28px 20px',
    }}>
      {/* Header */}
      <div style={{ maxWidth: 860, margin: '0 auto 28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ color: 'white', fontSize: 24, fontWeight: 800, margin: 0 }}>
              ⚡ Cyber Incident Simulator
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13, margin: '4px 0 0' }}>
              PrepIQ · Tabletop scenarios, timed challenges, AI-led debrief
            </p>
          </div>
          {view !== 'library' && (
            <button onClick={() => setView('library')} style={{ ...btn('ghost'), fontSize: 13 }}>
              ← Scenario Library
            </button>
          )}
        </div>
      </div>

      <div style={{ maxWidth: 860, margin: '0 auto' }}>
        {loading && <p style={{ color: 'rgba(255,255,255,0.3)', textAlign: 'center', padding: 40 }}>Loading…</p>}

        {!loading && view === 'library' && (
          <div>
            {/* Filters */}
            <div style={{ display: 'flex', gap: 10, marginBottom: 24, flexWrap: 'wrap' }}>
              <select value={filter.category} onChange={e => setFilter(f => ({ ...f, category: e.target.value }))}
                style={{ padding: '8px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: 'white', fontSize: 13, outline: 'none' }}>
                <option value="">All categories</option>
                {Object.entries(CATEGORY_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.icon} {v.label}</option>)}
              </select>
              <select value={filter.difficulty} onChange={e => setFilter(f => ({ ...f, difficulty: e.target.value }))}
                style={{ padding: '8px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: 'white', fontSize: 13, outline: 'none' }}>
                <option value="">All difficulties</option>
                {Object.entries(DIFFICULTY_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
              <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13, alignSelf: 'center', marginLeft: 4 }}>
                {filtered.length} scenario{filtered.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
              {filtered.map(s => <ScenarioCard key={s.id} scenario={s} onSelect={handleSelectScenario} />)}
            </div>
          </div>
        )}

        {!loading && view === 'mode' && selected && (
          <ModeSelector scenario={selected} onStart={handleStartSim} onBack={() => setView('library')} />
        )}

        {!loading && view === 'sim' && session && selected && mode === 'tabletop' && (
          <TabletopSimulator scenario={session.scenario} session={session} onComplete={handleComplete} />
        )}

        {!loading && view === 'sim' && session && selected && mode === 'timed_challenge' && (
          <TimedChallenge scenario={session.scenario} session={session} onComplete={handleComplete} />
        )}

        {!loading && view === 'sim' && session && selected && mode === 'ai_debrief' && (
          <AIDebrief scenario={session.scenario} session={session} onComplete={() => setView('library')} />
        )}

        {!loading && view === 'result' && result && selected && (
          <ResultsScreen
            result={result}
            scenario={selected}
            onLeaderboard={() => setView('leaderboard')}
            onRetry={() => handleStartSim(mode)}
            onBack={() => setView('library')}
          />
        )}

        {!loading && view === 'leaderboard' && selected && (
          <Leaderboard scenario={selected} onBack={() => setView('result')} />
        )}
      </div>
    </div>
  );
}
