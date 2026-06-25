import request from '@/utils/request'

// User API
export const userApi = {
  login: (data) => request.post('/users/login/', data),
  refreshToken: (data) => request.post('/users/token/refresh/', data),
  getMe: () => request.get('/users/me/'),
  updateMe: (data) => request.patch('/users/me/', data),
  changePassword: (data) => request.post('/users/change-password/', data),
  // Admin only
  list: (params) => request.get('/users/', { params }),
  create: (data) => request.post('/users/', data),
  update: (id, data) => request.patch(`/users/${id}/`, data),
  delete: (id) => request.delete(`/users/${id}/`),
}

// Tag API
export const tagApi = {
  list: (params) => request.get('/resumes/tags/', { params }),
  create: (data) => request.post('/resumes/tags/', data),
  update: (id, data) => request.patch(`/resumes/tags/${id}/`, data),
  delete: (id) => request.delete(`/resumes/tags/${id}/`),
}

// Resume API
export const resumeApi = {
  list: (params) => request.get('/resumes/', { params }),
  detail: (id) => request.get(`/resumes/${id}/`),
  create: (data) => request.post('/resumes/', data),
  update: (id, data) => request.patch(`/resumes/${id}/`, data),
  delete: (id) => request.delete(`/resumes/${id}/`),
  uploadFile: (id, formData) => request.post(`/resumes/${id}/upload_file/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  updateModules: (id, data) => request.post(`/resumes/${id}/update-modules/`, data),
  setTags: (id, tagIds) => request.post(`/resumes/${id}/set-tags/`, { tag_ids: tagIds }),
  exportPdf: (id, modules) => request.post(`/resumes/${id}/export-pdf/`, { modules }, {
    responseType: 'blob',
  }),
  // Visitor link management
  generateVisitorLink: (id, data) => request.post(`/resumes/${id}/generate-visitor-link/`, data),
  disableVisitorLink: (id) => request.post(`/resumes/${id}/disable-visitor-link/`),
  visitorLinkInfo: (id) => request.get(`/resumes/${id}/visitor-link-info/`),
}

// Visitor API (no auth required)
export const visitorApi = {
  getResume: (token, params) => request.get(`/resumes/visitor/${token}/`, { params }),
  downloadPdf: (token, params) => request.get(`/resumes/visitor/${token}/download/`, {
    params,
    responseType: 'blob',
  }),
  // HR visitor AI chat (role=hr in params)
  aiChat: (token, params, data) => request.post(`/resumes/visitor/${token}/ai-chat/`, data, { params }),
}

// Education API
export const educationApi = {
  list: (params) => request.get('/resumes/educations/', { params }),
  create: (data) => request.post('/resumes/educations/', data),
  update: (id, data) => request.patch(`/resumes/educations/${id}/`, data),
  delete: (id) => request.delete(`/resumes/educations/${id}/`),
}

// Work Experience API
export const workApi = {
  list: (params) => request.get('/resumes/work-experiences/', { params }),
  create: (data) => request.post('/resumes/work-experiences/', data),
  update: (id, data) => request.patch(`/resumes/work-experiences/${id}/`, data),
  delete: (id) => request.delete(`/resumes/work-experiences/${id}/`),
}

// Project API
export const projectApi = {
  list: (params) => request.get('/resumes/projects/', { params }),
  create: (data) => request.post('/resumes/projects/', data),
  update: (id, data) => request.patch(`/resumes/projects/${id}/`, data),
  delete: (id) => request.delete(`/resumes/projects/${id}/`),
}

// Skill API
export const skillApi = {
  list: (params) => request.get('/resumes/skills/', { params }),
  create: (data) => request.post('/resumes/skills/', data),
  update: (id, data) => request.patch(`/resumes/skills/${id}/`, data),
  delete: (id) => request.delete(`/resumes/skills/${id}/`),
}

// AI Assistant API
export const aiApi = {
  chat: (query) => request.post('/ai/chat/', { query }),
  polish: (text, moduleName) => request.post('/ai/polish/', { text, module_name: moduleName }),
  history: (params) => request.get('/ai/history/', { params }),
  logs: (params) => request.get('/ai/logs/', { params }),
  polishLogs: (params) => request.get('/ai/polish-logs/', { params }),
  classificationLogs: (params) => request.get('/ai/classification-logs/', { params }),
}

// Audit Log API (admin only)
export const auditLogApi = {
  list: (params) => request.get('/users/audit-logs/', { params }),
}

// HR AI Usage Log API (admin only)
export const hrAiUsageApi = {
  list: (params) => request.get('/users/hr-ai-logs/', { params }),
}

