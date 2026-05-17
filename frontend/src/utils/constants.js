export const ROLE_REDIRECT = {
  admin:     '/admin',
  boss:      '/boss',
  secretary: '/secretary',
  employee:  '/my-tasks',
}

export const TASK_TYPE_LABELS = {
  task:    'Vazifa',
  payment: "To'lov",
  debt:    'Qarz',
  general: 'Umumiy',
}

export const TASK_TYPE_COLORS = {
  task:    'bg-blue-100 text-blue-700',
  payment: 'bg-amber-100 text-amber-700',
  debt:    'bg-red-100 text-red-700',
  general: 'bg-gray-100 text-gray-600',
}

export const PRIORITY_LABELS = {
  high:   'Yuqori',
  medium: "O'rta",
  low:    'Past',
}

export const PRIORITY_COLORS = {
  high:   'bg-red-100 text-red-700',
  medium: 'bg-amber-100 text-amber-700',
  low:    'bg-green-100 text-green-700',
}

export const STATUS_LABELS = {
  pending:      'Kutilmoqda',
  confirmed:    'Tasdiqlangan',
  in_progress:  'Jarayonda',
  submitted:    'Yuborildi',
  approved:     'Bajarildi',
  rejected:     'Qaytarildi',
  processing:   'Qayta ishlanmoqda',
  ready:        'Tayyor',
  distributing: 'Taqsimlanmoqda',
  distributed:  'Taqsimlangan',
  failed:       'Xato',
}

export const STATUS_COLORS = {
  pending:      'bg-gray-100 text-gray-600',
  confirmed:    'bg-blue-100 text-blue-700',
  in_progress:  'bg-purple-100 text-purple-700',
  submitted:    'bg-amber-100 text-amber-700',
  approved:     'bg-green-100 text-green-700',
  rejected:     'bg-red-100 text-red-700',
  processing:   'bg-orange-100 text-orange-700',
  ready:        'bg-teal-100 text-teal-700',
  distributed:  'bg-indigo-100 text-indigo-700',
  failed:       'bg-red-100 text-red-700',
}
