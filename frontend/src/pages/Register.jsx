import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../utils/api'

export default function Register() {
  const [step, setStep] = useState('register') // register | verify
  const [form, setForm] = useState({ email: '', password: '', confirmPassword: '', fullName: '' })
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleRegister = async (e) => {
    e.preventDefault()
    if (form.password.length < 8) return toast.error('Password must be at least 8 characters')
    if (form.password !== form.confirmPassword) return toast.error('Passwords do not match')
    setLoading(true)
    try {
      await api.post('/auth/register', {
        email: form.email,
        password: form.password,
        confirm_password: form.confirmPassword,
        full_name: form.fullName,
      })
      toast.success('Account created! Check your email for the 6-digit OTP.')
      setStep('verify')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async (e) => {
    e.preventDefault()
    if (otp.length !== 6) return toast.error('Please enter the 6-digit code')
    setLoading(true)
    try {
      await api.post('/auth/verify-otp', { email: form.email, otp })
      toast.success('Email verified! You can now log in.')
      navigate('/login')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid OTP')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    try {
      await api.post('/auth/resend-otp', null, { params: { email: form.email } })
      toast.success('New OTP sent to your email.')
    } catch (err) {
      toast.error('Could not resend OTP')
    }
  }

  return (
    <div className="min-h-screen bg-forge-bg flex items-center justify-center p-4"
      style={{ backgroundImage: 'radial-gradient(ellipse at 50% 0%, rgba(0,255,136,0.05) 0%, transparent 60%)' }}>
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex w-16 h-16 rounded-2xl bg-forge-accent/10 border border-forge-accent/30 items-center justify-center mb-4">
            <Shield size={32} className="text-forge-accent" />
          </div>
          <h1 className="text-3xl font-bold font-mono text-forge-text tracking-wider">PREPIQ</h1>
          <p className="text-forge-muted text-sm mt-2">
            {step === 'register' ? 'Create your account' : 'Verify your email'}
          </p>
        </div>

        <div className="card">
          {step === 'register' ? (
            <>
              <h2 className="text-lg font-semibold text-forge-text mb-6 font-mono">Register</h2>
              <form onSubmit={handleRegister} className="space-y-4">
                {[
                  { key: 'fullName', label: 'Full Name', type: 'text', placeholder: 'Jane Smith' },
                  { key: 'email', label: 'Email', type: 'email', placeholder: 'you@company.com' },
                  { key: 'password', label: 'Password', type: 'password', placeholder: 'Min. 8 characters' },
                  { key: 'confirmPassword', label: 'Confirm Password', type: 'password', placeholder: 'Re-enter password' },
                ].map(({ key, label, type, placeholder }) => (
                  <div key={key}>
                    <label className="block text-xs font-mono text-forge-muted mb-1.5 uppercase tracking-wider">{label}</label>
                    <input type={type} value={form[key]} onChange={set(key)}
                      className="input-field" placeholder={placeholder} required />
                  </div>
                ))}
                {form.confirmPassword && form.password !== form.confirmPassword && (
                  <p className="text-xs text-red-400 font-mono">Passwords do not match</p>
                )}
                <button type="submit" className="btn-primary w-full" disabled={loading}>
                  {loading ? 'Creating account...' : 'Create Account →'}
                </button>
              </form>
              <p className="text-center text-sm text-forge-muted mt-4">
                Already have an account?{' '}
                <Link to="/login" className="text-forge-accent hover:underline">Sign in</Link>
              </p>
            </>
          ) : (
            <>
              <h2 className="text-lg font-semibold text-forge-text mb-2 font-mono">Check your email</h2>
              <p className="text-forge-muted text-sm mb-6">
                We sent a 6-digit verification code to <strong className="text-forge-text">{form.email}</strong>.
                It expires in 10 minutes.
              </p>
              <form onSubmit={handleVerify} className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-forge-muted mb-1.5 uppercase tracking-wider">
                    Verification Code
                  </label>
                  <input
                    type="text"
                    value={otp}
                    onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="input-field text-center text-2xl font-mono tracking-widest"
                    placeholder="000000"
                    maxLength={6}
                    required
                  />
                </div>
                <button type="submit" className="btn-primary w-full" disabled={loading}>
                  {loading ? 'Verifying...' : 'Verify Email →'}
                </button>
              </form>
              <div className="flex items-center justify-between mt-4">
                <button onClick={handleResend}
                  className="text-xs text-forge-muted hover:text-forge-accent transition-colors">
                  Resend code
                </button>
                <button onClick={() => setStep('register')}
                  className="text-xs text-forge-muted hover:text-forge-accent transition-colors">
                  ← Back
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
