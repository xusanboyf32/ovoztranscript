import client from './client'

export const employeeApi = {
  getMyTasks: (status_filter) =>
  client.get(`/employee/my-tasks${status_filter && status_filter !== null ? `?status_filter=${status_filter}` : ''}`),

  submitReport: (taskId, formData) =>
    client.post(`/employee/tasks/${taskId}/report`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  getMyStats: () =>
    client.get('/employee/my-stats'),

  getProfile: () =>
    client.get('/employee/profile'),
}
