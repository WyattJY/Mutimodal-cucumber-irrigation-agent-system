// SourceBadge - 来源显示组件
import React from 'react'
import type { PredictionSource } from '@/types/predict'

interface SourceBadgeProps {
  source: PredictionSource
  className?: string
}

const sourceConfig: Record<PredictionSource, { label: string; color: string; bg: string }> = {
  tsmixer: {
    label: 'TSMixer',
    color: 'text-blue-700',
    bg: 'bg-blue-100'
  },
  override: {
    label: '人工修正',
    color: 'text-purple-700',
    bg: 'bg-purple-100'
  },
  sanity_adjusted: {
    label: 'AI 调整',
    color: 'text-orange-700',
    bg: 'bg-orange-100'
  },
  fallback: {
    label: '默认值',
    color: 'text-gray-700',
    bg: 'bg-gray-100'
  }
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({ source, className = '' }) => {
  const config = sourceConfig[source] || sourceConfig.fallback

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color} ${className}`}
    >
      {config.label}
    </span>
  )
}

export default SourceBadge
