// Weekly Types - 周报数据类型定义

/** 周统计数据 */
export interface WeeklyStats {
  total_irrigation: number
  avg_irrigation: number
  trend_distribution: {
    better: number
    same: number
    worse: number
  }
  override_count: number
  risk_distribution: {
    low: number
    medium: number
    high: number
    critical: number
  }
}

/** RAG 引用片段 */
export interface RAGReference {
  id: string
  source: string
  chapter?: string
  page?: number
  content: string
  relevance_score: number
}

/** 周报 */
export interface WeeklySummary {
  id: string
  week_start: string
  week_end: string
  created_at: string

  // LLM 生成的洞察
  insights: string[]

  // 统计数据
  stats: WeeklyStats

  // RAG 引用
  rag_references: RAGReference[]

  // 注入下周的 Prompt
  injected_prompt?: string
}

/** 周报列表 */
export interface WeeklySummaryList {
  items: WeeklySummary[]
  total: number
}
