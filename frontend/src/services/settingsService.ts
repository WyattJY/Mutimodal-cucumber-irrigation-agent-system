import apiClient from './api'
import type { ApiResponse } from '@/types'

export interface LLMSettings {
  use_custom_config: boolean
  has_custom_key: boolean
  custom_base_url?: string | null
  custom_model?: string | null
  active_model: string
  active_base_url: string
  default_model: string
  default_base_url: string
}

export const settingsService = {
  async getSettings(): Promise<LLMSettings> {
    const response = await apiClient.get<ApiResponse<LLMSettings>>('/settings/')
    return response.data.data!
  },
}

export default settingsService
