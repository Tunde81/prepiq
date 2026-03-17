import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Minimize2, Bot, User, Loader } from 'lucide-react'
import api from '../utils/api'
import { useLocation } from 'react-router-dom'

function getContext(pathname) {
  if (pathname.includes('/learning/') && pathname !== '/learning') return 'learning module: ' + pathname.split('/learning/')[1]
  if (pathname.includes('/simulations/')) return 'simulation scenario'
  if (pathname.includes('/assessment')) return 'cyber risk assessment'
  if (pathname.includes('/dashboard')) return 'dashboard overview'
  return null
}

const SUGGESTIONS = [
  "What is phishing and how do I spot it?",
  "How do I improve my risk score?",
  "What does GDPR require from SMEs?",
  "What should I do during a ransomware attack?",
]

export default function AICoach() {
  const [open, setOpen] = useState(false)
  const [minimised, setMinimised] = useState(false)
  const [messages, setMessages] = useState([{ role: 'assistant', content: "Hi! I'm CyberCoach, your AI cybersecurity assistant. Ask me anything about cyber threats, best practices, or how to use PrepIQ." }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [available, setAvailable] = useState(true)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const location = useLocation()

  useEffect(() => {
    api.get('/coach/status').then(r => setAvailable(r.data.available)).catch(() => setAvailable(false))
  }, [])

  useEffect(() => {
    if (open && !minimised) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      inputRef.current?.focus()
    }
  }, [messages, open, minimised])

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')
    const newMessages = [...messages, { role: 'user', content: msg }]
    setMessages(newMessages)
    setLoading(true)
    try {
      const history = newMessages.slice(1, -1)
      const res = await api.post('/coach/chat', { message: msg, context: getContext(location.pathname), history })
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.reply }])
    } catch (err) {
      const errMsg = err.response?.status === 429 ? "I'm a bit busy right now - please try again in a moment." : "Sorry, I'm having trouble connecting. Please try again."
      setMessages(prev => [...prev, { role: 'assistant', content: errMsg }])
    } finally {
      setLoading(false)
    }
  }

  if (!available) return null

  return (
    <>
      {!open && (
        <button onClick={() => setOpen(true)} className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-forge-accent text-forge-bg flex items-center justify-center shadow-lg hover:scale-110 transition-all duration-200" style={{boxShadow:'0 0 20px rgba(0,212,255,0.4)'}} title="Open CyberCoach AI">
          <MessageCircle size={24} />
        </button>
      )}
      {open && (
        <div className={`fixed bottom-6 right-6 z-50 w-96 bg-forge-surface border border-forge-border rounded-2xl shadow-2xl flex flex-col transition-all duration-200 ${minimised ? 'h-14' : 'h-[520px]'}`} style={{boxShadow:'0 0 40px rgba(0,212,255,0.15)'}}>
          <div className="flex items-center justify-between px-4 py-3 border-b border-forge-border rounded-t-2xl bg-forge-accent/5 flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-forge-accent/20 border border-forge-accent/40 flex items-center justify-center">
                <Bot size={14} className="text-forge-accent" />
              </div>
              <div>
                <div className="text-sm font-semibold text-forge-text font-mono">CyberCoach</div>
                <div className="text-xs text-green-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block"></span>AI Assistant · Online</div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => setMinimised(m => !m)} className="p-1.5 text-forge-muted hover:text-forge-text rounded-lg hover:bg-forge-border transition-colors"><Minimize2 size={14} /></button>
              <button onClick={() => setOpen(false)} className="p-1.5 text-forge-muted hover:text-red-400 rounded-lg hover:bg-forge-border transition-colors"><X size={14} /></button>
            </div>
          </div>
          {!minimised && (
            <>
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${msg.role === 'user' ? 'bg-forge-accent/20' : 'bg-green-900/30'}`}>
                      {msg.role === 'user' ? <User size={12} className="text-forge-accent" /> : <Bot size={12} className="text-green-400" />}
                    </div>
                    <div className={`max-w-[78%] px-3 py-2 rounded-xl text-xs leading-relaxed ${msg.role === 'user' ? 'bg-forge-accent/10 text-forge-text border border-forge-accent/20' : 'bg-forge-border/50 text-forge-text'}`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-2">
                    <div className="w-6 h-6 rounded-full bg-green-900/30 flex items-center justify-center flex-shrink-0"><Bot size={12} className="text-green-400" /></div>
                    <div className="bg-forge-border/50 px-3 py-2 rounded-xl"><Loader size={12} className="text-forge-muted animate-spin" /></div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
              {messages.length === 1 && (
                <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                  {SUGGESTIONS.slice(0,3).map((s,i) => (
                    <button key={i} onClick={() => send(s)} className="text-xs px-2.5 py-1 rounded-full border border-forge-border text-forge-muted hover:border-forge-accent hover:text-forge-accent transition-all">{s}</button>
                  ))}
                </div>
              )}
              <div className="p-3 border-t border-forge-border flex-shrink-0">
                <div className="flex gap-2">
                  <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()} placeholder="Ask CyberCoach..." className="flex-1 bg-forge-bg border border-forge-border rounded-lg px-3 py-2 text-xs text-forge-text placeholder-forge-muted focus:outline-none focus:border-forge-accent transition-colors" disabled={loading} />
                  <button onClick={() => send()} disabled={!input.trim() || loading} className="w-8 h-8 rounded-lg bg-forge-accent flex items-center justify-center text-forge-bg disabled:opacity-40 hover:opacity-90 transition-all flex-shrink-0"><Send size={13} /></button>
                </div>
                <div className="text-center text-xs text-forge-muted mt-1.5 font-mono">Powered by PrepIQ AI</div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  )
}
