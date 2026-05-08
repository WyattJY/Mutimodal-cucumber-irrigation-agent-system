// FeedbackForm - 用户反馈表单
import React, { useState } from 'react'
import type { UserFeedback } from '@/types/predict'
import { predictService } from '@/services'
import { Card } from '../common/Card'
import { Button } from '../common/Button'
import { Spinner } from '../common/Spinner'

interface FeedbackFormProps {
  date: string
  predictedValue?: number
  onSubmit?: (feedback: UserFeedback) => void
}

export const FeedbackForm: React.FC<FeedbackFormProps> = ({
  date,
  predictedValue,
  onSubmit
}) => {
  const [actualIrrigation, setActualIrrigation] = useState<string>('')
  const [rating, setRating] = useState<number>(0)
  const [notes, setNotes] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const feedback: UserFeedback = {
        date,
        actual_irrigation: actualIrrigation ? parseFloat(actualIrrigation) : undefined,
        rating: rating > 0 ? rating : undefined,
        notes: notes || undefined
      }

      await predictService.submitFeedback(feedback)
      setSuccess(true)
      onSubmit?.(feedback)

      // 重置表单
      setActualIrrigation('')
      setRating(0)
      setNotes('')
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交失败')
    } finally {
      setLoading(false)
    }
  }

  const diff = actualIrrigation && predictedValue
    ? parseFloat(actualIrrigation) - predictedValue
    : null

  return (
    <Card className="p-4">
      <h4 className="font-medium text-gray-800 mb-3">
        反馈表单 - {date}
      </h4>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 实际灌水量 */}
        <div>
          <label className="block text-sm text-gray-600 mb-1">
            实际灌水量 (L/m²)
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              step="0.1"
              min="0"
              max="20"
              value={actualIrrigation}
              onChange={(e) => setActualIrrigation(e.target.value)}
              placeholder="例如: 5.2"
              className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
            {diff !== null && (
              <span className={`text-sm ${diff > 0 ? 'text-red-500' : diff < 0 ? 'text-green-500' : 'text-gray-500'}`}>
                {diff > 0 ? '+' : ''}{diff.toFixed(1)}
              </span>
            )}
          </div>
          {predictedValue && (
            <div className="text-xs text-gray-400 mt-1">
              预测值: {predictedValue.toFixed(1)} L/m²
            </div>
          )}
        </div>

        {/* 评分 */}
        <div>
          <label className="block text-sm text-gray-600 mb-1">
            预测准确度评分
          </label>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(star)}
                className={`text-2xl transition-colors ${
                  star <= rating ? 'text-yellow-400' : 'text-gray-300'
                } hover:text-yellow-400`}
              >
                ★
              </button>
            ))}
            {rating > 0 && (
              <button
                type="button"
                onClick={() => setRating(0)}
                className="ml-2 text-xs text-gray-400 hover:text-gray-600"
              >
                清除
              </button>
            )}
          </div>
        </div>

        {/* 备注 */}
        <div>
          <label className="block text-sm text-gray-600 mb-1">
            备注 (可选)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="任何观察或建议..."
            rows={2}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none"
          />
        </div>

        {/* 错误/成功提示 */}
        {error && (
          <div className="p-2 bg-red-50 text-red-600 text-sm rounded">
            {error}
          </div>
        )}
        {success && (
          <div className="p-2 bg-green-50 text-green-600 text-sm rounded">
            反馈已提交，感谢您的贡献！
          </div>
        )}

        {/* 提交按钮 */}
        <Button
          type="submit"
          disabled={loading || (!actualIrrigation && rating === 0 && !notes)}
          className="w-full"
        >
          {loading ? <Spinner size="sm" /> : '提交反馈'}
        </Button>
      </form>
    </Card>
  )
}

export default FeedbackForm
