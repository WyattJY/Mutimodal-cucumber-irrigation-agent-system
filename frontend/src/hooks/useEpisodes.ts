// Episode Hooks - 决策数据 Query Hooks

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { episodeService } from '@/services'
import type { EpisodeFilters, OverrideData } from '@/types'

// Query Keys
export const episodeKeys = {
  all: ['episodes'] as const,
  latest: () => [...episodeKeys.all, 'latest'] as const,
  byDate: (date: string) => [...episodeKeys.all, 'date', date] as const,
  list: (filters: EpisodeFilters) => [...episodeKeys.all, 'list', filters] as const,
  dates: () => [...episodeKeys.all, 'dates'] as const,
  growthStats: () => [...episodeKeys.all, 'growth-stats'] as const,
  trend: (days: number) => [...episodeKeys.all, 'trend', days] as const,
}

/**
 * 获取最新 Episode
 * - 自动轮询 (10秒)
 * - 缓存 1 分钟
 */
export function useLatestEpisode() {
  return useQuery({
    queryKey: episodeKeys.latest(),
    queryFn: () => episodeService.getLatest(),
    staleTime: 1000 * 60, // 1 分钟
    refetchInterval: 1000 * 10, // 10 秒轮询
  })
}

/**
 * 根据日期获取 Episode
 */
export function useEpisode(date: string | undefined) {
  return useQuery({
    queryKey: episodeKeys.byDate(date || ''),
    queryFn: () => episodeService.getByDate(date!),
    enabled: !!date,
    staleTime: 1000 * 60 * 5, // 5 分钟
  })
}

/**
 * 查询 Episode 列表 (支持筛选)
 */
export function useEpisodesQuery(filters: EpisodeFilters = {}) {
  return useQuery({
    queryKey: episodeKeys.list(filters),
    queryFn: () => episodeService.query(filters),
    staleTime: 1000 * 60, // 1 分钟
    placeholderData: (previousData) => previousData, // 保留旧数据
  })
}

/**
 * 获取所有日期列表
 */
export function useEpisodeDates() {
  return useQuery({
    queryKey: episodeKeys.dates(),
    queryFn: () => episodeService.getDateList(),
    staleTime: 1000 * 60 * 5, // 5 分钟
  })
}

/**
 * 获取生长统计数据
 */
export function useGrowthStats() {
  return useQuery({
    queryKey: episodeKeys.growthStats(),
    queryFn: () => episodeService.getGrowthStats(),
    staleTime: 1000 * 60 * 5, // 5 分钟
  })
}

/**
 * 获取趋势数据 (用于图表)
 */
export function useTrendData(days: number = 30) {
  return useQuery({
    queryKey: episodeKeys.trend(days),
    queryFn: () => episodeService.getTrendData(days),
    staleTime: 1000 * 60, // 1 分钟
  })
}

/**
 * Override Mutation
 * - 成功后失效相关缓存
 */
export function useOverrideMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: OverrideData) => episodeService.override(data),
    onSuccess: (episode) => {
      // 失效最新和指定日期的缓存
      queryClient.invalidateQueries({ queryKey: episodeKeys.latest() })
      queryClient.invalidateQueries({ queryKey: episodeKeys.byDate(episode.date) })
      queryClient.invalidateQueries({ queryKey: episodeKeys.all })
    },
  })
}
