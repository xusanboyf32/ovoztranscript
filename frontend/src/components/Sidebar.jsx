import { useState, useRef } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/auth'
import { profileApi } from '../api/profile'
import {
  LayoutDashboard, FileText, ClipboardList,
  LogOut, Mic, Phone, Building2, Briefcase,
  X, Camera, Edit2, Save, Mail, Calendar,
} from 'lucide-react'
import Spinner from './Spinner'

const ROLE_LINKS = {
  boss: [
    { to: '/boss', icon: <LayoutDashboard size={18} />, label: 'Bosh sahifa' },
  ],
  secretary: [
    { to: '/secretary', icon: <FileText size={18} />, label: 'Majlislar' },
  ],
  employee: [
    { to: '/my-tasks', icon: <ClipboardList size={18} />, label: 'Topshiriqlarim' },
  ],
}

const ROLE_LABELS = {
  boss:      'Rahbar',
  secretary: 'Kotiba',
  employee:  'Xodim',
  admin:     'Admin',
}

const ROLE_BG = {
  boss:      'bg-blue-600',
  secretary: 'bg-purple-600',
  employee:  'bg-green-600',
  admin:     'bg-red-600',
}

const ROLE_BADGE = {
  boss:      'bg-blue-600 text-white',
  secretary: 'bg-purple-600 text-white',
  employee:  'bg-green-600 text-white',
  admin:     'bg-red-600 text-white',
}

const getAvatarUrl = (url) => {
  if (!url) return null
  if (url.startsWith('http')) {
    return url.replace('http://localhost:8000', '')
  }
  return url
}

