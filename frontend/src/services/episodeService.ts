// Episode Service - 决策数据服务

import apiClient from './api'
import type {
  Episode,
  EpisodeFilters,
  PaginatedResponse,
  OverrideData,
  GrowthStats,
  ApiResponse,
} from '@/types'

const BASE_PATH = '/episodes'

export const episodeService = {
  /**
   * 获取最新的 Episode
   */
  async getLatest(): Promise<Episode> {
    const response = await apiClient.get<ApiResponse<Episode>>(`${BASE_PATH}/latest`)
    return response.data.data!
  },

  /**
   * 根据日期获取 Episode
   */
  async getByDate(date: string): Promise<Episode> {
    const response = await apiClient.get<ApiResponse<Episode>>(`${BASE_PATH}/${date}`)
    return response.data.data!
  },

  /**
   * 查询 Episode 列表 (支持筛选和分页)
   */
  async query(filters: EpisodeFilters = {}): Promise<PaginatedResponse<Episode>> {
    const params = new URLSearchParams()

    if (filters.start_date) params.append('start_date', filters.start_date)
    if (filters.end_date) params.append('end_date', filters.end_date)
    if (filters.trend && filters.trend !== 'all') params.append('trend', filters.trend)
    if (filters.source && filters.source !== 'all') params.append('source', filters.source)
    if (filters.risk_level && filters.risk_level !== 'all') params.append('risk_level', filters.risk_level)
    if (filters.page) params.append('page', String(filters.page))
    if (filters.page_size) params.append('page_size', String(filters.page_size))

    const response = await apiClient.get<ApiResponse<PaginatedResponse<Episode>>>(
      `${BASE_PATH}?${params.toString()}`
    )
    return response.data.data!
  },

  /**
   * 获取所有日期列表
   */
  async getDateList(): Promise<string[]> {
    const response = await apiClient.get<ApiResponse<string[]>>(`${BASE_PATH}/dates`)
    return response.data.data!
  },

  /**
   * 提交 Override
   */
  async override(data: OverrideData): Promise<Episode> {
    const response = await apiClient.post<ApiResponse<Episode>>('/override', data)
    return response.data.data!
  },

  /**
   * 获取生长统计数据
   */
  async getGrowthStats(): Promise<GrowthStats> {
    const response = await apiClient.get<ApiResponse<GrowthStats>>('/stats/growth')
    return response.data.data!
  },

  /**
   * 获取趋势数据 (用于图表)
   */
  async getTrendData(days: number = 30): Promise<{
    dates: string[]
    irrigation: number[]
    trends: string[]
  }> {
    const response = await apiClient.get<ApiResponse<{
      dates: string[]
      irrigation: number[]
      trends: string[]
    }>>(`/stats/trend?days=${days}`)
    return response.data.data!
  },
}

export default episodeService
