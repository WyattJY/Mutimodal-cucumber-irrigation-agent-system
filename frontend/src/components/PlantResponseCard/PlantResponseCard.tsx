// T3.6 PlantResponseCard - 主组件
import React from 'react'
import { TrendBadge } from './TrendBadge'
import { ConfidenceBar } from './ConfidenceBar'
import { EvidenceList } from './EvidenceList'
import { AbnormalityAlert } from './AbnormalityAlert'
import type { PlantResponseResult } from '@/types/predict'

interface PlantResponseCardProps {
  response: PlantResponseResult | null
  isLoading?: boolean
  onRefresh?: () => void
}

// 生育期配置
const growthStageLabels: Record<string, { label: string; icon: string }> = {
  vegetative: { label: '营养期', icon: '🌱' },
  flowering: { label: '开花期', icon: '🌸' },
  fruiting: { label: '结果期', icon: '🥒' },
  mixed: { label: '混合期', icon: '🌿' }
}

// 骨架屏组件
const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
)

// Loading 状态骨架屏
const LoadingSkeleton: React.FC = () => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
    <div className="flex items-center justify-between">
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
    <Skeleton className="h-4 w-full" />
    <div className="space-y-2">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
    </div>
    <div className="grid grid-cols-2 gap-4">
      <Skeleton className="h-16" />
      <Skeleton className="h-16" />
    </div>
  </div>
)

// Helper to convert string severity to SeverityType
const toSeverity = (value: string | undefined): 'none' | 'mild' | 'severe' => {
  if (!value || value === 'none' || value === '无' || value === '') return 'none'
  if (value === 'mild' || value === '轻微' || value.includes('轻')) return 'mild'
  if (value === 'severe' || value === '严重' || value.includes('重')) return 'severe'
  return 'none'
}

// Helper to parse comparison value string to number
const parseComparisonValue = (value: string | undefined): number | undefined => {
  if (!value) return undefined
  // Try to extract number from strings like "+5%", "-10%", "增加5%", etc.
  const match = value.match(/([+-]?\d+\.?\d*)/);
  if (match) {
    return parseFloat(match[1]) / 100; // Convert to decimal
  }
  return undefined
}

export const PlantResponseCard: React.FC<PlantResponseCardProps> = ({
  response,
  isLoading = false,
  onRefresh
}) => {
  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (!response) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="text-center py-8">
          <div className="text-4xl mb-3">🌱</div>
          <div className="text-gray-500">暂无植株响应数据</div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="mt-4 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              获取数据
            </button>
          )}
        </div>
      </div>
    )
  }

  const growthStageInfo = response.growth_stage
    ? growthStageLabels[response.growth_stage]
    : null

  // Transform evidence to match EvidenceList interface
  const transformedEvidence = response.evidence ? {
    leaves: response.evidence.leaf_observation,
    flowers: response.evidence.flower_observation,
    fruits: response.evidence.fruit_observation,
    apex: response.evidence.terminal_bud_observation
  } : undefined

  // Transform abnormalities to match AbnormalityAlert interface
  const transformedAbnormalities = response.abnormalities ? {
    wilting: toSeverity(response.abnormalities.wilting),
    yellowing: toSeverity(response.abnormalities.yellowing),
    pests: toSeverity(response.abnormalities.pest_damage),
    disease: toSeverity(response.abnormalities.other)
  } : undefined

  // Parse comparison values
  const parsedComparison = response.comparison ? {
    leaf_area_change: parseComparisonValue(response.comparison.leaf_area_change),
    flower_count_change: parseComparisonValue(response.comparison.flower_count_change),
    fruit_count_change: parseComparisonValue(response.comparison.fruit_count_change),
    overall_vigor_change: parseComparisonValue(response.comparison.overall_vigor_change)
  } : undefined

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-gray-800">植株响应分析</h3>
            {response.is_cold_start && (
              <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded-full border border-yellow-300">
                首次观察
              </span>
            )}
          </div>
          <TrendBadge trend={response.trend} size="md" />
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* 置信度和生育期 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500 mb-2">分析置信度</div>
            <ConfidenceBar value={response.confidence} />
          </div>

          {growthStageInfo && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-2">生育阶段</div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{growthStageInfo.icon}</span>
                <span className="font-medium text-gray-800">
                  {growthStageInfo.label}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* 异常警告 */}
        {transformedAbnormalities && (
          <div>
            <AbnormalityAlert abnormalities={transformedAbnormalities} />
          </div>
        )}

        {/* 观察证据 */}
        {transformedEvidence && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm font-medium text-gray-700 mb-3">
              观察记录
            </div>
            <EvidenceList evidence={transformedEvidence} />
          </div>
        )}

        {/* 对比分析（非冷启动） */}
        {!response.is_cold_start && parsedComparison && (
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-sm font-medium text-blue-800 mb-3">
              与昨日对比
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {parsedComparison.leaf_area_change !== undefined && (
                <ComparisonItem
                  label="叶面积"
                  value={parsedComparison.leaf_area_change}
                  unit="%"
                />
              )}
              {parsedComparison.flower_count_change !== undefined && (
                <ComparisonItem
                  label="花朵数"
                  value={parsedComparison.flower_count_change}
                  isCount
                />
              )}
              {parsedComparison.fruit_count_change !== undefined && (
                <ComparisonItem
                  label="果实数"
                  value={parsedComparison.fruit_count_change}
                  isCount
                />
              )}
              {parsedComparison.overall_vigor_change !== undefined && (
                <ComparisonItem
                  label="整体活力"
                  value={parsedComparison.overall_vigor_change}
                  unit="%"
                />
              )}
            </div>
          </div>
        )}

        {/* 当前状态摘要 (冷启动时显示) */}
        {response.current_state_summary && (
          <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4">
            <div className="font-medium text-gray-700 mb-2">状态摘要</div>
            <p className="whitespace-pre-wrap">{response.current_state_summary}</p>
          </div>
        )}

        {/* 刷新按钮 */}
        {onRefresh && (
          <div className="flex justify-end pt-2">
            <button
              onClick={onRefresh}
              className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              刷新分析
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// 对比项组件
interface ComparisonItemProps {
  label: string
  value: number
  unit?: string
  isCount?: boolean
}

const ComparisonItem: React.FC<ComparisonItemProps> = ({
  label,
  value,
  unit = '',
  isCount = false
}) => {
  const isPositive = value > 0
  const isNegative = value < 0
  const displayValue = isCount
    ? (isPositive ? '+' : '') + value
    : (isPositive ? '+' : '') + (value * 100).toFixed(1) + unit

  return (
    <div className="text-center">
      <div className="text-xs text-blue-600 mb-1">{label}</div>
      <div
        className={`text-lg font-semibold ${
          isPositive
            ? 'text-green-600'
            : isNegative
            ? 'text-red-600'
            : 'text-gray-600'
        }`}
      >
        {displayValue}
      </div>
    </div>
  )
}

export default PlantResponseCard
