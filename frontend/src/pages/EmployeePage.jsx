import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { employeeApi } from '../api/employee'
import Sidebar from '../components/Sidebar'
import Badge from '../components/Badge'
import Spinner from '../components/Spinner'
import Modal from '../components/Modal'
import { formatDeadline, formatDate, deadlineColor } from '../utils/date'
import {
  TASK_TYPE_LABELS, TASK_TYPE_COLORS,
  PRIORITY_LABELS, PRIORITY_COLORS,
  STATUS_LABELS, STATUS_COLORS,
} from '../utils/constants'
import {
  Upload, X, ClipboardList, ChevronRight,
  CheckCircle, Clock, Send, AlertCircle,
} from 'lucide-react'


const NAV_FILTERS = [
  { label: 'Yangi topshiriq', value: 'confirmed', icon: <ClipboardList size={16} /> },
  { label: 'Topshirildi', value: 'submitted', icon: <Clock size={16} /> },
  { label: 'Tasdiqlandi', value: 'approved', icon: <CheckCircle size={16} /> },
  { label: 'Hammasi', value: null, icon: <Send size={16} /> },
]



function AttachmentItem({ att }) {
  if (att.file_type === 'image') {
    return (
      <div className="rounded-xl overflow-hidden border border-gray-200">
        <img
          src={att.file_url}
          alt={att.file_name}
          className="w-full object-cover max-h-64"
          onError={(e) => { e.target.style.display = 'none' }}
        />
        <div className="px-3 py-2 bg-gray-50 flex items-center justify-between">
          <span className="text-gray-600 text-xs truncate">{att.file_name}</span>
          <a
            href={att.file_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 text-xs hover:underline shrink-0 ml-2"
          >
            To'liq ko'rish
          </a>
        </div>
      </div>
    )
  }

  if (att.file_type === 'video') {
    return (
      <div className="rounded-xl overflow-hidden border border-gray-200">
        <video src={att.file_url} controls className="w-full max-h-48" />
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
    <a
      href={att.file_url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-3 bg-gray-50 border border-gray-200
                 rounded-xl px-4 py-3 hover:bg-blue-50 hover:border-blue-200 transition"
    >
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

export default function EmployeePage() {
  const { user } = useAuthStore()
  const qc = useQueryClient()

  const [filter, setFilter] = useState('confirmed')
  const [selectedTask, setSelectedTask] = useState(null)
  const [reportModal, setReportModal] = useState(null)
  const [reportText, setReportText] = useState('')
  const [files, setFiles] = useState([])
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const fileRef = useRef(null)

  const { data, isLoading } = useQuery({
    queryKey: ['my-tasks', filter],
    queryFn: () => employeeApi.getMyTasks(filter).then(r => r.data),
  })

  const { data: stats } = useQuery({
    queryKey: ['my-stats'],
    queryFn: () => employeeApi.getMyStats().then(r => r.data),
  })

  const submitMutation = useMutation({
    mutationFn: () => {
      const fd = new FormData()
      if (reportText) fd.append('report_text', reportText)
      files.forEach(f => fd.append('files', f))
      return employeeApi.submitReport(reportModal, fd)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-tasks'] })
      qc.invalidateQueries({ queryKey: ['my-stats'] })
      setSubmitSuccess(true)
      setTimeout(() => {
        setReportModal(null)
        setReportText('')
        setFiles([])
        setSelectedTask(null)
        setSubmitSuccess(false)
      }, 2000)
    },
  })

  const openReportModal = (taskId) => {
    setReportModal(taskId)
    setReportText('')
    setFiles([])
    setSubmitSuccess(false)
  }

  const closeReportModal = () => {
    setReportModal(null)
    setReportText('')
    setFiles([])
    setSubmitSuccess(false)
  }

  const addFiles = (e) => {
    if (e.target.files) {
      setFiles(prev => [...prev, ...Array.from(e.target.files)])
    }
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const statCounts = {
  total: stats?.total || 0,
  confirmed: stats?.status_counts?.confirmed || 0,
  approved: stats?.status_counts?.approved || 0,
  submitted: stats?.status_counts?.submitted || 0,
  overdue: stats?.overdue_count || 0,
}



  return (
    <div className="flex min-h-screen bg-gray-50">

      <div className="flex">
        <Sidebar />

        {/* Extra left panel */}
        <div className="w-56 min-h-screen bg-white border-r border-gray-200 flex flex-col">
          <div className="px-4 py-4 border-b border-gray-100">
            <h2 className="text-gray-700 font-semibold text-sm">Topshiriqlarim</h2>
          </div>

          <nav className="flex-1 px-3 py-3 space-y-1">
            {NAV_FILTERS.map((f) => {
                const count = f.value !== null ? (statCounts[f.value] || 0) : statCounts.total
              return (
                <button
                  key={String(f.value)}
                  onClick={() => setFilter(f.value)}
                  className={`w-full flex items-center justify-between px-3 py-2.5
                             rounded-xl text-sm font-medium transition
                             ${filter === f.value
                               ? 'bg-blue-50 text-blue-600'
                               : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                             }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={filter === f.value ? 'text-blue-500' : 'text-gray-400'}>
                      {f.icon}
                    </span>
                    {f.label}
                  </div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full
                                   ${filter === f.value
                                     ? 'bg-blue-100 text-blue-600'
                                     : 'bg-gray-100 text-gray-500'
                                   }`}>
                    {count}
                  </span>
                </button>
              )
            })}
          </nav>

          <div className="px-4 py-4 border-t border-gray-100 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-xs">Muddati o'tgan</span>
              <span className="text-red-500 text-xs font-bold">{stats?.overdue_count || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-xs">Bajarilgan</span>
              <span className="text-green-500 text-xs font-bold">{statCounts.approved}</span>
            </div>
          </div>
        </div>
      </div>

      <main className="flex-1 overflow-auto">
        <div className="p-6 max-w-3xl mx-auto space-y-5">

          <div>
            <h1 className="text-xl font-bold text-gray-900">
              Salom, {user?.full_name}!
            </h1>
            <p className="text-gray-500 text-sm mt-0.5">
              {NAV_FILTERS.find(f => f.value === filter)?.label || 'Hammasi'} ko'rinmoqda
            </p>
          </div>

          {isLoading && (
            <div className="flex justify-center pt-10">
              <Spinner size="lg" />
            </div>
          )}

          {!isLoading && !data?.tasks?.length && (
            <div className="flex flex-col items-center justify-center py-16">
              <ClipboardList size={40} className="text-gray-300 mb-3" />
              <p className="text-gray-500 font-medium">Topshiriqlar yo'q</p>
              <p className="text-gray-400 text-sm mt-1">
                {filter ? "Bu bo'limda topshiriq yo'q" : "Hozircha topshiriq yo'q"}
              </p>
            </div>
          )}

          <div className="space-y-3">
            {data?.tasks?.map((task) => (
              <button
                key={task.id}
                onClick={() => setSelectedTask(task)}
                className="w-full text-left bg-white rounded-2xl border border-gray-200
                           shadow-sm p-5 hover:border-blue-300 hover:shadow-md transition"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="space-y-1 mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 text-xs w-24 shrink-0">Topshiriq turi:</span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md
                                         text-xs font-medium ${TASK_TYPE_COLORS[task.task_type]}`}>
                          {TASK_TYPE_LABELS[task.task_type]}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 text-xs w-24 shrink-0">Muhimligi:</span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md
                                         text-xs font-medium ${PRIORITY_COLORS[task.priority]}`}>
                          {PRIORITY_LABELS[task.priority]}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 text-xs w-24 shrink-0">Holati:</span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md
                                         text-xs font-medium ${STATUS_COLORS[task.status]}`}>
                          {STATUS_LABELS[task.status]}
                        </span>
                      </div>
                    </div>

                    <p className="text-gray-900 font-semibold text-sm">{task.title}</p>

                    {task.description && (
                      <p className="text-gray-500 text-xs mt-1 truncate">{task.description}</p>
                    )}

                    <div className="flex items-center gap-4 mt-2 text-xs">
                      {task.deadline && (
                        <span className={`font-medium ${deadlineColor(task.deadline)}`}>
                          📅 {formatDeadline(task.deadline)}
                        </span>
                      )}
                      {task.amount && (
                        <span className="text-gray-400">
                          💰 {task.amount} {task.currency}
                        </span>
                      )}
                    </div>

                    {task.report?.status === 'submitted' && (
                      <div className="mt-2 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-amber-400" />
                        <span className="text-amber-600 text-xs">Ko'rib chiqilmoqda</span>
                      </div>
                    )}
                    {task.report?.status === 'approved' && (
                      <div className="mt-2 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-green-500" />
                        <span className="text-green-600 text-xs">Tasdiqlandi</span>
                      </div>
                    )}
                    {task.report?.status === 'rejected' && (
                      <div className="mt-2 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-red-500" />
                        <span className="text-red-600 text-xs">Qaytarildi</span>
                      </div>
                    )}
                  </div>
                  <ChevronRight size={18} className="text-gray-300 shrink-0 mt-1" />
                </div>
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setSelectedTask(null)}
          />
          <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl
                          border border-gray-200 max-h-[90vh] flex flex-col overflow-hidden">

            <div className="flex items-start justify-between px-6 py-5 border-b border-gray-100">
              <div>
                <h2 className="text-gray-900 font-bold text-base">{selectedTask.title}</h2>
                <p className="text-gray-400 text-xs mt-0.5">Topshiriq tafsilotlari</p>
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-gray-400 hover:text-gray-600 transition"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">

              <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500 text-sm">Topshiriq turi</span>
                  <Badge label={TASK_TYPE_LABELS[selectedTask.task_type]} className={TASK_TYPE_COLORS[selectedTask.task_type]} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500 text-sm">Muhimligi</span>
                  <Badge label={PRIORITY_LABELS[selectedTask.priority]} className={PRIORITY_COLORS[selectedTask.priority]} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500 text-sm">Holati</span>
                  <Badge label={STATUS_LABELS[selectedTask.status]} className={STATUS_COLORS[selectedTask.status]} />
                </div>
                {selectedTask.deadline && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 text-sm">Muddat</span>
                    <span className={`text-sm font-medium ${deadlineColor(selectedTask.deadline)}`}>
                      {formatDeadline(selectedTask.deadline)}
                    </span>
                  </div>
                )}
                {selectedTask.amount && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 text-sm">Miqdor</span>
                    <span className="text-gray-900 text-sm font-medium">
                      {selectedTask.amount} {selectedTask.currency}
                    </span>
                  </div>
                )}
              </div>

              {selectedTask.description && (
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <p className="text-gray-500 text-xs font-medium mb-1">Tavsif</p>
                  <p className="text-gray-700 text-sm leading-relaxed">{selectedTask.description}</p>
                </div>
              )}

              {selectedTask.report && (
                <div className="space-y-3">
                  <h3 className="text-gray-700 font-semibold text-sm">Hisobot</h3>

                  {selectedTask.report.status === 'submitted' && (
                    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                      <p className="text-amber-700 text-sm font-medium">⏳ Ko'rib chiqilmoqda</p>
                      <p className="text-amber-500 text-xs mt-0.5">
                        Yuborilgan: {formatDate(selectedTask.report.submitted_at)}
                      </p>
                    </div>
                  )}

                  {selectedTask.report.status === 'approved' && (
                    <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                      <p className="text-green-700 text-sm font-medium">✅ Tasdiqlandi</p>
                      <p className="text-green-500 text-xs mt-0.5">
                        {formatDate(selectedTask.report.reviewed_at)}
                      </p>
                    </div>
                  )}

                  {selectedTask.report.status === 'rejected' && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                      <p className="text-red-700 text-sm font-medium">Qaytarildi</p>
                      {selectedTask.report.rejection_note && (
                        <p className="text-red-500 text-sm mt-1">
                          Sabab: {selectedTask.report.rejection_note}
                        </p>
                      )}
                    </div>
                  )}

                  {selectedTask.report.report_text && (
                    <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                      <p className="text-gray-500 text-xs font-medium mb-2">Hisobot matni:</p>
                      <p className="text-gray-700 text-sm leading-relaxed">
                        {selectedTask.report.report_text}
                      </p>
                    </div>
                  )}

                  {selectedTask.report.attachments?.length > 0 && (
                    <div>
                      <p className="text-gray-500 text-xs font-medium mb-2">
                        Biriktirilgan fayllar ({selectedTask.report.attachments.length}):
                      </p>
                      <div className="space-y-2">
                        {selectedTask.report.attachments.map((att) => (
                          <AttachmentItem key={att.id} att={att} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {['confirmed', 'in_progress', 'rejected'].includes(selectedTask.status) && (
              <div className="px-6 py-4 border-t border-gray-100">
                <button
                  onClick={() => {
                    openReportModal(selectedTask.id)
                    setSelectedTask(null)
                  }}
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white
                             text-sm rounded-xl transition font-medium shadow-sm"
                >
                  {selectedTask.report?.status === 'rejected' ? 'Qayta yuborish' : 'Hisobot yuborish'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Report Modal */}
      <Modal
        isOpen={!!reportModal}
        onClose={closeReportModal}
        title="Hisobot yuborish"
        size="md"
      >
        {submitSuccess ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center
                           justify-center mx-auto mb-4">
              <CheckCircle size={32} className="text-green-600" />
            </div>
            <p className="text-gray-900 font-semibold text-lg">Hisobot yuborildi!</p>
            <p className="text-gray-500 text-sm mt-1">Kotiba ko'rib chiqadi</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Hisobot matni
              </label>
              <textarea
                value={reportText}
                onChange={e => setReportText(e.target.value)}
                placeholder="Bajargan ishingiz haqida yozing..."
                className="w-full border border-gray-300 text-gray-900 rounded-xl
                           p-3 text-sm outline-none focus:border-blue-500
                           focus:ring-2 focus:ring-blue-100 resize-none"
                rows={4}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Fayllar (ixtiyoriy)
              </label>
              <div
                onClick={() => fileRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-xl p-5
                           text-center cursor-pointer hover:border-blue-400
                           hover:bg-blue-50 transition"
              >
                <Upload size={22} className="text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500 text-sm">Fayl biriktirish uchun bosing</p>
                <p className="text-gray-400 text-xs mt-0.5">Rasm, video, hujjat, audio</p>
              </div>
              <input
                ref={fileRef}
                type="file"
                multiple
                className="hidden"
                onChange={addFiles}
              />
            </div>

            {files.length > 0 && (
              <div className="space-y-2">
                {files.map((f, i) => (
                  <div key={i}
                    className="flex items-center justify-between bg-gray-50
                               border border-gray-200 rounded-xl px-3 py-2.5">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <div className="w-7 h-7 bg-blue-100 rounded-lg flex
                                      items-center justify-center shrink-0">
                        <span className="text-blue-600 text-xs font-bold">
                          {f.name.split('.').pop()?.toUpperCase().slice(0, 3)}
                        </span>
                      </div>
                      <span className="text-gray-700 text-sm truncate">{f.name}</span>
                    </div>
                    <button
                      onClick={() => removeFile(i)}
                      className="text-gray-400 hover:text-red-500 transition ml-2 shrink-0"
                    >
                      <X size={15} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-3 justify-end pt-2">
              <button
                onClick={closeReportModal}
                className="px-4 py-2 bg-gray-100 text-gray-700 text-sm
                           rounded-xl hover:bg-gray-200 transition font-medium"
              >
                Bekor
              </button>
              <button
                onClick={() => submitMutation.mutate()}
                disabled={submitMutation.isPending || (!reportText.trim() && files.length === 0)}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-xl
                           hover:bg-blue-700 transition disabled:opacity-50
                           flex items-center gap-2 font-medium shadow-sm"
              >
                {submitMutation.isPending && <Spinner size="sm" />}
                Yuborish
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}