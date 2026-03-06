// T3.3 ConfidenceBar - 置信度进度条组件
import React from 'react'

interface ConfidenceBarProps {
  value: number  // 0-1
  showLabel?: boolean
  height?: 'sm' | 'md' | 'lg'
}

const getColorClass = (value: number): string => {
  if (value < 0.5) return 'bg-red-500'
  if (value < 0.7) return 'bg-yellow-500'
  return 'bg-green-500'
}

const getBackgroundClass = (value: number): string => {
  if (value < 0.5) return 'bg-red-100'
  if (value < 0.7) return 'bg-yellow-100'
  return 'bg-green-100'
}

const heightConfig = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3'
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  value,
  showLabel = true,
  height = 'md'
}) => {
  const percentage = Math.min(Math.max(value * 100, 0), 100)
  const colorClass = getColorClass(value)
  const bgClass = getBackgroundClass(value)
  const heightClass = heightConfig[height]

  return (
    <div className="w-full">
      <div className="flex items-center gap-2">
        <div className={`flex-1 ${bgClass} rounded-full overflow-hidden ${heightClass}`}>
          <div
            className={`${colorClass} ${heightClass} rounded-full transition-all duration-500 ease-out`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {showLabel && (
          <span className="text-sm font-medium text-gray-600 min-w-[3rem] text-right">
            {percentage.toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  )
}

export default ConfidenceBar
