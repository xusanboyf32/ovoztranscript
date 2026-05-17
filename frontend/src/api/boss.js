import client from './client'

export const bossApi = {
  uploadAudio: (formData) =>
    client.post('/boss/meetings/upload-audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  getMeetings: () =>
    client.get('/boss/meetings'),

  getMeeting: (id) =>
    client.get(`/boss/meetings/${id}`),

  getMeetingStatus: (id) =>
    client.get(`/boss/meetings/${id}/status`),

  getOverview: () =>
    client.get('/boss/overview'),

  getStats: () =>
    client.get('/boss/stats'),
}
