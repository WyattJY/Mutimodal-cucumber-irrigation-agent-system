// Knowledge Hooks - 知识库 Query Hooks

import { useQuery, useMutation } from '@tanstack/react-query'
import { knowledgeService } from '@/services'
import type { KnowledgeSearchParams, KnowledgeFeedback } from '@/types'

// Query Keys
export const knowledgeKeys = {
  all: ['knowledge'] as const,
  search: (params: KnowledgeSearchParams) => [...knowledgeKeys.all, 'search', params] as const,
  sourceStats: () => [...knowledgeKeys.all, 'source-stats'] as const,
}

/**
 * 知识库搜索
 * - 当 query 为空时不执行
 */
export function useKnowledgeSearch(params: KnowledgeSearchParams) {
  return useQuery({
    queryKey: knowledgeKeys.search(params),
    queryFn: () => knowledgeService.search(params),
    enabled: !!params.query && params.query.length > 0,
    staleTime: 1000 * 60 * 2, // 2 分钟
  })
}

/**
 * 获取知识来源统计
 */
export function useKnowledgeSourceStats() {
  return useQuery({
    queryKey: knowledgeKeys.sourceStats(),
    queryFn: () => knowledgeService.getSourceStats(),
    staleTime: 1000 * 60 * 10, // 10 分钟
  })
}

/**
 * 知识反馈 Mutation
 */
export function useKnowledgeFeedback() {
  return useMutation({
    mutationFn: (data: KnowledgeFeedback) => knowledgeService.feedback(data),
  })
}
