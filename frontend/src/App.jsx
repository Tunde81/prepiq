import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useEffect } from 'react'
import useAuthStore from './store/authStore'

import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Learning from './pages/Learning'
import ModuleDetail from './pages/ModuleDetail'
import Simulations from './pages/Simulations'
import SimulationPlay from './pages/SimulationPlay'
import Assessment from './pages/Assessment'
import AssessmentResult from './pages/AssessmentResult'
import Profile from './pages/Profile'
import AdminPanel from './pages/AdminPanel'
import ComplianceTracker from './pages/ComplianceTracker'
import LearningPaths from './pages/LearningPaths'
import OrgHealth from './pages/OrgHealth'
import ImpactDashboard from './pages/ImpactDashboard'
import Layout from './components/Layout'
import CyberHealthIndex from './pages/CyberHealthIndex'
import CyberIncidentSimulator from './pages/CyberIncidentSimulator'
import PhishingSimulator from './pages/PhishingSimulator'
import PhishingTraining from './pages/PhishingTraining'
import LandingPage from './pages/LandingPage'

function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore(s => s.isAuthenticated)
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function AdminRoute({ children }) {
  const user = useAuthStore(s => s.user)
  if (!user) return <Navigate to="/login" replace />
  if (!['admin', 'superadmin'].includes(user.role)) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  const initAuth = useAuthStore(s => s.initAuth)
  useEffect(() => { initAuth() }, [])

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#0d1321', color: '#e2e8f0', border: '1px solid #1a2540' },
          success: { iconTheme: { primary: '#00ff88', secondary: '#0d1321' } },
          error: { iconTheme: { primary: '#ff4444', secondary: '#0d1321' } },
        }}
      />
      <Routes>
        <Route path="/impact" element={<ImpactDashboard />} />
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/phishing/training/:token" element={<PhishingTraining />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="learning" element={<Learning />} />
          <Route path="learning/:slug" element={<ModuleDetail />} />
          <Route path="simulations" element={<Simulations />} />
          <Route path="simulations/:id/play" element={<SimulationPlay />} />
          <Route path="assessment" element={<Assessment />} />
          <Route path="assessment/result/:id" element={<AssessmentResult />} />
          <Route path="profile" element={<Profile />} />
          <Route path="admin" element={<AdminRoute><AdminPanel /></AdminRoute>} />
          <Route path="compliance" element={<ComplianceTracker />} />
          <Route path="paths" element={<LearningPaths />} />
          <Route path="organisation" element={<OrgHealth />} />
          <Route path="health-index" element={<CyberHealthIndex />} />
          <Route path="simulator" element={<CyberIncidentSimulator />} />
          <Route path="phishing" element={<PhishingSimulator />} />
        </Route>
      </Routes>
    </>
  )
}
