import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, CheckCircle, ChevronRight, Award, Sparkles, Loader, Download } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import api from '../utils/api'

export default function ModuleDetail() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [module, setModule] = useState(null)
  const [activeLesson, setActiveLesson] = useState(0)
  const [loading, setLoading] = useState(true)
  const [quiz, setQuiz] = useState(null)
  const [quizMode, setQuizMode] = useState(false)
  const [answers, setAnswers] = useState([])
  const [quizResult, setQuizResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [generating, setGenerating] = useState(false)

  const generateLessons = async () => {
    setGenerating(true)
    try {
      await api.post('/coach/generate-lessons', { module_id: module.id, topic: module.title, num_lessons: 4 })
      const res = await api.get('/learning/modules/' + module.slug)
      setModule(res.data)
    } catch (e) { console.error(e) }
    finally { setGenerating(false) }
  }

  const downloadCertificate = async () => {
    try {
      const res = await api.get('/certificates/module/' + module.id, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = 'PrepIQ_Certificate_' + module.slug + '.pdf'
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e) { console.error('Certificate download failed', e) }
  }

  useEffect(() => {
    api.get(`/learning/modules/${slug}`)
      .then(r => {
        setModule(r.data)
        api.post('/learning/progress/start', { module_id: r.data.id }).catch(() => {})
      })
      .finally(() => setLoading(false))
  }, [slug])

  const loadQuiz = async () => {
    if (!module?.quizzes?.[0]) return toast.error('No quiz available')
    const res = await api.get(`/learning/quiz/${module.quizzes[0].id}`)
    setQuiz(res.data)
    setAnswers(new Array(res.data.questions.length).fill(-1))
    setQuizMode(true)
  }

  const submitQuiz = async () => {
    if (answers.includes(-1)) return toast.error('Please answer all questions')
    setSubmitting(true)
    try {
      const res = await api.post('/learning/quiz/submit', { quiz_id: quiz.id, answers })
      setQuizResult(res.data)
      if (res.data.passed) {
        toast.success(`Passed! Score: ${res.data.score}%`)
        api.post('/badges/check').catch(() => {})
      }
      else toast.error(`Score: ${res.data.score}% — Need ${quiz.pass_threshold}% to pass`)
    } catch {
      toast.error('Failed to submit quiz')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full p-20">
      <div className="text-forge-accent font-mono text-sm animate-pulse">Loading module...</div>
    </div>
  )

  if (!module) return <div className="p-8 text-forge-muted">Module not found.</div>
  if (!module.lessons || module.lessons.length === 0) return (
    <div className="flex flex-col items-center justify-center h-full p-20 text-center">
      <div className="w-16 h-16 rounded-2xl bg-forge-accent/10 border border-forge-accent/20 flex items-center justify-center mb-4">
        <Sparkles size={28} className="text-forge-accent" />
      </div>
      <h2 className="text-lg font-bold text-forge-text mb-2">{module.title}</h2>
      <p className="text-forge-muted text-sm max-w-md">{module.description}</p>
      <p className="text-forge-muted text-xs font-mono mt-4 opacity-60">No lessons added yet.</p>
      <button onClick={generateLessons} disabled={generating} className="mt-6 flex items-center gap-2 px-6 py-3 bg-forge-accent text-forge-bg rounded-xl font-mono font-bold text-sm hover:opacity-90 transition-all disabled:opacity-40">
        {generating ? <Loader size={16} className="animate-spin" /> : <Sparkles size={16} />}
        {generating ? "Generating lessons with AI..." : "Generate Lessons with AI"}
      </button>
      <button onClick={() => navigate("/learning")} className="mt-4 flex items-center gap-2 text-sm text-forge-muted hover:text-forge-accent transition-colors">
        <ArrowLeft size={14} /> Back to Modules
      </button>
    </div>
  )

  return (
    <div className="flex h-full">
      {/* Sidebar - lessons list */}
      <div className="w-72 flex-shrink-0 bg-forge-surface border-r border-forge-border overflow-y-auto">
        <div className="p-4 border-b border-forge-border">
          <button onClick={() => navigate('/learning')} className="flex items-center gap-2 text-forge-muted hover:text-forge-text text-sm transition-colors">
            <ArrowLeft size={14} />
            Back to Modules
          </button>
          <h2 className="font-semibold text-forge-text text-sm mt-3">{module.title}</h2>
        </div>
        <nav className="p-3 space-y-1">
          {module.lessons.map((lesson, i) => (
            <button
              key={lesson.id}
              onClick={() => { setActiveLesson(i); setQuizMode(false); setQuizResult(null) }}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-xs transition-all ${
                activeLesson === i && !quizMode
                  ? 'bg-forge-accent/10 text-forge-accent border border-forge-accent/20'
                  : 'text-forge-muted hover:text-forge-text hover:bg-forge-border'
              }`}
            >
              <span className="font-mono mr-2">{String(i + 1).padStart(2, '0')}.</span>
              {lesson.title}
            </button>
          ))}
          {module.quizzes.length > 0 && (
            <button
              onClick={loadQuiz}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-xs transition-all flex items-center gap-2 ${
                quizMode
                  ? 'bg-forge-yellow/10 text-forge-yellow border border-forge-yellow/20'
                  : 'text-forge-muted hover:text-forge-text hover:bg-forge-border'
              }`}
            >
              <Award size={12} />
              Knowledge Check
            </button>
          )}
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {!quizMode ? (
          <div className="max-w-3xl mx-auto">
            <div className="mb-6">
              <h1 className="text-xl font-bold text-forge-text">{module.lessons[activeLesson]?.title}</h1>
            </div>
            <div className="prose prose-invert prose-sm max-w-none text-forge-text">
              <ReactMarkdown
                components={{
                  h2: ({ children }) => <h2 className="text-forge-accent font-mono text-lg font-bold mt-8 mb-4 border-b border-forge-border pb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-forge-text font-semibold mt-6 mb-3">{children}</h3>,
                  strong: ({ children }) => <strong className="text-forge-accent">{children}</strong>,
                  ul: ({ children }) => <ul className="space-y-2 list-none pl-0">{children}</ul>,
                  li: ({ children }) => <li className="flex gap-2 text-forge-muted text-sm"><span className="text-forge-accent mt-1">▸</span><span>{children}</span></li>,
                  code: ({ children }) => <code className="bg-forge-border text-forge-accent px-1.5 py-0.5 rounded font-mono text-xs">{children}</code>,
                  p: ({ children }) => <p className="text-forge-muted text-sm leading-relaxed mb-4">{children}</p>,
                }}
              >
                {module.lessons[activeLesson]?.content}
              </ReactMarkdown>
            </div>
            {activeLesson < module.lessons.length - 1 && (
              <button
                onClick={() => setActiveLesson(i => i + 1)}
                className="btn-primary mt-8 flex items-center gap-2"
              >
                Next Lesson <ChevronRight size={16} />
              </button>
            )}
          </div>
        ) : (
          <div className="max-w-2xl mx-auto">
            <h1 className="text-xl font-bold text-forge-text mb-2">{quiz?.title}</h1>
            <p className="text-forge-muted text-sm mb-8 font-mono">Pass threshold: {quiz?.pass_threshold}%</p>

            {quizResult ? (
              <div className="card">
                <div className={`text-center py-6 ${quizResult.passed ? 'text-forge-green' : 'text-forge-red'}`}>
                  {quizResult.passed ? <CheckCircle size={40} className="mx-auto mb-3" /> : <Award size={40} className="mx-auto mb-3" />}
                  <div className="text-3xl font-bold font-mono">{quizResult.score}%</div>
                  <div className="text-sm mt-1">{quizResult.passed ? 'Passed!' : 'Not quite — review the lessons and try again'}</div>
                  {quizResult.passed && (
                    <button onClick={downloadCertificate} className="mt-4 flex items-center gap-2 mx-auto px-5 py-2.5 bg-forge-accent text-forge-bg rounded-xl font-mono font-bold text-sm hover:opacity-90 transition-all">
                      <Download size={15} /> Download Certificate
                    </button>
                  )}
                </div>
                <div className="space-y-4 mt-6">
                  {quiz.questions.map((q, i) => (
                    <div key={i} className={`p-3 rounded-lg border ${quizResult.results[i]?.correct ? 'border-green-800/30 bg-green-900/10' : 'border-red-800/30 bg-red-900/10'}`}>
                      <p className="text-sm text-forge-text mb-2">{q.question}</p>
                      <p className="text-xs text-forge-muted">{quizResult.results[i]?.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {quiz?.questions.map((q, i) => (
                  <div key={i} className="card">
                    <p className="text-sm font-medium text-forge-text mb-4">
                      <span className="text-forge-accent font-mono mr-2">Q{i + 1}.</span>
                      {q.question}
                    </p>
                    <div className="space-y-2">
                      {q.options.map((opt, j) => (
                        <button
                          key={j}
                          onClick={() => {
                            const newAnswers = [...answers]
                            newAnswers[i] = j
                            setAnswers(newAnswers)
                          }}
                          className={`w-full text-left px-4 py-3 rounded-lg text-sm border transition-all ${
                            answers[i] === j
                              ? 'border-forge-accent bg-forge-accent/10 text-forge-accent'
                              : 'border-forge-border text-forge-muted hover:border-forge-accent/50 hover:text-forge-text'
                          }`}
                        >
                          <span className="font-mono mr-2">{String.fromCharCode(65 + j)}.</span>
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
                <button onClick={submitQuiz} className="btn-primary" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit Answers'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
