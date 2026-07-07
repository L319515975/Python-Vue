import request from '../utils/request'

const wrapPage = (params = {}) => {
  const page = params.page || params.pageNo || 1
  const pageSize = params.page_size || params.pageSize || 20
  return { ...params, page, page_size: pageSize }
}

export const userApi = {
  login: (data) => request.post('/users/login/', data, { skipAuth: true }),
  refreshToken: (data) => request.post('/users/token/refresh/', data, { skipAuth: true }),
  getMe: () => request.get('/users/me/'),
  updateMe: (data) => request.patch('/users/me/', data),
  changePassword: (data) => request.post('/users/change-password/', data),
  list: (params) => request.get('/users/', wrapPage(params)),
  create: (data) => request.post('/users/', data),
  update: (id, data) => request.patch(`/users/${id}/`, data),
  delete: (id) => request.delete(`/users/${id}/`),
}

export const tagApi = {
  list: (params) => request.get('/resumes/tags/', wrapPage(params)),
  create: (data) => request.post('/resumes/tags/', data),
  update: (id, data) => request.patch(`/resumes/tags/${id}/`, data),
  delete: (id) => request.delete(`/resumes/tags/${id}/`),
}

export const resumeApi = {
  list: (params) => request.get('/resumes/', wrapPage(params)),
  detail: (id) => request.get(`/resumes/${id}/`),
  create: (data) => request.post('/resumes/', data),
  update: (id, data) => request.patch(`/resumes/${id}/`, data),
  delete: (id) => request.delete(`/resumes/${id}/`),
  uploadFile: (id, filePath, name = 'file', formData = {}) =>
    request.uploadFile(`/resumes/${id}/upload_file/`, filePath, name, formData),
  updateModules: (id, data) => request.post(`/resumes/${id}/update-modules/`, data),
  setTags: (id, tagIds) => request.post(`/resumes/${id}/set-tags/`, { tag_ids: tagIds }),
  exportPdf: (id, modules, templateKey) =>
    request.post(
      `/resumes/${id}/export-pdf/`,
      { modules, template_key: templateKey },
      { responseType: 'arraybuffer' },
    ),
  generateVisitorLink: (id, data) => request.post(`/resumes/${id}/generate-visitor-link/`, data),
  disableVisitorLink: (id) => request.post(`/resumes/${id}/disable-visitor-link/`),
  visitorLinkInfo: (id) => request.get(`/resumes/${id}/visitor-link-info/`),
}

export const pdfTemplateApi = {
  list: (params) => request.get('/resumes/pdf-templates/', params || {}),
  listAll: () => request.get('/resumes/pdf-templates/', { include_inactive: 1 }),
  create: (filePath, formData) =>
    request.uploadFile('/resumes/pdf-templates/', filePath, 'template_file', formData || {}),
  update: (id, data) => request.patch(`/resumes/pdf-templates/${id}/`, data),
  delete: (id) => request.delete(`/resumes/pdf-templates/${id}/`),
}

export const visitorApi = {
  getResume: (token, params) => request.get(`/resumes/visitor/${token}/`, params, { skipAuth: true }),
  downloadPdf: (token, params) => request.download(`/resumes/visitor/${token}/download/`, { params, skipAuth: true }),
  aiChat: (token, params, data) => request.post(`/resumes/visitor/${token}/ai-chat/`, data, { skipAuth: true, params }),
}

export const educationApi = {
  list: (params) => request.get('/resumes/educations/', wrapPage(params)),
  create: (data) => request.post('/resumes/educations/', data),
  update: (id, data) => request.patch(`/resumes/educations/${id}/`, data),
  delete: (id) => request.delete(`/resumes/educations/${id}/`),
}

export const workApi = {
  list: (params) => request.get('/resumes/work-experiences/', wrapPage(params)),
  create: (data) => request.post('/resumes/work-experiences/', data),
  update: (id, data) => request.patch(`/resumes/work-experiences/${id}/`, data),
  delete: (id) => request.delete(`/resumes/work-experiences/${id}/`),
}

export const projectApi = {
  list: (params) => request.get('/resumes/projects/', wrapPage(params)),
  create: (data) => request.post('/resumes/projects/', data),
  update: (id, data) => request.patch(`/resumes/projects/${id}/`, data),
  delete: (id) => request.delete(`/resumes/projects/${id}/`),
}

export const skillApi = {
  list: (params) => request.get('/resumes/skills/', wrapPage(params)),
  create: (data) => request.post('/resumes/skills/', data),
  update: (id, data) => request.patch(`/resumes/skills/${id}/`, data),
  delete: (id) => request.delete(`/resumes/skills/${id}/`),
}

export const aiApi = {
  chat: (query) => request.post('/ai/chat/', { query }),
  polish: (text, moduleName) => request.post('/ai/polish/', { text, module_name: moduleName }),
  history: (params) => request.get('/ai/history/', wrapPage(params)),
  logs: (params) => request.get('/ai/logs/', wrapPage(params)),
  polishLogs: (params) => request.get('/ai/polish-logs/', wrapPage(params)),
  classificationLogs: (params) => request.get('/ai/classification-logs/', wrapPage(params)),
}

export const auditLogApi = {
  list: (params) => request.get('/users/audit-logs/', wrapPage(params)),
}

export const visitorAiUsageApi = {
  list: (params) => request.get('/users/visitor-ai-logs/', wrapPage(params)),
}
