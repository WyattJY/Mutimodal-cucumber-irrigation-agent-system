// Weekly Service - 周报服务

import apiClient from './api'
import type { WeeklySummary, WeeklySummaryList, ApiResponse } from '@/types'

const BASE_PATH = '/weekly'

export const weeklyService = {
  /**
   * 获取所有周报列表
   */
  async getAll(): Promise<WeeklySummaryList> {
    const response = await apiClient.get<ApiResponse<WeeklySummaryList>>(BASE_PATH)
    return response.data.data!
  },

  /**
   * 获取最新周报
   */
  async getLatest(): Promise<WeeklySummary> {
    const response = await apiClient.get<ApiResponse<WeeklySummary>>(`${BASE_PATH}/latest`)
    return response.data.data!
  },

  /**
   * 根据周起始日期获取周报
   */
  async getByWeekStart(weekStart: string): Promise<WeeklySummary> {
    const response = await apiClient.get<ApiResponse<WeeklySummary>>(`${BASE_PATH}/${weekStart}`)
    return response.data.data!
  },

  /**
   * 手动触发生成周报
   */
  async generate(weekStart: string): Promise<WeeklySummary> {
    const response = await apiClient.post<ApiResponse<WeeklySummary>>(`${BASE_PATH}/generate`, {
      week_start: weekStart,
    })
    return response.data.data!
  },
}

export default weeklyService
