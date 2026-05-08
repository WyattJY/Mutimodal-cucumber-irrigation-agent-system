// WeeklySummaryCard - 周报卡片组件
import React, { useState } from 'react'
import type { WeeklySummaryResult, WeeklyGenerateRequest } from '@/types/predict'
import { predictService } from '@/services'
import { Card } from '../common/Card'
import { Button } from '../common/Button'
import { Spinner } from '../common/Spinner'

interface WeeklySummaryCardProps {
  summary?: WeeklySummaryResult
  onGenerate?: (result: WeeklySummaryResult) => void
}

export const WeeklySummaryCard: React.FC<WeeklySummaryCardProps> = ({
  summary: initialSummary,
  onGenerate
}) => {
  const [summary, setSummary] = useState<WeeklySummaryResult | null>(initialSummary || null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 默认周期：过去7天
  const getDefaultWeek = () => {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 6)
    return {
      week_start: start.toISOString().split('T')[0],
      week_end: end.toISOString().split('T')[0]
    }
  }

  const [weekRange, setWeekRange] = useState(getDefaultWeek())

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)

    try {
      const request: WeeklyGenerateRequest = weekRange
      const result = await predictService.generateWeeklySummary(request)
      setSummary(result)
      onGenerate?.(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成周报失败')
    } finally {
      setLoading(false)
    }
  }

  const getTrendIcon = (better: number, worse: number) => {
    if (better > worse) return '📈'
    if (worse > better) return '📉'
    return '➡️'
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">周报生成</h3>
      </div>

      {/* 日期范围选择 */}
      <div className="flex gap-4 mb-4">
        <div className="flex-1">
          <label className="block text-sm text-gray-500 mb-1">开始日期</label>
          <input
            type="date"
            value={weekRange.week_start}
            onChange={(e) => setWeekRange({ ...weekRange, week_start: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div className="flex-1">
          <label className="block text-sm text-gray-500 mb-1">结束日期</label>
          <input
            type="date"
            value={weekRange.week_end}
            onChange={(e) => setWeekRange({ ...weekRange, week_end: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div className="flex items-end">
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? <Spinner size="sm" /> : '生成周报'}
          </Button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="p-3 bg-red-50 text-red-600 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* 周报内容 */}
      {summary && (
        <div className="space-y-4">
          {/* 统计摘要 */}
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-blue-50 p-3 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-600">
                {summary.statistics.avg_irrigation.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500">日均灌水 L/m²</div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-600">
                {summary.statistics.better_days}
              </div>
              <div className="text-xs text-gray-500">好转天数</div>
            </div>
            <div className="bg-yellow-50 p-3 rounded-lg text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {summary.statistics.same_days}
              </div>
              <div className="text-xs text-gray-500">平稳天数</div>
            </div>
            <div className="bg-red-50 p-3 rounded-lg text-center">
              <div className="text-2xl font-bold text-red-600">
                {summary.statistics.worse_days}
              </div>
              <div className="text-xs text-gray-500">下降天数</div>
            </div>
          </div>

          {/* 关键洞察 */}
          {summary.insights.length > 0 && (
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="font-medium text-blue-800 mb-2">
                {getTrendIcon(summary.statistics.better_days, summary.statistics.worse_days)} 关键洞察
              </div>
              <ul className="space-y-1">
                {summary.insights.map((insight, i) => (
                  <li key={i} className="text-sm text-blue-700">• {insight}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 发现规律 */}
          {summary.patterns.length > 0 && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="font-medium text-gray-800 mb-2">📊 发现规律</div>
              <ul className="space-y-1">
                {summary.patterns.map((pattern, i) => (
                  <li key={i} className="text-sm text-gray-600">• {pattern}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 风险触发 */}
          {summary.risk_triggers.length > 0 && (
            <div className="p-4 bg-orange-50 rounded-lg">
              <div className="font-medium text-orange-800 mb-2">⚠️ 风险事件</div>
              <ul className="space-y-1">
                {summary.risk_triggers.map((trigger, i) => (
                  <li key={i} className="text-sm text-orange-700">• {trigger}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Prompt Block (可折叠) */}
          <details className="p-4 bg-gray-100 rounded-lg">
            <summary className="cursor-pointer font-medium text-gray-700">
              📝 注入 Prompt 预览
            </summary>
            <pre className="mt-2 text-xs text-gray-600 whitespace-pre-wrap">
              {summary.prompt_block}
            </pre>
          </details>
        </div>
      )}
    </Card>
  )
}

export default WeeklySummaryCard
