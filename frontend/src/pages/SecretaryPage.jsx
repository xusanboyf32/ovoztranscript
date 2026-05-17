import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { secretaryApi } from '../api/secretary'
import Sidebar from '../components/Sidebar'
import Badge from '../components/Badge'
import Spinner from '../components/Spinner'
import Modal from '../components/Modal'
import { formatDate, formatDeadline, deadlineColor } from '../utils/date'
import {
  TASK_TYPE_LABELS, TASK_TYPE_COLORS,
  PRIORITY_LABELS, PRIORITY_COLORS,
  STATUS_LABELS, STATUS_COLORS,
} from '../utils/constants'
import {
  ChevronRight, Edit2, Trash2, CheckCircle,
  RefreshCw, FileText, ClipboardList, Users, X, Bell,
} from 'lucide-react'

const NAV_SECTIONS = [
  { label: 'Majlislar', value: 'meetings', icon: <FileText size={16} /> },
  { label: 'Topshiriqlar', value: 'tasks', icon: <ClipboardList size={16} /> },
  { label: 'Yangi hisobotlar', value: 'new_reports', icon: <Bell size={16} /> },
  { label: 'Tasdiqlangan', value: 'approved_reports', icon: <CheckCircle size={16} /> },
]

function AttachmentItem({ att }) {
  if (att.file_type === 'image') {
    return (
      <div className="rounded-xl overflow-hidden border border-gray-200">
        <img src={att.file_url} alt={att.file_name}
          className="w-full object-cover max-h-48"
          onError={(e) => { e.target.style.display = 'none' }} />
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
                 rounded-xl px-4 py-3 hover:bg-blue-50 hover:border-blue-200 transition">
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

export default function SecretaryPage() {
  const qc = useQueryClient()

  const [section, setSection] = useState('meetings')
  const [selectedId, setSelectedId] = useState(null)
  const [editingTranscript, setEditingTranscript] = useState(false)
  const [transcriptText, setTranscriptText] = useState('')
  const [editingTaskId, setEditingTaskId] = useState(null)
  const [editData, setEditData] = useState({})
  const [confirmModal, setConfirmModal] = useState(false)
  const [rejectModal, setRejectModal] = useState(null)
  const [rejectNote, setRejectNote] = useState('')
  const [selectedReport, setSelectedReport] = useState(null)

  const { data: meetings } = useQuery({
    queryKey: ['sec-meetings'],
    queryFn: () => secretaryApi.getMeetings().then(r => r.data),
  })

  const { data: meeting, isLoading } = useQuery({
    queryKey: ['sec-meeting', selectedId],
    queryFn: () => secretaryApi.getMeeting(selectedId).then(r => r.data),
    enabled: !!selectedId && section === 'meetings',
  })

  const { data: employeesData } = useQuery({
    queryKey: ['sec-employees'],
    queryFn: () => secretaryApi.getEmployees().then(r => r.data),
  })
  const employees = employeesData?.employees || []

  const { data: reportDetail, isLoading: reportLoading } = useQuery({
    queryKey: ['sec-report', selectedReport?.taskId],
    queryFn: () => secretaryApi.getReport(selectedReport.taskId).then(r => r.data),
    enabled: !!selectedReport?.taskId,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['sec-meeting', selectedId] })
    qc.invalidateQueries({ queryKey: ['sec-meetings'] })
    qc.invalidateQueries({ queryKey: ['sec-meeting-reports'] })
  }

  const distributeMutation = useMutation({
    mutationFn: () => secretaryApi.distributeTasks(selectedId),
    onSuccess: invalidate,
  })

  const confirmMutation = useMutation({
    mutationFn: () => secretaryApi.confirmTasks(selectedId),
    onSuccess: () => { invalidate(); setConfirmModal(false) },
  })

  const updateTaskMutation = useMutation({
    mutationFn: ({ id, data }) => secretaryApi.updateTask(id, data),
    onSuccess: () => { invalidate(); setEditingTaskId(null); setEditData({}) },
    onError: (err) => { console.error('Task saqlashda xato:', err.response?.data) },
  })

  const deleteTaskMutation = useMutation({
    mutationFn: (id) => secretaryApi.deleteTask(id),
    onSuccess: invalidate,
  })

  const reviewMutation = useMutation({
    mutationFn: ({ taskId, action, note }) =>
      secretaryApi.reviewReport(taskId, action, note),
    onSuccess: () => {
      invalidate()
      setRejectModal(null)
      setRejectNote('')
      setSelectedReport(null)
      qc.invalidateQueries({ queryKey: ['sec-report'] })
    },
  })

  const saveTranscript = async () => {
    try {
      await secretaryApi.updateTranscript(selectedId, transcriptText)
      invalidate()
      setEditingTranscript(false)
    } catch (err) {
      console.error('Transcript saqlashda xato:', err)
    }
  }

  const selectMeeting = (id) => {
    setSelectedId(id)
    setEditingTranscript(false)
    setEditingTaskId(null)
    setEditData({})
  }

  const allTasks = meetings?.items?.flatMap(m =>
    (m.tasks || []).map(t => ({ ...t, meetingTitle: m.title }))
  ) || []
  const allReports = allTasks.filter(t => t.report)
  const canEdit = meeting && ['ready', 'distributed'].includes(meeting.status)
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
                             ? 'bg-purple-50 text-purple-600'
                             : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                           }`}
              >
                <span className={section === s.value ? 'text-purple-500' : 'text-gray-400'}>
                  {s.icon}
                </span>
                {s.label}
              </button>
            ))}
          </nav>
          <div className="px-4 py-4 border-t border-gray-100 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-xs">Jami majlislar</span>
              <span className="text-gray-600 text-xs font-bold">{meetings?.items?.length || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-xs">Hisobotlar</span>
              <span className="text-gray-600 text-xs font-bold">{allReports.length}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden h-screen">

        {/* ===== MAJLISLAR ===== */}
        {section === 'meetings' && (
          <>
            <div className="w-72 bg-white border-r border-gray-200 flex flex-col">
              <div className="px-4 py-4 border-b border-gray-100">
                <h2 className="text-gray-900 font-semibold text-sm">Majlislar</h2>
              </div>
              <div className="flex-1 overflow-y-auto">
                {!meetings?.items?.length && (
                  <div className="p-6 text-center text-gray-400 text-sm">Majlislar yo'q</div>
                )}
                {meetings?.items?.map((m) => (
                  <button key={m.id} onClick={() => selectMeeting(m.id)}
                    className={`w-full text-left px-4 py-3.5 border-b border-gray-100
                                hover:bg-gray-50 transition flex items-center justify-between
                                ${selectedId === m.id ? 'bg-blue-50 border-l-2 border-l-blue-600' : ''}`}>
                    <div className="overflow-hidden flex-1">
                      <p className="text-gray-900 text-sm font-medium truncate">
                        {m.title || 'Nomsiz majlis'}
                      </p>
                      <p className="text-gray-400 text-xs mt-0.5">{formatDate(m.meeting_date)}</p>
                      <div className="mt-1">
                        <Badge label={STATUS_LABELS[m.status] || m.status} className={STATUS_COLORS[m.status]} />
                      </div>
                    </div>
                    <ChevronRight size={14} className="text-gray-300 shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {!selectedId && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <FileText size={40} className="text-gray-300 mb-3" />
                  <p className="text-gray-500 font-medium">Majlisni tanlang</p>
                </div>
              )}
              {isLoading && <div className="flex justify-center pt-20"><Spinner size="lg" /></div>}
              {meeting && (
                <>
                  <div className="flex items-start justify-between">
                    <div>
                      <h1 className="text-gray-900 font-bold text-lg">{meeting.title || 'Nomsiz majlis'}</h1>
                      <p className="text-gray-400 text-sm mt-0.5">{formatDate(meeting.meeting_date)}</p>
                    </div>
                    <Badge label={STATUS_LABELS[meeting.status] || meeting.status} className={STATUS_COLORS[meeting.status]} />
                  </div>

                  <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-gray-900 font-semibold text-sm">Transcript</h3>
                      {canEdit && (
                        <div className="flex items-center gap-2">
                          {!editingTranscript ? (
                            <button onClick={() => { setTranscriptText(meeting.edited_transcript || meeting.transcript || ''); setEditingTranscript(true) }}
                              className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 px-3 py-1.5 bg-blue-50 rounded-lg transition">
                              <Edit2 size={12} /> Tahrirlash
                            </button>
                          ) : (
                            <div className="flex gap-2">
                              <button onClick={saveTranscript}
                                className="text-xs text-white bg-green-600 hover:bg-green-700 px-3 py-1.5 rounded-lg transition">
                                Saqlash
                              </button>
                              <button onClick={() => setEditingTranscript(false)}
                                className="text-xs text-gray-600 bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded-lg transition">
                                Bekor
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    {editingTranscript ? (
                      <textarea value={transcriptText} onChange={e => setTranscriptText(e.target.value)}
                        className="w-full border border-gray-300 text-gray-700 rounded-xl p-4 text-sm outline-none focus:border-blue-500 resize-none"
                        rows={6} />
                    ) : (
                      <p className="text-gray-600 text-sm leading-relaxed">
                        {meeting.edited_transcript || meeting.transcript || "Transcript yo'q"}
                      </p>
                    )}
                    {canEdit && (
                      <div className="flex gap-3 mt-4 pt-4 border-t border-gray-100">
                        <button onClick={() => distributeMutation.mutate()} disabled={distributeMutation.isPending}
                          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl transition disabled:opacity-50 shadow-sm">
                          {distributeMutation.isPending ? <Spinner size="sm" /> : <RefreshCw size={14} />}
                          {meeting.status === 'distributed' ? 'Qayta taqsimlash' : "Tasklarga bo'lish"}
                        </button>
                      </div>
                    )}
                  </div>

                  {meeting.tasks?.length > 0 && (
                    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
                      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                        <h3 className="text-gray-900 font-semibold text-sm">
                          Topshiriqlar ({meeting.tasks.length})
                        </h3>
                        {meeting.status === 'distributed' && (
                          <button onClick={() => setConfirmModal(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-xl transition shadow-sm">
                            <CheckCircle size={14} /> Tasdiqlash
                          </button>
                        )}
                      </div>
                      <div className="divide-y divide-gray-100">
                        {meeting.tasks.map((task) => (
                          <div key={task.id} className="px-5 py-4">
                            {editingTaskId === task.id ? (
                              <div className="space-y-3">
                                <input value={editData.title ?? task.title}
                                  onChange={e => setEditData({ ...editData, title: e.target.value })}
                                  className="w-full border border-gray-300 text-gray-900 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500"
                                  placeholder="Sarlavha" />
                                <textarea value={editData.description ?? (task.description || '')}
                                  onChange={e => setEditData({ ...editData, description: e.target.value })}
                                  className="w-full border border-gray-300 text-gray-900 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500 resize-none"
                                  placeholder="Tavsif" rows={2} />
                                <div className="grid grid-cols-2 gap-3">
                                  <select value={editData.priority ?? task.priority}
                                    onChange={e => setEditData({ ...editData, priority: e.target.value })}
                                    className="border border-gray-300 text-gray-900 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500">
                                    <option value="high">Yuqori</option>
                                    <option value="medium">O'rta</option>
                                    <option value="low">Past</option>
                                  </select>
                                  <select value={editData.task_type ?? task.task_type}
                                    onChange={e => setEditData({ ...editData, task_type: e.target.value })}
                                    className="border border-gray-300 text-gray-900 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500">
                                    <option value="task">Vazifa</option>
                                    <option value="payment">To'lov</option>
                                    <option value="debt">Qarz</option>
                                    <option value="general">Umumiy</option>
                                  </select>
                                </div>
                                <select value={editData.assigned_to ?? (task.assignee?.id || '')}
                                  onChange={e => setEditData({ ...editData, assigned_to: e.target.value || null })}
                                  className="w-full border border-gray-300 text-gray-900 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500">
                                  <option value="">— Ishchi tanlang —</option>
                                  {employees.map(emp => (
                                    <option key={emp.id} value={emp.id}>
                                      {emp.full_name}{emp.position ? ` — ${emp.position}` : ''}
                                    </option>
                                  ))}
                                </select>
                                <div>
                                  <label className="text-xs text-gray-500 font-medium mb-1 block">
                                    📅 Deadline (muddat)
                                  </label>
                                  <input type="date"
                                    value={editData.deadline ?? (task.deadline ? task.deadline.split('T')[0] : '')}
                                    onChange={e => setEditData({ ...editData, deadline: e.target.value || null })}
                                    className="w-full border border-gray-300 text-gray-900 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500" />
                                </div>
                                {['payment', 'debt'].includes(editData.task_type ?? task.task_type) && (
                                  <div className="grid grid-cols-2 gap-3">
                                    <input type="number" value={editData.amount ?? (task.amount || '')}
                                      onChange={e => setEditData({ ...editData, amount: e.target.value })}
                                      className="border border-gray-300 text-gray-900 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500"
                                      placeholder="Miqdor" />
                                    <select value={editData.currency ?? task.currency}
                                      onChange={e => setEditData({ ...editData, currency: e.target.value })}
                                      className="border border-gray-300 text-gray-900 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500">
                                      <option value="UZS">UZS</option>
                                      <option value="USD">USD</option>
                                    </select>
                                  </div>
                                )}
                                <div className="flex gap-2">
                                  <button onClick={() => updateTaskMutation.mutate({ id: task.id, data: editData })}
                                    disabled={updateTaskMutation.isPending}
                                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-xl transition disabled:opacity-50">
                                    Saqlash
                                  </button>
                                  <button onClick={() => { setEditingTaskId(null); setEditData({}) }}
                                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-xl transition">
                                    Bekor
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 flex-wrap mb-1.5">
                                    <Badge label={TASK_TYPE_LABELS[task.task_type]} className={TASK_TYPE_COLORS[task.task_type]} />
                                    <Badge label={PRIORITY_LABELS[task.priority]} className={PRIORITY_COLORS[task.priority]} />
                                    <Badge label={STATUS_LABELS[task.status]} className={STATUS_COLORS[task.status]} />
                                  </div>
                                  <p className="text-gray-900 text-sm font-medium">{task.title}</p>
                                  {task.description && (
                                    <p className="text-gray-500 text-xs mt-0.5">{task.description}</p>
                                  )}
                                  <div className="flex items-center gap-4 mt-1.5 text-xs flex-wrap">
                                    {task.assignee ? (
                                      <div className="flex items-center gap-1.5">
                                        <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center">
                                          <span className="text-blue-600 text-xs font-bold">
                                            {task.assignee.full_name?.[0]?.toUpperCase()}
                                          </span>
                                        </div>
                                        <span className="text-gray-600 font-medium">{task.assignee.full_name}</span>
                                      </div>
                                    ) : (
                                      <span className="text-red-400">⚠️ Ishchi belgilanmagan</span>
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
                                  {task.report && (
                                    <div className="mt-3 bg-gray-50 rounded-xl p-3 border border-gray-200">
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                          <Badge label={STATUS_LABELS[task.report.status]} className={STATUS_COLORS[task.report.status]} />
                                          <span className="text-gray-400 text-xs">{formatDate(task.report.submitted_at)}</span>
                                        </div>
                                        {task.report.status === 'submitted' && (
                                          <div className="flex gap-2">
                                            <button onClick={() => reviewMutation.mutate({ taskId: task.id, action: 'approve' })}
                                              className="px-3 py-1 bg-green-100 text-green-700 text-xs rounded-lg hover:bg-green-200 transition font-medium">
                                              Tasdiqlash
                                            </button>
                                            <button onClick={() => setRejectModal({ taskId: task.id })}
                                              className="px-3 py-1 bg-red-100 text-red-700 text-xs rounded-lg hover:bg-red-200 transition font-medium">
                                              Qaytarish
                                            </button>
                                          </div>
                                        )}
                                      </div>
                                      {task.report.report_text && (
                                        <p className="text-gray-600 text-xs mt-2">{task.report.report_text}</p>
                                      )}
                                    </div>
                                  )}
                                </div>
                                {canEdit && (
                                  <div className="flex items-center gap-1 shrink-0">
                                    <button onClick={() => { setEditingTaskId(task.id); setEditData({}) }}
                                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition">
                                      <Edit2 size={14} />
                                    </button>
                                    <button onClick={() => deleteTaskMutation.mutate(task.id)}
                                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition">
                                      <Trash2 size={14} />
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </>
        )}

        {/* ===== TOPSHIRIQLAR ===== */}
        {section === 'tasks' && (
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-gray-900 font-bold text-lg mb-5">Barcha topshiriqlar</h2>
            {taskMeetings.map((m) => (
              <MeetingTasksRow key={m.id} meetingId={m.id} meetingTitle={m.title}
                meetingDate={m.meeting_date} meetingStatus={m.status} />
            ))}
          </div>
        )}

        {/* ===== YANGI HISOBOTLAR ===== */}
        {section === 'new_reports' && (
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-gray-900 font-bold text-lg mb-5">Yangi hisobotlar</h2>
            {taskMeetings.map((m) => (
              <MeetingNewReportsRow key={m.id} meetingId={m.id} meetingTitle={m.title}
                meetingDate={m.meeting_date} filterStatus="submitted"
                onSelect={(taskId, task) => setSelectedReport({ taskId, task })} />
            ))}
          </div>
        )}

        {/* ===== TASDIQLANGAN HISOBOTLAR ===== */}
        {section === 'approved_reports' && (
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-gray-900 font-bold text-lg mb-5">Tasdiqlangan hisobotlar</h2>
            {taskMeetings.map((m) => (
              <MeetingNewReportsRow key={m.id} meetingId={m.id} meetingTitle={m.title}
                meetingDate={m.meeting_date} filterStatus="approved"
                onSelect={(taskId, task) => setSelectedReport({ taskId, task })} />
            ))}
          </div>
        )}
      </div>

      {/* Report Detail Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setSelectedReport(null)} />
          <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl
                          border border-gray-200 max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-start justify-between px-6 py-5 border-b border-gray-100">
              <div>
                <h2 className="text-gray-900 font-bold text-base">{selectedReport.task?.title}</h2>
                <p className="text-gray-400 text-xs mt-0.5">Hisobot tafsilotlari</p>
              </div>
              <button onClick={() => setSelectedReport(null)} className="text-gray-400 hover:text-gray-600 transition">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
              {reportLoading ? (
                <div className="flex justify-center py-8"><Spinner size="lg" /></div>
              ) : reportDetail ? (
                <>
                  <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-500 text-sm">Ishchi</span>
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center">
                          <span className="text-purple-600 text-xs font-bold">
                            {reportDetail.employee?.full_name?.[0]?.toUpperCase()}
                          </span>
                        </div>
                        <span className="text-gray-900 text-sm font-medium">{reportDetail.employee?.full_name}</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-500 text-sm">Holati</span>
                      <Badge label={STATUS_LABELS[reportDetail.status]} className={STATUS_COLORS[reportDetail.status]} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-500 text-sm">Yuborilgan</span>
                      <span className="text-gray-700 text-sm">{formatDate(reportDetail.submitted_at)}</span>
                    </div>
                    {reportDetail.reviewed_at && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-500 text-sm">Ko'rib chiqilgan</span>
                        <span className="text-gray-700 text-sm">{formatDate(reportDetail.reviewed_at)}</span>
                      </div>
                    )}
                  </div>

                  {reportDetail.report_text && (
                    <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                      <p className="text-gray-500 text-xs font-medium mb-2">Hisobot matni:</p>
                      <p className="text-gray-700 text-sm leading-relaxed">{reportDetail.report_text}</p>
                    </div>
                  )}

                  {reportDetail.rejection_note && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                      <p className="text-red-600 text-xs font-medium mb-1">Qaytarish sababi:</p>
                      <p className="text-red-500 text-sm">{reportDetail.rejection_note}</p>
                    </div>
                  )}

                  {reportDetail.attachments?.length > 0 && (
                    <div>
                      <p className="text-gray-500 text-xs font-medium mb-2">
                        Biriktirilgan fayllar ({reportDetail.attachments.length}):
                      </p>
                      <div className="space-y-2">
                        {reportDetail.attachments.map((att) => (
                          <AttachmentItem key={att.id} att={att} />
                        ))}
                      </div>
                    </div>
                  )}

                  {reportDetail.status === 'submitted' && (
                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={() => reviewMutation.mutate({ taskId: selectedReport.task.id, action: 'approve' })}
                        className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-xl transition font-medium">
                        ✅ Tasdiqlash
                      </button>
                      <button
                        onClick={() => { setRejectModal({ taskId: selectedReport.task.id }); setSelectedReport(null) }}
                        className="flex-1 py-2.5 bg-red-50 hover:bg-red-100 text-red-600 text-sm rounded-xl transition font-medium border border-red-200">
                        ❌ Qaytarish
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-gray-400 text-sm text-center py-8">Hisobot topilmadi</p>
              )}
            </div>
          </div>
        </div>
      )}

      <Modal isOpen={confirmModal} onClose={() => setConfirmModal(false)} title="Tasdiqlash" size="sm">
        <p className="text-gray-600 text-sm mb-5">Barcha topshiriqlar xodimlarga yuboriladi. Davom etasizmi?</p>
        <div className="flex gap-3 justify-end">
          <button onClick={() => setConfirmModal(false)}
            className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-xl hover:bg-gray-200 transition">
            Bekor
          </button>
          <button onClick={() => confirmMutation.mutate()} disabled={confirmMutation.isPending}
            className="px-4 py-2 bg-green-600 text-white text-sm rounded-xl hover:bg-green-700 transition disabled:opacity-50 flex items-center gap-2">
            {confirmMutation.isPending && <Spinner size="sm" />}
            Ha, tasdiqlash
          </button>
        </div>
      </Modal>

      <Modal isOpen={!!rejectModal} onClose={() => { setRejectModal(null); setRejectNote('') }}
        title="Qaytarish sababi" size="sm">
        <textarea value={rejectNote} onChange={e => setRejectNote(e.target.value)}
          placeholder="Qaytarish sababini yozing..."
          className="w-full border border-gray-300 text-gray-900 rounded-xl p-3 text-sm outline-none focus:border-blue-500 resize-none mb-4"
          rows={3} />
        <div className="flex gap-3 justify-end">
          <button onClick={() => { setRejectModal(null); setRejectNote('') }}
            className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-xl hover:bg-gray-200 transition">
            Bekor
          </button>
          <button
            onClick={() => reviewMutation.mutate({ taskId: rejectModal.taskId, action: 'reject', note: rejectNote })}
            disabled={!rejectNote || reviewMutation.isPending}
            className="px-4 py-2 bg-red-600 text-white text-sm rounded-xl hover:bg-red-700 transition disabled:opacity-50">
            Qaytarish
          </button>
        </div>
      </Modal>
    </div>
  )
}

function MeetingTasksRow({ meetingId, meetingTitle, meetingDate, meetingStatus }) {
  const { data, isLoading } = useQuery({
    queryKey: ['sec-meeting', meetingId],
    queryFn: () => secretaryApi.getMeeting(meetingId).then(r => r.data),
  })

  if (isLoading) return (
    <div className="mb-4 flex items-center gap-2">
      <Spinner size="sm" />
      <span className="text-gray-400 text-xs">Yuklanmoqda...</span>
    </div>
  )
  if (!data?.tasks?.length) return null

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-gray-700 font-semibold text-sm">{meetingTitle || 'Nomsiz majlis'}</h3>
        <span className="text-gray-400 text-xs">{formatDate(meetingDate)}</span>
        <Badge label={STATUS_LABELS[meetingStatus] || meetingStatus} className={STATUS_COLORS[meetingStatus]} />
      </div>
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm divide-y divide-gray-100">
        {data.tasks.map((task) => (
          <div key={task.id} className="px-5 py-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <Badge label={TASK_TYPE_LABELS[task.task_type]} className={TASK_TYPE_COLORS[task.task_type]} />
                  <Badge label={PRIORITY_LABELS[task.priority]} className={PRIORITY_COLORS[task.priority]} />
                  <Badge label={STATUS_LABELS[task.status]} className={STATUS_COLORS[task.status]} />
                </div>
                <p className="text-gray-900 text-sm font-medium">{task.title}</p>
                <div className="flex items-center gap-3 mt-1.5 text-xs flex-wrap">
                  {task.assignee ? (
                    <div className="flex items-center gap-1">
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
                    <span className={deadlineColor(task.deadline)}>
                      📅 {formatDeadline(task.deadline)}
                    </span>
                  )}
                </div>
              </div>
              {task.report && (
                <Badge label={STATUS_LABELS[task.report.status]} className={STATUS_COLORS[task.report.status]} />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function MeetingNewReportsRow({ meetingId, meetingTitle, meetingDate, onSelect, filterStatus }) {
  const { data, isLoading } = useQuery({
    queryKey: ['sec-meeting-reports', meetingId],
    queryFn: () => secretaryApi.getMeetingReports(meetingId).then(r => r.data),
  })

  if (isLoading) return (
    <div className="mb-4 flex items-center gap-2">
      <Spinner size="sm" />
      <span className="text-gray-400 text-xs">Yuklanmoqda...</span>
    </div>
  )

  const filtered = data?.reports?.filter(r => r.status === filterStatus) || []
  if (!filtered.length) return null

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-gray-700 font-semibold text-sm">{meetingTitle || 'Nomsiz majlis'}</h3>
        <span className="text-gray-400 text-xs">{formatDate(meetingDate)}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                         ${filterStatus === 'submitted' ? 'bg-amber-100 text-amber-600' : 'bg-green-100 text-green-600'}`}>
          {filtered.length} ta
        </span>
      </div>
      <div className="space-y-2">
        {filtered.map((report) => (
          <button key={report.id}
            onClick={() => onSelect(report.task_id, { id: report.task_id, title: 'Topshiriq' })}
            className={`w-full text-left bg-white rounded-2xl border shadow-sm p-4 hover:shadow-md transition
                       ${filterStatus === 'submitted' ? 'border-amber-200 hover:border-amber-300' : 'border-green-200 hover:border-green-300'}`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center
                                  ${filterStatus === 'submitted' ? 'bg-amber-100' : 'bg-green-100'}`}>
                    <span className={`text-xs font-bold ${filterStatus === 'submitted' ? 'text-amber-600' : 'text-green-600'}`}>
                      {report.employee?.full_name?.[0]?.toUpperCase()}
                    </span>
                  </div>
                  <span className="text-gray-900 text-sm font-medium">{report.employee?.full_name}</span>
                  {filterStatus === 'submitted' && (
                    <span className="text-xs bg-amber-100 text-amber-600 px-2 py-0.5 rounded-full">Yangi</span>
                  )}
                </div>
                <p className="text-gray-400 text-xs">{formatDate(report.submitted_at)}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge label={STATUS_LABELS[report.status]} className={STATUS_COLORS[report.status]} />
                <ChevronRight size={14} className="text-gray-300" />
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
