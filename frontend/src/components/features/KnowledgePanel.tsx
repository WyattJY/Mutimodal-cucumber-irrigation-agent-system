// KnowledgePanel - 知识库面板
import React, { useState } from 'react'
import type { RAGAnswer, KnowledgeQueryRequest } from '@/types/predict'
import { predictService } from '@/services'
import { Card } from '../common/Card'
import { Button } from '../common/Button'
import { Spinner } from '../common/Spinner'

interface KnowledgePanelProps {
  onQueryComplete?: (result: RAGAnswer) => void
}

export const KnowledgePanel: React.FC<KnowledgePanelProps> = ({
  onQueryComplete
}) => {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [answer, setAnswer] = useState<RAGAnswer | null>(null)

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setError(null)

    try {
      const request: KnowledgeQueryRequest = {
        question: question.trim(),
        top_k: 5
      }

      const response = await predictService.queryKnowledge(request)
      if (response.success && response.data) {
        setAnswer(response.data)
        onQueryComplete?.(response.data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '查询失败')
    } finally {
      setLoading(false)
    }
  }

  const suggestedQuestions = [
    '黄瓜开花期需要多少灌水量?',
    '高温天气如何调整灌溉?',
    '作物系数 Kc 如何计算?'
  ]

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">知识库问答</h3>

      {/* 搜索表单 */}
      <form onSubmit={handleQuery} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="输入您的问题..."
            className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          />
          <Button type="submit" disabled={loading || !question.trim()}>
            {loading ? <Spinner size="sm" /> : '查询'}
          </Button>
        </div>
      </form>

      {/* 推荐问题 */}
      {!answer && (
        <div className="mb-4">
          <div className="text-sm text-gray-500 mb-2">推荐问题：</div>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((q, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setQuestion(q)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="p-3 bg-red-50 text-red-600 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* 回答 */}
      {answer && (
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <div className="text-gray-800 whitespace-pre-wrap">
              {answer.answer}
            </div>
            <div className="mt-2 text-xs text-gray-400">
              模型: {answer.model}
            </div>
          </div>

          {/* 引用来源 */}
          {answer.references.length > 0 && (
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">
                参考来源 ({answer.references.length})
              </div>
              <div className="space-y-2">
                {answer.references.map((ref, i) => (
                  <div
                    key={i}
                    className="p-3 bg-gray-50 rounded-lg border-l-4 border-blue-400"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm text-gray-800">
                        {ref.title || ref.doc_id}
                      </span>
                      <span className="text-xs text-gray-400">
                        相关度: {(ref.relevance * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 line-clamp-2">
                      {ref.snippet}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 清除结果 */}
          <Button
            variant="ghost"
            onClick={() => {
              setAnswer(null)
              setQuestion('')
            }}
            className="w-full"
          >
            清除结果
          </Button>
        </div>
      )}
    </Card>
  )
}

export default KnowledgePanel
