// API Types - 通用 API 类型定义

/** API 错误 */
export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

/** 统一 API 响应格式 */
export interface ApiResponse<T = unknown> {
  success: boolean
  data: T | null
  error: ApiError | null
  timestamp: string
}

/** 请求状态 */
export type RequestStatus = 'idle' | 'loading' | 'success' | 'error'

/** 通用列表响应 */
export interface ListResponse<T> {
  items: T[]
  total: number
}
