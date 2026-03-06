// T3.2 TrendBadge - 趋势标签组件
import React from 'react'

export type TrendValue = 'better' | 'same' | 'worse' | null

interface TrendBadgeProps {
  trend: TrendValue
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const trendConfig = {
  better: {
    icon: '↑',
    label: '好转',
    bgColor: 'bg-green-100',
    textColor: 'text-green-700',
    borderColor: 'border-green-300'
  },
  same: {
    icon: '→',
    label: '平稳',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-600',
    borderColor: 'border-gray-300'
  },
  worse: {
    icon: '↓',
    label: '下降',
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
    borderColor: 'border-red-300'
  },
  null: {
    icon: '?',
    label: '首次',
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-700',
    borderColor: 'border-yellow-300'
  }
}

const sizeConfig = {
  sm: {
    wrapper: 'px-2 py-0.5 text-xs',
    icon: 'text-sm'
  },
  md: {
    wrapper: 'px-3 py-1 text-sm',
    icon: 'text-base'
  },
  lg: {
    wrapper: 'px-4 py-1.5 text-base',
    icon: 'text-lg'
  }
}

export const TrendBadge: React.FC<TrendBadgeProps> = ({
  trend,
  size = 'md',
  showLabel = true
}) => {
  const config = trendConfig[trend ?? 'null']
  const sizeClasses = sizeConfig[size]

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full border font-medium
        transition-all duration-200 hover:shadow-sm
        ${config.bgColor} ${config.textColor} ${config.borderColor}
        ${sizeClasses.wrapper}
      `}
    >
      <span className={`${sizeClasses.icon} animate-pulse`}>
        {config.icon}
      </span>
      {showLabel && <span>{config.label}</span>}
    </span>
  )
}

export default TrendBadge
