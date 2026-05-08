// Prediction Service - 预测相关 API 服务

import { apiClient } from './api'
import type {
  DailyPredictRequest,
  DailyPredictResult,
  PlantResponseResult,
  WeeklyGenerateRequest,
  WeeklySummaryResult,
  KnowledgeQueryRequest,
  RAGAnswer,
  UserFeedback,
  FeedbackStats
} from '@/types/predict'
import type { ApiResponse } from '@/types'

// ============================================================================
// 预测 API
// ============================================================================

/**
 * 执行每日预测
 */
export async function predictDaily(request: DailyPredictRequest): Promise<DailyPredictResult> {
  const response = await apiClient.post<DailyPredictResult>('/predict/daily', request)
  return response.data
}

/**
 * 获取指定日期的 PlantResponse
 */
export async function getPlantResponse(date: string): Promise<ApiResponse<PlantResponseResult>> {
  const response = await apiClient.get<ApiResponse<PlantResponseResult>>(`/predict/response/${date}`)
  return response.data
}

/**
 * 获取指定日期的 Episode
 */
export async function getEpisode(date: string): Promise<ApiResponse<Record<string, unknown>>> {
  const response = await apiClient.get<ApiResponse<Record<string, unknown>>>(`/predict/episode/${date}`)
  return response.data
}

/**
 * 列出 PlantResponse 文件
 */
export async function listPlantResponses(
  startDate?: string,
  endDate?: string
): Promise<ApiResponse<{ date: string; file: string; is_cold_start: boolean; trend: string | null }[]>> {
  const params = new URLSearchParams()
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)

  const response = await apiClient.get<ApiResponse<{ date: string; file: string; is_cold_start: boolean; trend: string | null }[]>>(
    `/predict/responses?${params.toString()}`
  )
  return response.data
}

/**
 * 获取最近的 Episodes
 */
export async function listEpisodes(days: number = 7): Promise<ApiResponse<Record<string, unknown>[]>> {
  const response = await apiClient.get<ApiResponse<Record<string, unknown>[]>>(`/predict/episodes?days=${days}`)
  return response.data
}

// ============================================================================
// 周报 API
// ============================================================================

/**
 * 生成周报
 */
export async function generateWeeklySummary(request: WeeklyGenerateRequest): Promise<WeeklySummaryResult> {
  const response = await apiClient.post<WeeklySummaryResult>('/weekly/generate', request)
  return response.data
}

/**
 * 获取最新的 prompt_block
 */
export async function getLatestPromptBlock(): Promise<ApiResponse<{ prompt_block: string | null }>> {
  const response = await apiClient.get<ApiResponse<{ prompt_block: string | null }>>('/weekly/prompt-block/latest')
  return response.data
}

// ============================================================================
// 知识库 API
// ============================================================================

/**
 * 查询知识库 (RAG)
 */
export async function queryKnowledge(request: KnowledgeQueryRequest): Promise<ApiResponse<RAGAnswer>> {
  const response = await apiClient.post<ApiResponse<RAGAnswer>>('/knowledge/query', request)
  return response.data
}

/**
 * 获取知识引用历史
 */
export async function getKnowledgeReferences(
  limit: number = 20,
  episodeDate?: string
): Promise<ApiResponse<{ references: unknown[]; total: number }>> {
  const params = new URLSearchParams()
  params.append('limit', limit.toString())
  if (episodeDate) params.append('episode_date', episodeDate)

  const response = await apiClient.get<ApiResponse<{ references: unknown[]; total: number }>>(
    `/knowledge/references?${params.toString()}`
  )
  return response.data
}

// ============================================================================
// 反馈 API
// ============================================================================

/**
 * 提交用户反馈
 */
export async function submitFeedback(feedback: UserFeedback): Promise<ApiResponse<{ message: string }>> {
  const response = await apiClient.post<ApiResponse<{ message: string }>>('/episodes/feedback', feedback)
  return response.data
}

/**
 * 获取反馈统计
 */
export async function getFeedbackStats(): Promise<ApiResponse<FeedbackStats>> {
  const response = await apiClient.get<ApiResponse<FeedbackStats>>('/episodes/feedback/stats')
  return response.data
}

export default {
  predictDaily,
  getPlantResponse,
  getEpisode,
  listPlantResponses,
  listEpisodes,
  generateWeeklySummary,
  getLatestPromptBlock,
  queryKnowledge,
  getKnowledgeReferences,
  submitFeedback,
  getFeedbackStats
}
