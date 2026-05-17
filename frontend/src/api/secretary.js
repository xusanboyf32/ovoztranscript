import client from './client'

export const secretaryApi = {
  getMeetings: () =>
    client.get('/secretary/meetings'),

  getMeeting: (id) =>
    client.get(`/secretary/meetings/${id}`),

  updateTranscript: (id, edited_transcript) =>
    client.patch(`/secretary/meetings/${id}/transcript`, { edited_transcript }),

  distributeTasks: (id) =>
    client.post(`/secretary/meetings/${id}/distribute`),

  confirmTasks: (id) =>
    client.post(`/secretary/meetings/${id}/confirm`),

  updateTask: (taskId, data) =>
    client.patch(`/secretary/tasks/${taskId}`, data),

  deleteTask: (taskId) =>
    client.delete(`/secretary/tasks/${taskId}`),

  getMeetingReports: (meetingId) =>
    client.get(`/secretary/meetings/${meetingId}/reports`),

  getReport: (taskId) =>
    client.get(`/secretary/tasks/${taskId}/report`),

  reviewReport: (taskId, action, rejection_note) =>
    client.post(`/secretary/tasks/${taskId}/report/review`, {
      action,
      rejection_note,
    }),

  getEmployees: () =>
    client.get('/secretary/employees'),
}
