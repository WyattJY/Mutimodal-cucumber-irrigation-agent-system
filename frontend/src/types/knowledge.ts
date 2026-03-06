// Knowledge Types - 知识库类型定义

/** 知识来源 */
export type KnowledgeSource = 'FAO56' | 'user_upload' | 'system'

/** 知识检索模式 */
export type SearchMode = 'vector' | 'keyword' | 'hybrid'

/** 知识片段 */
export interface KnowledgeChunk {
  id: string
  source: KnowledgeSource
  source_file?: string
  chapter?: string
  page?: number
  content: string
  relevance_score: number
  created_at: string
}

/** 知识检索参数 */
export interface KnowledgeSearchParams {
  query: string
  top_k?: number
  source?: KnowledgeSource | 'all'
  mode?: SearchMode
}

/** 知识检索结果 */
export interface KnowledgeSearchResult {
  chunks: KnowledgeChunk[]
  total: number
  query: string
  search_time_ms: number
}

/** 知识反馈 */
export interface KnowledgeFeedback {
  chunk_id: string
  is_helpful: boolean
  reason?: string
  context?: string
}
