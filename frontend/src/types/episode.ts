// Episode Types - 灌溉决策数据类型定义

/** YOLO 检测指标 */
export interface YoloMetrics {
  'leaf Instance Count': number
  'leaf average mask': number
  'flower Instance Count': number
  'flower Mask Pixel Count': number
  'terminal average Mask Pixel Count': number
  'fruit Mask average': number
  'all leaf mask': number
}

/** 环境数据 */
export interface EnvData {
  temperature: number
  humidity: number
  light: number
  solar_radiation?: number
}

/** 长势趋势 */
export type GrowthTrend = 'better' | 'same' | 'worse'

/** 异常等级 */
export type AbnormalityLevel = 'none' | 'mild' | 'moderate' | 'severe'

/** 生长证据 */
export interface Evidence {
  leaf_observation: string
  flower_observation: string
  fruit_observation: string
  terminal_bud_observation: string
}

/** 异常情况 */
export interface Abnormalities {
  wilting: AbnormalityLevel
  yellowing: AbnormalityLevel
  pest_damage: AbnormalityLevel
  other: string
}

/** 变化对比 */
export interface Comparison {
  leaf_area_change: string
  leaf_count_change: string
  flower_count_change: string
  fruit_count_change: string
  overall_vigor_change: string
}

/** LLM 长势响应 */
export interface PlantResponse {
  trend: GrowthTrend
  confidence: number
  evidence: Evidence
  abnormalities: Abnormalities
  growth_stage: string
  comparison: Comparison
  reasoning?: string
}

/** 风险等级 */
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

/** 决策来源 */
export type DecisionSource = 'TSMixer' | 'FAO56' | 'Override'

/** Episode - 单日决策记录 */
export interface Episode {
  date: string
  created_at: string
  prompt_version: string
  image_today: string
  image_yesterday: string
  yolo_today: YoloMetrics
  yolo_yesterday: YoloMetrics
  env_today: EnvData
  response: PlantResponse
  raw_response: string

  // 扩展字段 (后端计算或用户操作)
  irrigation_amount?: number
  decision_source?: DecisionSource
  risk_level?: RiskLevel
  override_reason?: string
  override_by?: string
  override_at?: string
}

/** Episode 列表筛选条件 */
export interface EpisodeFilters {
  start_date?: string
  end_date?: string
  trend?: GrowthTrend | 'all'
  source?: DecisionSource | 'all'
  risk_level?: RiskLevel | 'all'
  page?: number
  page_size?: number
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/** Override 提交数据 */
export interface OverrideData {
  date: string
  original_value: number
  replaced_value: number
  reason: string
  confirmation_answers?: Record<string, string>
}

/** 生长统计 */
export interface GrowthStats {
  created_at: string
  all_leaf_mask: {
    start_value: number
    end_value: number
    total_growth: number
    daily_avg: number
    daily_std: number
    growth_rate_percent: number
  }
  date_range: {
    start: string
    end: string
    total_days: number
  }
  thresholds: {
    better: number
    worse: number
    description: string
  }
}
