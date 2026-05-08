// Weekly Hooks - 周报 Query Hooks

import { useQuery } from '@tanstack/react-query'
import { weeklyService } from '@/services'

// Query Keys
export const weeklyKeys = {
  all: ['weekly'] as const,
  list: () => [...weeklyKeys.all, 'list'] as const,
  latest: () => [...weeklyKeys.all, 'latest'] as const,
  byWeekStart: (weekStart: string) => [...weeklyKeys.all, 'week', weekStart] as const,
}

/**
 * 获取所有周报列表
 */
export function useWeeklySummaries() {
  return useQuery({
    queryKey: weeklyKeys.list(),
    queryFn: () => weeklyService.getAll(),
    staleTime: 1000 * 60 * 5, // 5 分钟
  })
}

/**
 * 获取最新周报
 */
export function useLatestWeeklySummary() {
  return useQuery({
    queryKey: weeklyKeys.latest(),
    queryFn: () => weeklyService.getLatest(),
    staleTime: 1000 * 60 * 5, // 5 分钟
  })
}

/**
 * 根据周起始日期获取周报
 */
export function useWeeklySummary(weekStart: string | undefined) {
  return useQuery({
    queryKey: weeklyKeys.byWeekStart(weekStart || ''),
    queryFn: () => weeklyService.getByWeekStart(weekStart!),
    enabled: !!weekStart,
    staleTime: 1000 * 60 * 5, // 5 分钟
  })
}