export default function Sidebar() {
  const { user, setUser, logout } = useAuthStore()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const avatarRef = useRef(null)

  const [profileOpen, setProfileOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({})
  const [avatarPreview, setAvatarPreview] = useState(null)

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => profileApi.getProfile().then(r => r.data),
    enabled: profileOpen,
  })

  const updateMutation = useMutation({
    mutationFn: (data) => profileApi.updateProfile(data),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      setUser({ ...user, ...res.data })
      setEditing(false)
    },
  })

  const avatarMutation = useMutation({
    mutationFn: (fd) => profileApi.uploadAvatar(fd),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      setAvatarPreview(null)
    },
  })

  const handleLogout = async () => {
    try { await authApi.logout() } catch {}
    logout()
    navigate('/login')
  }

  const openProfile = () => {
    setProfileOpen(true)
    setEditing(false)
    setForm({})
  }

  const startEdit = () => {
    setForm({
      first_name:  profile?.first_name || '',
      last_name:   profile?.last_name || '',
      email:       profile?.email || '',
      phone:       profile?.phone || '',
      birth_date:  profile?.birth_date || '',
      position:    profile?.position || '',
      department:  profile?.department || '',
    })
    setEditing(true)
  }

  const handleAvatarChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const preview = URL.createObjectURL(file)
    setAvatarPreview(preview)
    const fd = new FormData()
    fd.append('file', file)
    avatarMutation.mutate(fd)
  }

  const links = ROLE_LINKS[user?.role] || []
  const avatarBg = ROLE_BG[user?.role] || 'bg-blue-600'
  const initial = user?.full_name?.[0]?.toUpperCase()
  const avatarUrl = avatarPreview || getAvatarUrl(profile?.avatar_url)

  return (
    <>
      <aside className="w-64 min-h-screen bg-white border-r border-gray-200
                        flex flex-col shadow-sm shrink-0">

        {/* Logo */}
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center
                            justify-center shrink-0">
              <Mic size={18} className="text-white" />
            </div>
            <div>
              <p className="text-gray-900 font-bold text-sm">VoiceTask AI</p>
              <p className="text-gray-400 text-xs">Boshqaruv tizimi</p>
            </div>
          </div>
        </div>

        {/* Profile button */}
        <button
          onClick={openProfile}
          className="mx-3 mt-4 mb-1 flex items-center gap-3 p-3 rounded-xl
                     hover:bg-gray-50 transition border border-gray-200
                     group text-left"
        >
          <div className={`w-10 h-10 rounded-full flex items-center justify-center
                          shrink-0 overflow-hidden ${avatarBg}`}>
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt="avatar"
                className="w-full h-full object-cover"
                onError={(e) => { e.target.style.display = 'none' }}
              />
            ) : (
              <span className="text-white font-bold text-base">{initial}</span>
            )}
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="text-gray-900 text-sm font-semibold truncate">
              {user?.full_name}
            </p>
            <span className={`inline-flex items-center px-2 py-0.5 rounded-md
                             text-xs font-semibold mt-0.5 ${ROLE_BADGE[user?.role]}`}>
              {ROLE_LABELS[user?.role]}
            </span>
          </div>
          <Edit2 size={13} className="text-gray-300 group-hover:text-gray-500
                                      transition shrink-0" />
        </button>

        {/* Nav */}
        <nav className="flex-1 px-3 py-3 space-y-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm
                 font-medium transition
                 ${isActive
                   ? 'bg-blue-50 text-blue-600'
                   : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                 }`
              }
            >
              {link.icon}
              {link.label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-3 py-4 border-t border-gray-100">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 w-full rounded-xl
                       text-gray-500 hover:bg-red-50 hover:text-red-600
                       text-sm font-medium transition"
          >
            <LogOut size={18} />
            Chiqish
          </button>
        </div>

      </aside>

      {/* Profile Modal */}
      {profileOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => { setProfileOpen(false); setEditing(false) }}
          />

          <div className="relative w-full max-w-md bg-white rounded-2xl
                          shadow-2xl border border-gray-200 overflow-hidden">

            {/* Header bg */}
            <div className={`relative px-6 pt-8 pb-16 text-center ${avatarBg}`}>
              <button
                onClick={() => { setProfileOpen(false); setEditing(false) }}
                className="absolute top-4 right-4 text-white/70 hover:text-white transition"
              >
                <X size={20} />
              </button>

              {/* Avatar */}
              <div className="relative inline-block">
                <div className="w-24 h-24 rounded-full bg-white/20 border-4
                                border-white/40 mx-auto overflow-hidden
                                flex items-center justify-center">
                  {avatarUrl ? (
                    <img
                      src={avatarUrl}
                      alt="avatar"
                      className="w-full h-full object-cover"
                      onError={(e) => { e.target.style.display = 'none' }}
                    />
                  ) : (
                    <span className="text-white font-bold text-4xl">{initial}</span>
                  )}
                </div>

                {/* Camera */}
                <button
                  onClick={() => avatarRef.current?.click()}
                  className="absolute bottom-0 right-0 w-8 h-8 bg-white rounded-full
                             flex items-center justify-center shadow-lg border
                             border-gray-200 hover:bg-gray-50 transition"
                >
                  {avatarMutation.isPending
                    ? <Spinner size="sm" />
                    : <Camera size={14} className="text-gray-600" />
                  }
                </button>
                <input
                  ref={avatarRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handleAvatarChange}
                />
              </div>

              <h2 className="text-white font-bold text-lg mt-3">{user?.full_name}</h2>
              <p className="text-white/70 text-sm">@{user?.username}</p>
            </div>

            {/* Role badge */}
            <div className="flex justify-center -mt-5 mb-2 relative z-10">
              <span className={`px-4 py-1.5 rounded-full text-sm font-bold
                               shadow-md ${ROLE_BADGE[user?.role]}`}>
                {ROLE_LABELS[user?.role]}
              </span>
            </div>

            {/* Content */}
            <div className="px-6 py-4 max-h-72 overflow-y-auto">
              {profileLoading ? (
                <div className="flex justify-center py-8">
                  <Spinner size="lg" />
                </div>
              ) : editing ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-gray-500 font-medium mb-1 block">Ism</label>
                      <input
                        value={form.first_name}
                        onChange={e => setForm({ ...form, first_name: e.target.value })}
                        className="w-full border border-gray-300 rounded-xl px-3 py-2
                                   text-sm outline-none focus:border-blue-500"
                        placeholder="Ism"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500 font-medium mb-1 block">Familiya</label>
                      <input
                        value={form.last_name}
                        onChange={e => setForm({ ...form, last_name: e.target.value })}
                        className="w-full border border-gray-300 rounded-xl px-3 py-2
                                   text-sm outline-none focus:border-blue-500"
                        placeholder="Familiya"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 font-medium mb-1 block">Email</label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={e => setForm({ ...form, email: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2
                                 text-sm outline-none focus:border-blue-500"
                      placeholder="email@example.com"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 font-medium mb-1 block">Telefon</label>
                    <input
                      value={form.phone}
                      onChange={e => setForm({ ...form, phone: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2
                                 text-sm outline-none focus:border-blue-500"
                      placeholder="+998901234567"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 font-medium mb-1 block">
                      Tug'ilgan sana
                    </label>
                    <input
                      type="date"
                      value={form.birth_date}
                      onChange={e => setForm({ ...form, birth_date: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2
                                 text-sm outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 font-medium mb-1 block">Lavozim</label>
                    <input
                      value={form.position}
                      onChange={e => setForm({ ...form, position: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2
                                 text-sm outline-none focus:border-blue-500"
                      placeholder="Lavozim"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 font-medium mb-1 block">Bo'lim</label>
                    <input
                      value={form.department}
                      onChange={e => setForm({ ...form, department: e.target.value })}
                      className="w-full border border-gray-300 rounded-xl px-3 py-2
                                 text-sm outline-none focus:border-blue-500"
                      placeholder="Bo'lim nomi"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {[
                    {
                      icon: <Briefcase size={15} className="text-blue-600" />,
                      bg: 'bg-blue-50',
                      label: 'Lavozim',
                      value: profile?.position,
                    },
                    {
                      icon: <Building2 size={15} className="text-purple-600" />,
                      bg: 'bg-purple-50',
                      label: "Bo'lim",
                      value: profile?.department,
                    },
                    {
                      icon: <Mail size={15} className="text-green-600" />,
                      bg: 'bg-green-50',
                      label: 'Email',
                      value: profile?.email,
                    },
                    {
                      icon: <Phone size={15} className="text-orange-600" />,
                      bg: 'bg-orange-50',
                      label: 'Telefon',
                      value: profile?.phone,
                    },
                    {
                      icon: <Calendar size={15} className="text-red-600" />,
                      bg: 'bg-red-50',
                      label: "Tug'ilgan sana",
                      value: profile?.birth_date,
                    },
                  ].filter(item => item.value).map((item) => (
                    <div key={item.label} className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-xl flex items-center
                                      justify-center shrink-0 ${item.bg}`}>
                        {item.icon}
                      </div>
                      <div>
                        <p className="text-gray-400 text-xs">{item.label}</p>
                        <p className="text-gray-900 text-sm font-medium">{item.value}</p>
                      </div>
                    </div>
                  ))}

                  {!profile?.position && !profile?.email &&
                   !profile?.phone && !profile?.department && (
                    <p className="text-gray-400 text-sm text-center py-4">
                      Ma'lumot yo'q — tahrirlash uchun bosing
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-gray-100 flex gap-3">
              {editing ? (
                <>
                  <button
                    onClick={() => setEditing(false)}
                    className="flex-1 py-2.5 bg-gray-100 text-gray-700 text-sm
                               rounded-xl hover:bg-gray-200 transition font-medium"
                  >
                    Bekor
                  </button>
                  <button
                    onClick={() => updateMutation.mutate(form)}
                    disabled={updateMutation.isPending}
                    className="flex-1 py-2.5 bg-blue-600 text-white text-sm
                               rounded-xl hover:bg-blue-700 transition font-medium
                               disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {updateMutation.isPending ? <Spinner size="sm" /> : <Save size={15} />}
                    Saqlash
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={startEdit}
                    className="flex-1 py-2.5 bg-blue-50 text-blue-600 text-sm
                               rounded-xl hover:bg-blue-100 transition font-medium
                               flex items-center justify-center gap-2"
                  >
                    <Edit2 size={15} />
                    Tahrirlash
                  </button>
                  <button
                    onClick={handleLogout}
                    className="flex-1 py-2.5 bg-red-50 text-red-600 text-sm
                               rounded-xl hover:bg-red-100 transition font-medium
                               flex items-center justify-center gap-2"
                  >
                    <LogOut size={15} />
                    Chiqish
                  </button>
                </>
              )}
            </div>

          </div>
        </div>
      )}
    </>
  )
}
