import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { bossApi } from '../api/boss'
import Sidebar from '../components/Sidebar'
import Badge from '../components/Badge'
import Spinner from '../components/Spinner'
import { formatDate, formatDeadline, deadlineColor } from '../utils/date'
import {
  PRIORITY_LABELS, PRIORITY_COLORS,
  STATUS_LABELS, STATUS_COLORS,
  TASK_TYPE_LABELS, TASK_TYPE_COLORS,
} from '../utils/constants'
import {
  Mic, MicOff, Clock, FileText,
  Users, X, ChevronRight, Play,
} from 'lucide-react'

const NAV_SECTIONS = [
  { label: 'Bosh sahifa', value: 'home', icon: <FileText size={16} /> },
  { label: 'Audiolar', value: 'audios', icon: <Play size={16} /> },
  { label: 'Topshiriqlar', value: 'tasks', icon: <FileText size={16} /> },
  { label: 'Xodimlar', value: 'employees', icon: <Users size={16} /> },
]

function AttachmentView({ att }) {
  if (!att.file_url) return null
  if (att.file_type === 'image') {
    return (
      <div className="rounded-xl overflow-hidden border border-gray-200">
        <img
          src={att.file_url}
          alt={att.file_name}
          className="w-full object-cover max-h-48"
          onError={(e) => { e.target.style.display = 'none' }}
        />
        <div className="px-3 py-2 bg-gray-50 flex items-center justify-between">
          <span className="text-gray-600 text-xs truncate">{att.file_name}</span>
          <a href={att.file_url} target="_blank" rel="noopener noreferrer"
            className="text-blue-500 text-xs hover:underline shrink-0 ml-2">
            To'liq ko'rish
          </a>
        </div>
      </div>
    )
  }
  if (att.file_type === 'video') {
    return (
      <div className="rounded-xl overflow-hidden border border-gray-200">
        <video src={att.file_url} controls className="w-full max-h-40" />
        <div className="px-3 py-2 bg-gray-50">
          <span className="text-gray-600 text-xs">{att.file_name}</span>
        </div>
      </div>
    )
  }
  if (att.file_type === 'audio') {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-3">
        <p className="text-gray-600 text-xs mb-2">{att.file_name}</p>
        <audio src={att.file_url} controls className="w-full" />
      </div>
    )
  }
  return (
    <a href={att.file_url} target="_blank" rel="noopener noreferrer"
      className="flex items-center gap-3 bg-gray-50 border border-gray-200
                 rounded-xl px-4 py-3 hover:bg-blue-50 transition">
      <div className="w-9 h-9 bg-blue-100 rounded-lg flex items-center justify-center shrink-0">
        <span className="text-blue-600 text-xs font-bold">
          {att.file_name?.split('.').pop()?.toUpperCase().slice(0, 3)}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-gray-700 text-sm font-medium truncate">{att.file_name}</p>
        {att.file_size && (
          <p className="text-gray-400 text-xs">{(att.file_size / 1024).toFixed(1)} KB</p>
        )}
      </div>
      <span className="text-blue-500 text-xs shrink-0">Ko'rish</span>
    </a>
  )
}

