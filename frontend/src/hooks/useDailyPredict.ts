// T3.1 useDailyPredict Hook
// 调用每日预测 API 的 React Hook
import { useState, useCallback, useEffect } from 'react'
import type {
  DailyPredictRequest,
  DailyPredictResult,
  PlantResponseResult
} from '@/types/predict'
import { predictService } from '@/services'

interface UseDailyPredictOptions {
  onSuccess?: (result: DailyPredictResult) => void
  onError?: (error: Error) => void
}

interface UseDailyPredictReturn {
  predict: (request: DailyPredictRequest) => Promise<DailyPredictResult | null>
  isLoading: boolean
  error: Error | null
  data: DailyPredictResult | null
  reset: () => void
}

/**
 * 每日预测 Hook
 * 用于调用预测 API 并管理状态
 */
export function useDailyPredict(
  options?: UseDailyPredictOptions
): UseDailyPredictReturn {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [data, setData] = useState<DailyPredictResult | null>(null)

  const predict = useCallback(
    async (request: DailyPredictRequest): Promise<DailyPredictResult | null> => {
      setIsLoading(true)
      setError(null)

      try {
        const result = await predictService.predictDaily(request)
        setData(result)
        options?.onSuccess?.(result)
        return result
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        setError(error)
        options?.onError?.(error)
        return null
      } finally {
        setIsLoading(false)
      }
    },
    [options]
  )

  const reset = useCallback(() => {
    setData(null)
    setError(null)
    setIsLoading(false)
  }, [])

  return {
    predict,
    isLoading,
    error,
    data,
    reset
  }
}

interface UsePlantResponseOptions {
  autoFetch?: boolean
}

interface UsePlantResponseReturn {
  data: PlantResponseResult | null
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * 获取指定日期的 PlantResponse
 */
export function usePlantResponse(
  date: string,
  options?: UsePlantResponseOptions
): UsePlantResponseReturn {
  const [data, setData] = useState<PlantResponseResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchResponse = useCallback(async () => {
    if (!date) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await predictService.getPlantResponse(date)
      if (response.success && response.data) {
        setData(response.data)
      } else {
        setData(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
      setData(null)
    } finally {
      setIsLoading(false)
    }
  }, [date])

  useEffect(() => {
    if (options?.autoFetch !== false && date) {
      fetchResponse()
    }
  }, [date, options?.autoFetch, fetchResponse])

  return {
    data,
    isLoading,
    error,
    refetch: fetchResponse
  }
}

interface UseEpisodeDataReturn {
  data: Record<string, unknown> | null
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * 获取指定日期的 Episode
 */
export function useEpisodeData(date: string): UseEpisodeDataReturn {
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchEpisode = useCallback(async () => {
    if (!date) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await predictService.getEpisode(date)
      if (response.success && response.data) {
        setData(response.data as Record<string, unknown>)
      } else {
        setData(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
      setData(null)
    } finally {
      setIsLoading(false)
    }
  }, [date])

  useEffect(() => {
    if (date) {
      fetchEpisode()
    }
  }, [date, fetchEpisode])

  return {
    data,
    isLoading,
    error,
    refetch: fetchEpisode
  }
}

export default useDailyPredict
