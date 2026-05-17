import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

import LoginPage from '../pages/LoginPage'
import BossPage from '../pages/BossPage'
import SecretaryPage from '../pages/SecretaryPage'
import EmployeePage from '../pages/EmployeePage'
import NotFound from '../pages/NotFound'

function PrivateRoute({ children, allowedRoles }) {
  const { user } = useAuthStore()
  if (!user) return <Navigate to="/login" replace />
  if (!allowedRoles.includes(user.role)) return <Navigate to="/login" replace />
  return children
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/boss"
          element={
            <PrivateRoute allowedRoles={['boss']}>
              <BossPage />
            </PrivateRoute>
          }
        />

        <Route
          path="/secretary"
          element={
            <PrivateRoute allowedRoles={['secretary']}>
              <SecretaryPage />
            </PrivateRoute>
          }
        />

        <Route
          path="/my-tasks"
          element={
            <PrivateRoute allowedRoles={['employee']}>
              <EmployeePage />
            </PrivateRoute>
          }
        />

        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
