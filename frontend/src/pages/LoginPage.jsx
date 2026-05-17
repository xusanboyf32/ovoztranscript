import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/auth'
import { ROLE_REDIRECT } from '../utils/constants'
import { Mic } from 'lucide-react'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setUser } = useAuthStore()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setError("Username va parolni kiriting")
      return
    }
    setLoading(true)
    setError('')
    try {
      const { data } = await authApi.login(username.trim(), password)
      setUser(data.user)
      navigate(ROLE_REDIRECT[data.user.role] || '/login')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (detail === "Username yoki parol noto'g'ri") {
        setError("Username yoki parol noto'g'ri")
      } else if (detail === "Foydalanuvchi bloklangan") {
        setError("Sizning hisobingiz bloklangan")
      } else {
        setError("Xato yuz berdi. Qayta urinib ko'ring")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100
                    flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center
                          w-16 h-16 bg-blue-600 rounded-2xl mb-4 shadow-lg">
            <Mic size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">VoiceTask AI</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Ovozli topshiriqlar boshqaruv tizimi
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Tizimga kirish
          </h2>

          <form onSubmit={handleLogin} className="space-y-4">

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username kiriting"
                autoComplete="username"
                className="w-full border border-gray-300 text-gray-900
                           rounded-xl px-4 py-2.5 text-sm outline-none
                           focus:border-blue-500 focus:ring-2 focus:ring-blue-100
                           placeholder:text-gray-400 transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Parol
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                className="w-full border border-gray-300 text-gray-900
                           rounded-xl px-4 py-2.5 text-sm outline-none
                           focus:border-blue-500 focus:ring-2 focus:ring-blue-100
                           placeholder:text-gray-400 transition"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400
                         disabled:cursor-not-allowed text-white font-medium
                         rounded-xl py-2.5 text-sm transition mt-2
                         flex items-center justify-center gap-2 shadow-sm"
            >
              {loading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10"
                      stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Kirilmoqda...
                </>
              ) : 'Kirish'}
            </button>

          </form>
        </div>

        <p className="text-center text-gray-400 text-xs mt-6">
          © 2025 VoiceTask AI
        </p>

      </div>
    </div>
  )
}
