function sanitizeFileName(value) {
  const text = String(value || 'resume')
    .replace(/[\\/:*?"<>|]+/g, '_')
    .replace(/\s+/g, ' ')
    .trim()
  return text || 'resume'
}

function buildPdfFilePath(baseName, templateName) {
  const nameParts = [baseName, templateName].filter(Boolean)
  const fileName = sanitizeFileName(nameParts.join('-')) + '-' + Date.now() + '.pdf'
  return wx.env.USER_DATA_PATH + '/' + fileName
}

function savePdfResponse(response, baseName, templateName) {
  const filePath = buildPdfFilePath(baseName, templateName)
  const fileSystem = wx.getFileSystemManager()
  const fileContent = response && response.data ? response.data : response

  if (fileContent instanceof ArrayBuffer) {
    fileSystem.writeFileSync(filePath, fileContent)
    return filePath
  }

  fileSystem.writeFileSync(filePath, fileContent, 'binary')
  return filePath
}

function formatTemplateName(item) {
  if (!item) return '默认模板'
  return item.name + (item.is_builtin ? '（内置）' : '')
}

export { buildPdfFilePath, formatTemplateName, sanitizeFileName, savePdfResponse }
