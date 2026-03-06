// Knowledge Service - 知识库服务

import apiClient from './api'
import type {
  KnowledgeSearchParams,
  KnowledgeSearchResult,
  KnowledgeFeedback,
  ApiResponse,
} from '@/types'

const BASE_PATH = '/knowledge'

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
}

export default knowledgeService
