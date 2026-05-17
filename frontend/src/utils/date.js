import dayjs from 'dayjs'

export const formatDate = (date) => {
  if (!date) return '—'
  return dayjs(date).format('DD.MM.YYYY HH:mm')
}

export const formatDeadline = (date) => {
  if (!date) return '—'
  return dayjs(date).format('DD.MM.YYYY')
}

export const deadlineColor = (date) => {
  if (!date) return 'text-gray-400'
  const now = dayjs()
  const d = dayjs(date)
  if (d.isBefore(now, 'day')) return 'text-red-600'
  if (d.isSame(now, 'day')) return 'text-amber-600'
  return 'text-green-600'
}
