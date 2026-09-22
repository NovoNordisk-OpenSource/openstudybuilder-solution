function generateDownload(blobData, fileName) {
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blobData)
  link.download = fileName
  link.click()
  URL.revokeObjectURL(link.href)
}

function downloadFile(data, type, fileName) {
  const blob = new Blob([data], { type: type })
  generateDownload(blob, fileName)
}

export default {
  generateDownload,
  downloadFile,
}
