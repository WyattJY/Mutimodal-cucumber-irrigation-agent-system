// Predict Types - 预测相关类型定义

/** 预测选项 */
export interface PredictOptions {
  run_sanity_check?: boolean
  use_rag?: boolean
  save_episode?: boolean
  save_response?: boolean
}

/** 每日预测请求 */
export interface DailyPredictRequest {
  date: string
  image_base64?: string
  env_data?: {
    temperature?: number
    humidity?: number
    light?: number
  }
  options?: PredictOptions
}

/** 预测来源 */
export type PredictionSource = 'tsmixer' | 'override' | 'sanity_adjusted' | 'fallback'

/** RAG 引用 */
export interface RAGReference {
  doc_id: string
  title?: string
  source?: string
  page?: number
  snippet: string
  relevance: number
}

/** 长势评估结果 (冷启动支持) */
export interface PlantResponseResult {
  trend: 'better' | 'same' | 'worse' | null
  confidence: number
  evidence: {
    leaf_observation: string
    flower_observation: string
    fruit_observation: string
    terminal_bud_observation: string
  }
  abnormalities: {
    wilting: string
    yellowing: string
    pest_damage: string
    other: string
  }
  growth_stage: string
  comparison?: {
    leaf_area_change: string
    leaf_count_change: string
    flower_count_change: string
    fruit_count_change: string
    overall_vigor_change: string
  } | null
  is_cold_start: boolean
  current_state_summary?: string
}

/** SanityCheck 结果 */
export interface SanityCheckResult {
  is_consistent: boolean
  confidence: number
  adjusted_value: number
  reason: string
  rag_used: boolean
}

/** YOLO 指标 (标准化) */
export interface YoloMetricsNormalized {
  leaf_instance_count: number
  leaf_average_mask: number
  flower_instance_count: number
  flower_mask_pixel_count: number
  terminal_average_mask_pixel_count: number
  fruit_mask_average: number
  all_leaf_mask: number
}

/** 每日预测结果 */
export interface DailyPredictResult {
  date: string
  irrigation_amount: number
  source: PredictionSource
  is_cold_start: boolean

  yolo_metrics?: YoloMetricsNormalized
  plant_response?: PlantResponseResult
  sanity_check?: SanityCheckResult
  rag_references: RAGReference[]

  warnings: string[]
  suggestions: string[]

  episode_id?: string
  response_saved_path?: string
}

/** 知识库查询请求 */
export interface KnowledgeQueryRequest {
  question: string
  context?: Record<string, unknown>
  top_k?: number
}

/** RAG 增强回答 */
export interface RAGAnswer {
  answer: string
  references: RAGReference[]
  model: string
}

/** 周报生成请求 */
export interface WeeklyGenerateRequest {
  week_start: string
  week_end: string
}

/** 周统计数据 */
export interface WeeklyStatistics {
  avg_irrigation: number
  max_irrigation: number
  min_irrigation: number
  override_rate: number
  better_days: number
  same_days: number
  worse_days: number
}

/** 周报结果 */
export interface WeeklySummaryResult {
  week_start: string
  week_end: string
  patterns: string[]
  risk_triggers: string[]
  overrides: Array<{
    date: string
    reason: string
  }>
  statistics: WeeklyStatistics
  prompt_block: string
  insights: string[]
}

/** 用户反馈 */
export interface UserFeedback {
  date: string
  actual_irrigation?: number
  rating?: number
  notes?: string
}

/** 反馈统计 */
export interface FeedbackStats {
  total_feedback: number
  with_actual_irrigation: number
  average_rating: number
  rating_count: number
  average_prediction_diff: number
}
