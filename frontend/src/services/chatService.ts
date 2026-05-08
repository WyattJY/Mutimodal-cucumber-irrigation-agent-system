import type { AxiosProgressEvent } from 'axios'
import apiClient from './api'
import type { ApiResponse, ChatImageAttachment, UploadProgressHandler } from '@/types'

const BASE_PATH = '/chat'

const emitUploadProgress = (
  event: AxiosProgressEvent,
  startedAt: number,
  onProgress?: UploadProgressHandler
) => {
  if (!onProgress) return

  const loaded = event.loaded || 0
  const total = event.total || undefined
  const elapsedSeconds = Math.max((Date.now() - startedAt) / 1000, 0.1)
  const bytesPerSecond = loaded / elapsedSeconds
  const etaSeconds =
    total && bytesPerSecond > 0 && loaded < total
      ? Math.ceil((total - loaded) / bytesPerSecond)
      : undefined

  onProgress({
    loaded,
    total,
    percent: total ? Math.min(100, Math.round((loaded / total) * 100)) : 0,
    etaSeconds,
  })
}

export const chatService = {
  async uploadImageAttachment(
    file: File,
    onProgress?: UploadProgressHandler
  ): Promise<ChatImageAttachment> {
    const formData = new FormData()
    formData.append('file', file)
    const startedAt = Date.now()

    const response = await apiClient.post<ApiResponse<ChatImageAttachment>>(
      `${BASE_PATH}/attachments/image`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000,
        onUploadProgress: (event) => emitUploadProgress(event, startedAt, onProgress),
      }
    )

    onProgress?.({
      loaded: file.size,
      total: file.size,
      percent: 100,
    })
    return response.data.data!
  },
}

export default chatService