function BossTaskCard({ task }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-gray-100 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <Badge label={TASK_TYPE_LABELS[task.task_type]} className={TASK_TYPE_COLORS[task.task_type]} />
            <Badge label={PRIORITY_LABELS[task.priority]} className={PRIORITY_COLORS[task.priority]} />
            <Badge label={STATUS_LABELS[task.status]} className={STATUS_COLORS[task.status]} />
          </div>
          <p className="text-gray-900 text-sm font-medium truncate">{task.title}</p>
          <div className="flex items-center gap-3 mt-1 text-xs flex-wrap">
            {task.assignee ? (
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-blue-600 text-xs font-bold">
                    {task.assignee.full_name?.[0]?.toUpperCase()}
                  </span>
                </div>
                <span className="text-gray-600">{task.assignee.full_name}</span>
              </div>
            ) : (
              <span className="text-red-400">⚠️ Ishchi yo'q</span>
            )}
            {task.deadline && (
              <span className={`font-medium ${deadlineColor(task.deadline)}`}>
                📅 {formatDeadline(task.deadline)}
              </span>
            )}
            {task.amount && (
              <span className="text-gray-500">💰 {task.amount} {task.currency}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          {task.report && (
            <Badge label={STATUS_LABELS[task.report.status]} className={STATUS_COLORS[task.report.status]} />
          )}
          <ChevronRight
            size={16}
            className={`text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}
          />
        </div>
      </button>

      {open && (
        <div className="px-5 pb-4 space-y-3 bg-gray-50 border-t border-gray-100">
          {task.description && (
            <div className="pt-3">
              <p className="text-gray-500 text-xs font-medium mb-1">Tavsif:</p>
              <p className="text-gray-700 text-sm">{task.description}</p>
            </div>
          )}
          {task.report ? (
            <div className="bg-white rounded-xl p-4 border border-gray-200 space-y-3">
              {task.report.employee && (
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-600 text-xs font-bold">
                      {task.report.employee.full_name?.[0]?.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-900 text-sm font-medium">{task.report.employee.full_name}</p>
                    <p className="text-gray-400 text-xs">{formatDate(task.report.submitted_at)}</p>
                  </div>
                  <Badge label={STATUS_LABELS[task.report.status]} className={STATUS_COLORS[task.report.status]} />
                </div>
              )}
              {task.report.report_text && (
                <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                  <p className="text-gray-500 text-xs font-medium mb-1">Ariza matni:</p>
                  <p className="text-gray-700 text-sm">{task.report.report_text}</p>
                </div>
              )}
              {task.report.rejection_note && (
                <div className="bg-red-50 rounded-lg p-3 border border-red-100">
                  <p className="text-red-500 text-xs font-medium mb-1">Qaytarish sababi:</p>
                  <p className="text-red-600 text-sm">{task.report.rejection_note}</p>
                </div>
              )}
              {task.report.attachments?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-gray-500 text-xs font-medium">
                    Yuborilgan fayllar ({task.report.attachments.length}):
                  </p>
                  {task.report.attachments.map((att) => (
                    <AttachmentView key={att.id} att={att} />
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-xl p-4 border border-gray-200">
              <p className="text-gray-400 text-sm">Hisobot hali yuborilmagan</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function BossPage() {
  const { user } = useAuthStore()

  const [section, setSection] = useState('home')
  const [recording, setRecording] = useState(false)
  const [timer, setTimer] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [processingStatus, setProcessingStatus] = useState('')
  const [uploadedMeetingId, setUploadedMeetingId] = useState(null)
  const [selectedMeeting, setSelectedMeeting] = useState(null)
  const [meetingTitle, setMeetingTitle] = useState('')

  const mediaRecorder = useRef(null)
  const audioChunks = useRef([])
  const timerRef = useRef(null)
  const pollingRef = useRef(null)

  const { data: stats } = useQuery({
    queryKey: ['boss-stats'],
    queryFn: () => bossApi.getStats().then(r => r.data),
    refetchInterval: 30000,
  })

  const { data: overview } = useQuery({
    queryKey: ['boss-overview'],
    queryFn: () => bossApi.getOverview().then(r => r.data),
    refetchInterval: 30000,
  })

  const { data: meetings, refetch: refetchMeetings } = useQuery({
    queryKey: ['boss-meetings'],
    queryFn: () => bossApi.getMeetings().then(r => r.data),
  })

  const { data: meetingDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['boss-meeting-detail', selectedMeeting?.id],
    queryFn: () => bossApi.getMeeting(selectedMeeting.id).then(r => r.data),
    enabled: !!selectedMeeting,
  })

  useEffect(() => {
    if (recording) {
      timerRef.current = setInterval(() => setTimer(t => t + 1), 1000)
    } else {
      clearInterval(timerRef.current)
      setTimer(0)
    }
    return () => clearInterval(timerRef.current)
  }, [recording])

  useEffect(() => {
    if (!uploadedMeetingId) return
    pollingRef.current = setInterval(async () => {
      try {
        const { data } = await bossApi.getMeetingStatus(uploadedMeetingId)
        if (data.status === 'ready') {
          setProcessingStatus('✅ Transcript tayyor!')
          clearInterval(pollingRef.current)
          refetchMeetings()
          setTimeout(() => {
            setUploadedMeetingId(null)
            setProcessingStatus('')
          }, 3000)
        } else if (data.status === 'failed') {
          setProcessingStatus('❌ Xato yuz berdi')
          clearInterval(pollingRef.current)
        }
      } catch {}
    }, 3000)
    return () => clearInterval(pollingRef.current)
  }, [uploadedMeetingId])

  const formatTimer = (s) => {
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const sec = s % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '00')}:${String(sec).padStart(2, '0')}`
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      audioChunks.current = []
      mr.ondataavailable = e => audioChunks.current.push(e.data)
      mr.onstop = async () => {
        const blob = new Blob(audioChunks.current, { type: 'audio/webm' })
        const fd = new FormData()
        fd.append('audio', blob, 'recording.webm')
        fd.append('title', meetingTitle.trim() || `Majlis — ${new Date().toLocaleString('uz')}`)
        setUploading(true)
        setProcessingStatus('Yuklanmoqda...')
        try {
          const { data } = await bossApi.uploadAudio(fd)
          setUploadedMeetingId(data.meeting_id)
          setProcessingStatus('Qayta ishlanmoqda...')
          setMeetingTitle('')
          refetchMeetings()
        } catch {
          setProcessingStatus('❌ Yuklashda xato')
        } finally {
          setUploading(false)
        }
        stream.getTracks().forEach(t => t.stop())
      }
      mr.start()
      mediaRecorder.current = mr
      setRecording(true)
    } catch {
      alert('Mikrofonga ruxsat berilmadi')
    }
  }

  const stopRecording = () => {
    mediaRecorder.current?.stop()
    setRecording(false)
  }

  const taskStats = stats?.task_stats || {}
  const audioMeetings = meetings?.items?.filter(m => m.audio_duration && m.audio_duration !== '00:00') || []
  const taskMeetings = meetings?.items?.filter(m => m.task_count > 0) || []

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="flex">
        <Sidebar />
        <div className="w-56 min-h-screen bg-white border-r border-gray-200 flex flex-col">
          <div className="px-4 py-4 border-b border-gray-100">
            <h2 className="text-gray-700 font-semibold text-sm">Bo'limlar</h2>
          </div>
          <nav className="flex-1 px-3 py-3 space-y-1">
            {NAV_SECTIONS.map((s) => (
              <button
                key={s.value}
                onClick={() => setSection(s.value)}
                className={`w-full flex items-center gap-2.5 px-3 py-2.5
                           rounded-xl text-sm font-medium transition
                           ${section === s.value
                             ? 'bg-blue-50 text-blue-600'
                             : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                           }`}
              >
                <span className={section === s.value ? 'text-blue-500' : 'text-gray-400'}>
                  {s.icon}
                </span>
                {s.label}
              </button>
            ))}
          </nav>
          <div className="px-4 py-4 border-t border-gray-100 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-xs">Jami topshiriqlar</span>
              <span className="text-blue-600 text-xs font-bold">{taskStats.total || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-xs">Bajarilgan</span>
              <span className="text-green-600 text-xs font-bold">{taskStats.approved || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-xs">Muddati o'tgan</span>
              <span className="text-red-500 text-xs font-bold">{taskStats.overdue || 0}</span>
            </div>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-auto">

        {section === 'home' && (
          <div className="p-6 max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">Bosh sahifa</h1>
                <p className="text-gray-500 text-sm mt-0.5">Salom, {user?.full_name}!</p>
              </div>
              <div className="text-sm text-gray-400">
                {new Date().toLocaleDateString('uz-UZ', { day: 'numeric', month: 'long', year: 'numeric' })}
              </div>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'Jami topshiriqlar', value: taskStats.total || 0, color: 'text-blue-600' },
                { label: 'Bajarilgan', value: taskStats.approved || 0, color: 'text-green-600' },
                { label: 'Jarayonda', value: taskStats.in_progress || 0, color: 'text-purple-600' },
                { label: "Muddati o'tgan", value: taskStats.overdue || 0, color: 'text-red-600' },
              ].map((stat) => (
                <div key={stat.label} className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm">
                  <p className="text-gray-500 text-xs font-medium">{stat.label}</p>
                  <p className={`text-3xl font-bold mt-2 ${stat.color}`}>{stat.value}</p>
                </div>
              ))}
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-5">
                <Mic size={18} className="text-blue-600" />
                <h2 className="text-gray-900 font-semibold text-sm">Ovoz yozish</h2>
              </div>
              {!recording && (
                <div className="mb-4">
                  <input
                    value={meetingTitle}
                    onChange={e => setMeetingTitle(e.target.value)}
                    placeholder="Majlis nomi (ixtiyoriy)"
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5
                               text-sm text-gray-900 outline-none focus:border-blue-500
                               focus:ring-2 focus:ring-blue-100 bg-gray-50"
                  />
                </div>
              )}
              <div className="flex flex-col items-center gap-4">
                <button
                  onClick={recording ? stopRecording : startRecording}
                  disabled={uploading}
                  className={`w-20 h-20 rounded-full flex items-center justify-center
                             shadow-lg transition-all duration-200 disabled:opacity-50
                             ${recording
                               ? 'bg-red-500 hover:bg-red-600 ring-4 ring-red-100'
                               : 'bg-blue-600 hover:bg-blue-700 ring-4 ring-blue-100'
                             }`}
                >
                  {recording ? <MicOff size={30} className="text-white" /> : <Mic size={30} className="text-white" />}
                </button>
                {recording && (
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                    <span className="text-red-500 font-mono font-semibold text-lg">{formatTimer(timer)}</span>
                  </div>
                )}
                {processingStatus && (
                  <div className="flex items-center gap-2 text-gray-600 text-sm">
                    {processingStatus.includes('ishlanmoqda') && <Spinner size="sm" />}
                    <span>{processingStatus}</span>
                  </div>
                )}
                <p className="text-gray-400 text-xs text-center">
                  {recording ? "To'xtatish uchun bosing" : 'Yozishni boshlash uchun bosing'}
                </p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
                <FileText size={16} className="text-blue-600" />
                <h2 className="text-gray-900 font-semibold text-sm">So'nggi majlislar</h2>
              </div>
              <div className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
                {!meetings?.items?.length && (
                  <div className="px-5 py-8 text-center text-gray-400 text-sm">Majlislar yo'q</div>
                )}
                {meetings?.items?.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setSelectedMeeting(m)}
                    className="w-full text-left px-5 py-3.5 flex items-center justify-between hover:bg-gray-50 transition"
                  >
                    <div>
                      <p className="text-gray-900 text-sm font-medium">{m.title}</p>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <Clock size={11} className="text-gray-400" />
                        <p className="text-gray-400 text-xs">{formatDate(m.meeting_date)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-xs">{m.task_count || 0} ta</span>
                      <Badge label={STATUS_LABELS[m.status] || m.status} className={STATUS_COLORS[m.status]} />
                      <ChevronRight size={14} className="text-gray-300" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {section === 'audios' && (
          <div className="p-6 max-w-4xl mx-auto space-y-5">
            <h1 className="text-xl font-bold text-gray-900">Yozilgan audiolar</h1>
            {!audioMeetings.length && (
              <div className="flex flex-col items-center justify-center py-16">
                <Play size={40} className="text-gray-300 mb-3" />
                <p className="text-gray-500 font-medium">Audio yozuvlar yo'q</p>
              </div>
            )}
            <div className="space-y-4">
              {audioMeetings.map((m) => (
                <AudioMeetingCard key={m.id} meeting={m} />
              ))}
            </div>
          </div>
        )}

        {section === 'tasks' && (
          <div className="p-6 max-w-4xl mx-auto space-y-5">
            <h1 className="text-xl font-bold text-gray-900">Topshiriqlar</h1>
            {!taskMeetings.length && (
              <div className="flex flex-col items-center justify-center py-16">
                <FileText size={40} className="text-gray-300 mb-3" />
                <p className="text-gray-500 font-medium">Topshiriqlar yo'q</p>
              </div>
            )}
            {taskMeetings.map((m) => (
              <BossMeetingTasksRow
                key={m.id}
                meetingId={m.id}
                meetingTitle={m.title}
                meetingDate={m.meeting_date}
                meetingStatus={m.status}
              />
            ))}
          </div>
        )}

        {section === 'employees' && (
          <div className="p-6 max-w-4xl mx-auto space-y-5">
            <h1 className="text-xl font-bold text-gray-900">Xodimlar holati</h1>
            {!overview?.employees?.length && (
              <div className="flex flex-col items-center justify-center py-16">
                <Users size={40} className="text-gray-300 mb-3" />
                <p className="text-gray-500 font-medium">Xodimlar yo'q</p>
              </div>
            )}
            <div className="space-y-4">
              {overview?.employees?.map((emp) => (
                <div key={emp.id} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-blue-600 font-bold text-sm">
                          {emp.full_name?.[0]?.toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="text-gray-900 text-sm font-semibold">{emp.full_name}</p>
                        <p className="text-gray-400 text-xs">{emp.position || '—'}</p>
                      </div>
                    </div>
                    <span className="text-gray-400 text-xs bg-gray-100 px-3 py-1 rounded-full">
                      {emp.active_tasks || 0} ta faol
                    </span>
                  </div>
                  {emp.tasks?.length > 0 && (
                    <div className="space-y-2">
                      {emp.tasks.map((task) => (
                        <EmployeeTaskCard key={task.id} task={task} />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {selectedMeeting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setSelectedMeeting(null)} />
          <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl
                          border border-gray-200 max-h-[85vh] flex flex-col overflow-hidden">
            <div className="flex items-start justify-between px-6 py-5 border-b border-gray-100">
              <div>
                <h2 className="text-gray-900 font-bold text-base">{selectedMeeting.title || 'Nomsiz majlis'}</h2>
                <p className="text-gray-400 text-sm mt-0.5">{formatDate(selectedMeeting.meeting_date)}</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge label={STATUS_LABELS[selectedMeeting.status] || selectedMeeting.status} className={STATUS_COLORS[selectedMeeting.status]} />
                <button onClick={() => setSelectedMeeting(null)} className="text-gray-400 hover:text-gray-600 transition">
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
              {detailLoading ? (
                <div className="flex justify-center py-10"><Spinner size="lg" /></div>
              ) : (
                <>
                  <div>
                    <h3 className="text-gray-700 font-semibold text-sm mb-2">Transcript</h3>
                    <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                      <p className="text-gray-600 text-sm leading-relaxed">
                        {meetingDetail?.edited_transcript || meetingDetail?.transcript || "Transcript yo'q"}
                      </p>
                    </div>
                  </div>
                  {meetingDetail?.tasks?.length > 0 && (
                    <div>
                      <h3 className="text-gray-700 font-semibold text-sm mb-2">
                        Topshiriqlar ({meetingDetail.tasks.length})
                      </h3>
                      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
                        {meetingDetail.tasks.map((task) => (
                          <BossTaskCard key={task.id} task={task} />
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function AudioMeetingCard({ meeting }) {
  const { data, isLoading } = useQuery({
    queryKey: ['boss-meeting-detail', meeting.id],
    queryFn: () => bossApi.getMeeting(meeting.id).then(r => r.data),
  })

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-gray-900 font-semibold text-sm">{meeting.title || 'Nomsiz majlis'}</p>
          <p className="text-gray-400 text-xs mt-0.5">{formatDate(meeting.meeting_date)}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-xs">{meeting.audio_duration}s</span>
          <Badge label={STATUS_LABELS[meeting.status] || meeting.status} className={STATUS_COLORS[meeting.status]} />
        </div>
      </div>
      {isLoading ? (
        <div className="flex items-center gap-2 py-2">
          <Spinner size="sm" />
          <span className="text-gray-400 text-xs">Yuklanmoqda...</span>
        </div>
      ) : (
        <>
          {data?.audio_file_path && (
            <div className="mb-3">
              <audio
                src={`http://localhost:8000/${data.audio_file_path.replace(/\\/g, '/')}`}

                controls
                className="w-full"
              />
            </div>
          )}
          {(data?.edited_transcript || data?.transcript) && (
            <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
              <p className="text-gray-500 text-xs font-medium mb-2">Transcript:</p>
              <p className="text-gray-700 text-sm leading-relaxed">
                {data.edited_transcript || data.transcript}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function BossMeetingTasksRow({ meetingId, meetingTitle, meetingDate, meetingStatus }) {
  const { data, isLoading } = useQuery({
    queryKey: ['boss-meeting-detail', meetingId],
    queryFn: () => bossApi.getMeeting(meetingId).then(r => r.data),
  })

  if (isLoading) return (
    <div className="flex items-center gap-2 py-2">
      <Spinner size="sm" />
      <span className="text-gray-400 text-xs">Yuklanmoqda...</span>
    </div>
  )
  if (!data?.tasks?.length) return null

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-gray-700 font-semibold text-sm">{meetingTitle || 'Nomsiz majlis'}</h3>
        <span className="text-gray-400 text-xs">{formatDate(meetingDate)}</span>
        <Badge label={STATUS_LABELS[meetingStatus] || meetingStatus} className={STATUS_COLORS[meetingStatus]} />
      </div>
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
        {data.tasks.map((task) => (
          <BossTaskCard key={task.id} task={task} />
        ))}
      </div>
    </div>
  )
}

function EmployeeTaskCard({ task }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="bg-gray-50 rounded-xl border border-gray-200">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-3 flex items-center justify-between"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <Badge label={STATUS_LABELS[task.status]} className={STATUS_COLORS[task.status]} />
            <Badge label={PRIORITY_LABELS[task.priority]} className={PRIORITY_COLORS[task.priority]} />
          </div>
          <p className="text-gray-800 text-sm font-medium truncate">{task.title}</p>
          {task.deadline && (
            <span className={`text-xs font-medium ${deadlineColor(task.deadline)}`}>
              📅 {formatDeadline(task.deadline)}
            </span>
          )}
        </div>
        <ChevronRight
          size={16}
          className={`text-gray-400 shrink-0 ml-2 transition-transform ${open ? 'rotate-90' : ''}`}
        />
      </button>

      {open && task.report && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-200 space-y-3">
          <div className="flex items-center justify-between pt-3">
            <span className="text-gray-500 text-xs font-medium">Hisobot holati</span>
            <Badge label={STATUS_LABELS[task.report.status]} className={STATUS_COLORS[task.report.status]} />
          </div>
          {task.report.report_text && (
            <div className="bg-white rounded-xl p-3 border border-gray-200">
              <p className="text-gray-500 text-xs font-medium mb-1">Hisobot matni:</p>
              <p className="text-gray-700 text-sm">{task.report.report_text}</p>
            </div>
          )}
          {task.report.attachments?.length > 0 && (
            <div className="space-y-2">
              <p className="text-gray-500 text-xs font-medium">
                Fayllar ({task.report.attachments.length}):
              </p>
              {task.report.attachments.map((att) => (
                <AttachmentView key={att.id} att={att} />
              ))}
            </div>
          )}
        </div>
      )}
      {open && !task.report && (
        <div className="px-4 pb-4 pt-3 border-t border-gray-200">
          <p className="text-gray-400 text-xs">Hisobot hali yuborilmagan</p>
        </div>
      )}
    </div>
  )
}
