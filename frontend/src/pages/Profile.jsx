import { useState } from 'react'
import { User, Shield, Key } from 'lucide-react'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
import api from '../utils/api'

export default function Profile() {
  const { user, refreshUser } = useAuthStore()
  const [name, setName] = useState(user?.full_name || '')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put('/users/profile', { full_name: name })
      await refreshUser()
      toast.success('Profile updated')
    } catch {
      toast.error('Failed to update')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-forge-muted text-sm font-mono mb-1">
          <User size={14} className="text-forge-accent" />
          <span>PREPIQ / PROFILE</span>
        </div>
        <h1 className="text-2xl font-bold text-forge-text">Your Profile</h1>
      </div>

      <div className="card mb-4">
        <h2 className="font-semibold text-forge-text mb-4 font-mono">Account Details</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-forge-muted mb-1.5 uppercase tracking-wider">Full Name</label>
            <input value={name} onChange={e => setName(e.target.value)} className="input-field" />
          </div>
          <div>
            <label className="block text-xs font-mono text-forge-muted mb-1.5 uppercase tracking-wider">Email</label>
            <input value={user?.email} disabled className="input-field opacity-50 cursor-not-allowed" />
          </div>
          <div>
            <label className="block text-xs font-mono text-forge-muted mb-1.5 uppercase tracking-wider">Role</label>
            <div className="flex items-center gap-2">
              <Shield size={14} className="text-forge-accent" />
              <span className="text-sm font-mono text-forge-accent">{user?.role?.toUpperCase()}</span>
            </div>
          </div>
          <button onClick={handleSave} className="btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
