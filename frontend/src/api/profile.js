import client from './client'

export const profileApi = {
  getProfile: () =>
    client.get('/profile'),

  updateProfile: (data) =>
    client.patch('/profile', data),

  uploadAvatar: (formData) =>
    client.post('/profile/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}
