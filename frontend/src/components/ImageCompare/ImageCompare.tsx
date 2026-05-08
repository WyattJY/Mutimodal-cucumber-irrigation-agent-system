// T3.7 ImageCompare - 图像对比组件
import React, { useState, useRef, useCallback } from 'react'

interface YOLOMetrics {
  leaf_area?: number
  flower_count?: number
  fruit_count?: number
  health_score?: number
  detection_confidence?: number
}

interface ImageCompareProps {
  imageYesterday: string  // URL or base64
  imageToday: string
  yoloYesterday?: YOLOMetrics
  yoloToday?: YOLOMetrics
  mode?: 'side-by-side' | 'slider'
  onModeChange?: (mode: 'side-by-side' | 'slider') => void
}

export const ImageCompare: React.FC<ImageCompareProps> = ({
  imageYesterday,
  imageToday,
  yoloYesterday,
  yoloToday,
  mode: initialMode = 'side-by-side',
  onModeChange
}) => {
  const [mode, setMode] = useState<'side-by-side' | 'slider'>(initialMode)
  const [sliderPosition, setSliderPosition] = useState(50)
  const containerRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)

  const handleModeChange = (newMode: 'side-by-side' | 'slider') => {
    setMode(newMode)
    onModeChange?.(newMode)
  }

  const handleMouseDown = useCallback(() => {
    isDragging.current = true
  }, [])

  const handleMouseUp = useCallback(() => {
    isDragging.current = false
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging.current || !containerRef.current) return

    const rect = containerRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const percentage = Math.min(Math.max((x / rect.width) * 100, 0), 100)
    setSliderPosition(percentage)
  }, [])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!containerRef.current) return

    const rect = containerRef.current.getBoundingClientRect()
    const touch = e.touches[0]
    const x = touch.clientX - rect.left
    const percentage = Math.min(Math.max((x / rect.width) * 100, 0), 100)
    setSliderPosition(percentage)
  }, [])

  // 计算 YOLO 指标差异 (reserved for future use)
  const _getDiff = (yesterday?: number, today?: number) => {
    if (yesterday === undefined || today === undefined) return null
    return today - yesterday
  }

  const _formatDiff = (diff: number | null, isPercentage = false): string => {
    if (diff === null) return '-'
    const prefix = diff > 0 ? '+' : ''
    if (isPercentage) {
      return `${prefix}${(diff * 100).toFixed(1)}%`
    }
    return `${prefix}${diff.toFixed(Number.isInteger(diff) ? 0 : 1)}`
  }

  // Suppress unused variable warnings
  void _getDiff
  void _formatDiff

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header with mode toggle */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">图像对比</h3>
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => handleModeChange('side-by-side')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              mode === 'side-by-side'
                ? 'bg-white shadow-sm text-gray-800'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            并排
          </button>
          <button
            onClick={() => handleModeChange('slider')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              mode === 'slider'
                ? 'bg-white shadow-sm text-gray-800'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            滑动
          </button>
        </div>
      </div>

      {/* Image comparison area */}
      {mode === 'side-by-side' ? (
        <div className="grid grid-cols-2 gap-0">
          <div className="relative">
            <div className="absolute top-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
              昨日
            </div>
            <img
              src={imageYesterday}
              alt="昨日图像"
              className="w-full h-auto object-cover"
            />
          </div>
          <div className="relative border-l border-gray-200">
            <div className="absolute top-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
              今日
            </div>
            <img
              src={imageToday}
              alt="今日图像"
              className="w-full h-auto object-cover"
            />
          </div>
        </div>
      ) : (
        <div
          ref={containerRef}
          className="relative cursor-ew-resize select-none"
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onMouseMove={handleMouseMove}
          onTouchMove={handleTouchMove}
        >
          {/* Yesterday image (background) */}
          <img
            src={imageYesterday}
            alt="昨日图像"
            className="w-full h-auto"
          />

          {/* Today image (overlay) */}
          <div
            className="absolute inset-0 overflow-hidden"
            style={{ width: `${sliderPosition}%` }}
          >
            <img
              src={imageToday}
              alt="今日图像"
              className="w-full h-auto"
              style={{
                width: containerRef.current
                  ? `${containerRef.current.offsetWidth}px`
                  : '100%'
              }}
            />
          </div>

          {/* Slider handle */}
          <div
            className="absolute top-0 bottom-0 w-1 bg-white shadow-lg cursor-ew-resize"
            style={{ left: `${sliderPosition}%`, transform: 'translateX(-50%)' }}
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full shadow-lg flex items-center justify-center">
              <span className="text-gray-400">⇔</span>
            </div>
          </div>

          {/* Labels */}
          <div className="absolute top-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
            今日
          </div>
          <div className="absolute top-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
            昨日
          </div>
        </div>
      )}

      {/* YOLO Metrics Comparison */}
      {(yoloYesterday || yoloToday) && (
        <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
          <div className="text-xs text-gray-500 mb-2">YOLO 检测对比</div>
          <div className="grid grid-cols-4 gap-2 text-center">
            <MetricCompare
              label="叶面积"
              yesterday={yoloYesterday?.leaf_area}
              today={yoloToday?.leaf_area}
              isPercentage
            />
            <MetricCompare
              label="花朵数"
              yesterday={yoloYesterday?.flower_count}
              today={yoloToday?.flower_count}
            />
            <MetricCompare
              label="果实数"
              yesterday={yoloYesterday?.fruit_count}
              today={yoloToday?.fruit_count}
            />
            <MetricCompare
              label="健康度"
              yesterday={yoloYesterday?.health_score}
              today={yoloToday?.health_score}
              isPercentage
            />
          </div>
        </div>
      )}
    </div>
  )
}

interface MetricCompareProps {
  label: string
  yesterday?: number
  today?: number
  isPercentage?: boolean
}

const MetricCompare: React.FC<MetricCompareProps> = ({
  label,
  yesterday,
  today,
  isPercentage = false
}) => {
  const diff = yesterday !== undefined && today !== undefined
    ? today - yesterday
    : null

  const formatValue = (value?: number): string => {
    if (value === undefined) return '-'
    if (isPercentage) return `${(value * 100).toFixed(0)}%`
    return value.toFixed(Number.isInteger(value) ? 0 : 1)
  }

  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm font-medium">
        <span className="text-gray-400">{formatValue(yesterday)}</span>
        <span className="mx-1">→</span>
        <span className="text-gray-800">{formatValue(today)}</span>
      </div>
      {diff !== null && (
        <div
          className={`text-xs font-medium ${
            diff > 0
              ? 'text-green-600'
              : diff < 0
              ? 'text-red-600'
              : 'text-gray-500'
          }`}
        >
          {diff > 0 ? '+' : ''}
          {isPercentage
            ? `${(diff * 100).toFixed(1)}%`
            : diff.toFixed(Number.isInteger(diff) ? 0 : 1)}
        </div>
      )}
    </div>
  )
}

export default ImageCompare
