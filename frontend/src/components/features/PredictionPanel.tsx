// PredictionPanel - 预测面板组件
import React, { useState } from 'react'
import type { DailyPredictResult, DailyPredictRequest } from '@/types/predict'
import { predictService } from '@/services'
import { Card } from '../common/Card'
import { Button } from '../common/Button'
import { Spinner } from '../common/Spinner'
import { Badge } from '../common/Badge'
import { SourceBadge } from './SourceBadge'

interface PredictionPanelProps {
  initialDate?: string
  onPredictionComplete?: (result: DailyPredictResult) => void
}

export const PredictionPanel: React.FC<PredictionPanelProps> = ({
  initialDate,
  onPredictionComplete
}) => {
  const [date, setDate] = useState(initialDate || new Date().toISOString().split('T')[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<DailyPredictResult | null>(null)

  const handlePredict = async () => {
    setLoading(true)
    setError(null)

    try {
      const request: DailyPredictRequest = {
        date,
        options: {
          run_sanity_check: true,
          use_rag: true,
          save_episode: true,
          save_response: true
        }
      }

      const predictResult = await predictService.predictDaily(request)
      setResult(predictResult)
      onPredictionComplete?.(predictResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : '预测失败')
    } finally {
      setLoading(false)
    }
  }

  const getTrendColor = (trend: string | null) => {
    switch (trend) {
      case 'better': return 'text-green-600'
      case 'worse': return 'text-red-600'
      default: return 'text-yellow-600'
    }
  }

  const getTrendText = (trend: string | null) => {
    switch (trend) {
      case 'better': return '好转'
      case 'worse': return '下降'
      case 'same': return '平稳'
      default: return '未知'
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">每日灌溉预测</h3>
        {result?.is_cold_start && (
          <Badge variant="warning">冷启动模式</Badge>
        )}
      </div>

      {/* 日期选择 */}
      <div className="flex gap-4 mb-4">
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <Button onClick={handlePredict} disabled={loading}>
          {loading ? <Spinner size="sm" /> : '执行预测'}
        </Button>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="p-3 bg-red-50 text-red-600 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* 预测结果 */}
      {result && (
        <div className="space-y-4">
          {/* 主要结果 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-gray-500">推荐灌水量</div>
              <div className="text-2xl font-bold text-blue-600">
                {result.irrigation_amount.toFixed(1)} L/m²
              </div>
              <SourceBadge source={result.source} />
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-500">长势趋势</div>
              <div className={`text-2xl font-bold ${getTrendColor(result.plant_response?.trend || null)}`}>
                {getTrendText(result.plant_response?.trend || null)}
              </div>
              {result.plant_response && (
                <div className="text-sm text-gray-500">
                  置信度: {(result.plant_response.confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>
          </div>

          {/* 冷启动提示 */}
          {result.is_cold_start && result.plant_response?.current_state_summary && (
            <div className="p-4 bg-yellow-50 rounded-lg">
              <div className="font-medium text-yellow-800 mb-1">当前状态评估</div>
              <div className="text-sm text-yellow-700">
                {result.plant_response.current_state_summary}
              </div>
            </div>
          )}

          {/* SanityCheck 结果 */}
          {result.sanity_check && !result.sanity_check.is_consistent && (
            <div className="p-4 bg-orange-50 rounded-lg">
              <div className="font-medium text-orange-800 mb-1">合理性调整</div>
              <div className="text-sm text-orange-700">
                {result.sanity_check.reason}
              </div>
            </div>
          )}

          {/* 警告和建议 */}
          {result.warnings.length > 0 && (
            <div className="p-4 bg-yellow-50 rounded-lg">
              <div className="font-medium text-yellow-800 mb-2">警告</div>
              <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {result.suggestions.length > 0 && (
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="font-medium text-blue-800 mb-2">建议</div>
              <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
                {result.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {/* RAG 引用 */}
          {result.rag_references.length > 0 && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="font-medium text-gray-800 mb-2">知识库参考</div>
              <div className="space-y-2">
                {result.rag_references.map((ref, i) => (
                  <div key={i} className="text-sm text-gray-600 p-2 bg-white rounded border">
                    <div className="font-medium">{ref.title || ref.doc_id}</div>
                    <div className="text-gray-500">{ref.snippet}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

export default PredictionPanel
