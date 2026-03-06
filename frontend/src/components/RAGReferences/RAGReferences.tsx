// T3.8 RAGReferences - RAG 引用显示组件
import React, { useState } from 'react'
import type { RAGReference } from '@/types/predict'

interface RAGReferencesProps {
  references: RAGReference[]
  maxDisplay?: number
  title?: string
}

export const RAGReferences: React.FC<RAGReferencesProps> = ({
  references,
  maxDisplay = 3,
  title = '参考来源'
}) => {
  const [expanded, setExpanded] = useState(false)
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  if (!references || references.length === 0) {
    return null
  }

  const displayRefs = expanded ? references : references.slice(0, maxDisplay)
  const hasMore = references.length > maxDisplay

  const toggleItemExpand = (docId: string) => {
    const newSet = new Set(expandedItems)
    if (newSet.has(docId)) {
      newSet.delete(docId)
    } else {
      newSet.add(docId)
    }
    setExpandedItems(newSet)
  }

  const getRelevanceColor = (relevance: number): string => {
    if (relevance >= 0.8) return 'text-green-600 bg-green-100'
    if (relevance >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-gray-600 bg-gray-100'
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700">
          {title} ({references.length})
        </h4>
        {hasMore && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            {expanded ? '收起' : `查看全部 (${references.length})`}
          </button>
        )}
      </div>

      {/* Reference List */}
      <div className="space-y-2">
        {displayRefs.map((ref, index) => {
          const isItemExpanded = expandedItems.has(ref.doc_id)

          return (
            <div
              key={ref.doc_id || index}
              className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden transition-all duration-200 hover:border-gray-300"
            >
              {/* Reference Header */}
              <button
                onClick={() => toggleItemExpand(ref.doc_id)}
                className="w-full px-4 py-3 flex items-start gap-3 text-left"
              >
                {/* Relevance Badge */}
                <span
                  className={`
                    flex-shrink-0 px-2 py-0.5 text-xs font-medium rounded
                    ${getRelevanceColor(ref.relevance)}
                  `}
                >
                  {(ref.relevance * 100).toFixed(0)}%
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {/* Title */}
                  {ref.title && (
                    <div className="font-medium text-gray-800 text-sm mb-1">
                      {ref.title}
                    </div>
                  )}

                  {/* Snippet Preview */}
                  <div
                    className={`text-sm text-gray-600 ${
                      isItemExpanded ? '' : 'line-clamp-2'
                    }`}
                  >
                    {ref.snippet}
                  </div>

                  {/* Doc ID */}
                  <div className="text-xs text-gray-400 mt-1">
                    ID: {ref.doc_id}
                  </div>
                </div>

                {/* Expand Icon */}
                <span
                  className={`
                    flex-shrink-0 text-gray-400 transition-transform duration-200
                    ${isItemExpanded ? 'rotate-180' : ''}
                  `}
                >
                  ▼
                </span>
              </button>

              {/* Expanded Content */}
              {isItemExpanded && (
                <div className="px-4 pb-3 border-t border-gray-200 bg-white">
                  <div className="pt-3 space-y-2">
                    {/* Full Snippet */}
                    <div>
                      <div className="text-xs text-gray-500 mb-1">完整内容</div>
                      <div className="text-sm text-gray-700 whitespace-pre-wrap">
                        {ref.snippet}
                      </div>
                    </div>

                    {/* Metadata */}
                    <div className="flex gap-4 text-xs text-gray-500">
                      <span>相关度: {(ref.relevance * 100).toFixed(1)}%</span>
                      <span>文档: {ref.doc_id}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Show More Button */}
      {hasMore && !expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="w-full py-2 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
        >
          显示更多 ({references.length - maxDisplay} 条)
        </button>
      )}
    </div>
  )
}

// 紧凑版引用列表（用于聊天消息）
interface CompactRAGReferencesProps {
  references: RAGReference[]
  maxDisplay?: number
}

export const CompactRAGReferences: React.FC<CompactRAGReferencesProps> = ({
  references,
  maxDisplay = 3
}) => {
  const [showAll, setShowAll] = useState(false)

  if (!references || references.length === 0) {
    return null
  }

  const displayRefs = showAll ? references : references.slice(0, maxDisplay)

  return (
    <div className="rag-references">
      <div className="rag-references__header">
        <i className="ph-fill ph-books"></i>
        <span>参考来源 ({references.length})</span>
      </div>
      <div className="rag-references__list">
        {displayRefs.map((ref, index) => (
          <div
            key={ref.doc_id || index}
            className="rag-reference-item"
            title={ref.snippet}
          >
            <span className="rag-reference-item__index">[{index + 1}]</span>
            <span className="rag-reference-item__source">{ref.source || 'FAO56'}</span>
            {ref.page && <span className="rag-reference-item__page">P{ref.page}</span>}
            <span className="rag-reference-item__relevance">
              {typeof ref.relevance === 'number' && ref.relevance < 1
                ? `${(ref.relevance * 100).toFixed(0)}%`
                : `${Math.min(ref.relevance || 0, 100).toFixed(0)}%`
              }
            </span>
          </div>
        ))}
      </div>
      {references.length > maxDisplay && (
        <button
          className="rag-references__toggle"
          onClick={() => setShowAll(!showAll)}
        >
          {showAll ? '收起' : `查看全部 ${references.length} 条`}
        </button>
      )}
    </div>
  )
}

export default RAGReferences
