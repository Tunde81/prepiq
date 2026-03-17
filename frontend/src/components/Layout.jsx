import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Shield, LayoutDashboard, BookOpen, Terminal, ClipboardCheck, User, LogOut, Settings, Zap, FileCheck, Sparkles, Building2 } from 'lucide-react'
import useAuthStore from '../store/authStore'
import clsx from 'clsx'
import AICoach from './AICoach'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/learning', icon: BookOpen, label: 'Learning' },
  { to: '/simulations', icon: Terminal, label: 'Simulations' },
  { to: '/assessment', icon: ClipboardCheck, label: 'Risk Assessment' },
  { to: '/compliance', icon: FileCheck, label: 'Compliance' },
  { to: '/paths', icon: Sparkles, label: 'Learning Paths' },
  { to: '/organisation', icon: Building2, label: 'Organisation' },
  { to: '/health-index', icon: Shield, label: 'Health Index' },
  { to: '/simulator', icon: Zap, label: 'Incident Simulator' },
  { to: '/phishing', icon: Shield, label: 'Phishing Simulator' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-forge-surface border-r border-forge-border flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-forge-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-forge-accent/10 border border-forge-accent/30 flex items-center justify-center">
              <Shield size={18} className="text-forge-accent" />
            </div>
            <div>
              <div className="font-mono font-bold text-forge-text tracking-wider text-sm">PREPIQ</div>
              <div className="text-xs text-forge-muted font-mono">v1.0.0</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          <div className="text-xs font-mono text-forge-muted px-4 mb-3 uppercase tracking-widest">Platform</div>
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => clsx('sidebar-link', isActive && 'active')}
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}

          {['admin', 'superadmin'].includes(user?.role) && (
            <>
              <div className="text-xs font-mono text-forge-muted px-4 mt-6 mb-3 uppercase tracking-widest">Admin</div>
              <NavLink to="/admin" className={({ isActive }) => clsx('sidebar-link', isActive && 'active')}>
                <Settings size={16} />
                <span>Admin Panel</span>
              </NavLink>
            </>
          )}
        </nav>

        {/* User section */}
        <div className="p-4 border-t border-forge-border space-y-1">
          <NavLink to="/profile" className={({ isActive }) => clsx('sidebar-link', isActive && 'active')}>
            <User size={16} />
            <span className="truncate">{user?.full_name || user?.email}</span>
          </NavLink>
          <button onClick={handleLogout} className="sidebar-link w-full text-left text-forge-red hover:text-forge-red hover:bg-red-900/10">
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="min-h-full">
          <Outlet />
        </div>
      </main>
      <AICoach />
    </div>
  )
}
