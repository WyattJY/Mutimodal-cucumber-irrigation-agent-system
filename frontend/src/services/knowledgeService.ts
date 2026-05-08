// Knowledge Service - 知识库服务

import apiClient from './api'
import type { AxiosProgressEvent } from 'axios'
import type {
  KnowledgeSearchParams,
  KnowledgeSearchResult,
  KnowledgeFeedback,
  KnowledgeUploadItem,
  KnowledgeUploadList,
  ApiResponse,
  UploadProgressHandler,
} from '@/types'

const BASE_PATH = '/knowledge'

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

export const knowledgeService = {
  /**
   * 搜索知识库
   */
  async search(params: KnowledgeSearchParams): Promise<KnowledgeSearchResult> {
    const queryParams = new URLSearchParams()
    queryParams.append('q', params.query)
    if (params.top_k) queryParams.append('top_k', String(params.top_k))
    if (params.source && params.source !== 'all') queryParams.append('source', params.source)
    if (params.mode) queryParams.append('mode', params.mode)

    const response = await apiClient.get<ApiResponse<KnowledgeSearchResult>>(
      `${BASE_PATH}/search?${queryParams.toString()}`
    )
    return response.data.data!
  },

  /**
   * 提交知识反馈
   */
  async feedback(data: KnowledgeFeedback): Promise<void> {
    await apiClient.post(`${BASE_PATH}/feedback`, data)
  },

  /**
   * 获取知识来源统计
   */
  async getSourceStats(): Promise<Record<string, number>> {
    const response = await apiClient.get<ApiResponse<Record<string, number>>>(
      `${BASE_PATH}/stats/sources`
    )
    return response.data.data!
  },

  /**
   * 上传用户知识库文献
   */
  async uploadDocument(
    file: File,
    title?: string,
    category = 'user_literature',
    onProgress?: UploadProgressHandler
  ): Promise<KnowledgeUploadItem> {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)
    formData.append('category', category)
    const startedAt = Date.now()

    const response = await apiClient.post<ApiResponse<KnowledgeUploadItem>>(
      `${BASE_PATH}/upload`,
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

  /**
   * 获取用户上传来源
   */
  async listUploads(): Promise<KnowledgeUploadList> {
    const response = await apiClient.get<ApiResponse<KnowledgeUploadList>>(
      `${BASE_PATH}/uploads`
    )
    return response.data.data!
  },
}

export default knowledgeService
