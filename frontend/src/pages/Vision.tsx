// Vision - 视觉分析页面
import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'
import { ImageViewer, MetricsDisplay, ImageUpload } from '@/components/vision'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

interface VisionMetrics {
  leaf_instance_count: number
  leaf_average_mask: number
  flower_instance_count: number
  flower_mask_pixel_count: number
  terminal_average_mask: number
  terminal_instance_count: number
  fruit_mask_average: number
  fruit_instance_count: number
  all_leaf_mask: number
  total_instances: number
  processed_at: string
  visualization_path?: string
  is_mock?: boolean
}

interface AnalysisResult {
  metrics: VisionMetrics
  visualization: string | null
  filename: string
}

export function Vision() {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const handleUpload = useCallback(async (file: File) => {
    // 显示预览
    const reader = new FileReader()
    reader.onload = () => setPreviewUrl(reader.result as string)
    reader.readAsDataURL(file)

    // 上传分析
    setIsLoading(true)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_BASE}/vision/analyze?conf_threshold=0.25`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (data.success) {
        setResult(data.data)
        toast.success('分析完成')
      } else {
        throw new Error(data.detail || '分析失败')
      }
    } catch (error) {
      console.error('Analysis failed:', error)
      toast.error('分析失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 转换为 MetricsDisplay 需要的格式
  const formatMetrics = (metrics: VisionMetrics | null) => {
    if (!metrics) return null

    return {
      leaf: {
        count: metrics.leaf_instance_count,
        avgMask: metrics.leaf_average_mask,
        totalMask: metrics.all_leaf_mask
      },
      flower: {
        count: metrics.flower_instance_count,
        avgMask: metrics.flower_mask_pixel_count / Math.max(metrics.flower_instance_count, 1),
        totalMask: metrics.flower_mask_pixel_count
      },
      terminal: {
        count: metrics.terminal_instance_count,
        avgMask: metrics.terminal_average_mask
      },
      fruit: {
        count: metrics.fruit_instance_count,
        avgMask: metrics.fruit_mask_average
      },
      total_instances: metrics.total_instances,
      processed_at: metrics.processed_at
    }
  }

  return (
    <div className="vision-page">
      {/* 页面头部 */}
      <header className="vision-page__header">
        <div className="vision-page__title-section">
          <h1 className="vision-page__title">
            <i className="ph-bold ph-scan"></i>
            视觉分析
          </h1>
          <p className="vision-page__desc">
            基于 YOLO11 实例分割模型，识别叶片、花朵、顶芽、果实
          </p>
        </div>

        <div className="vision-page__status">
          <span className="vision-page__status-dot"></span>
          <span>模型已加载</span>
        </div>
      </header>

      {/* 主内容区 */}
      <div className="vision-page__content">
        {/* 左侧 - 上传区 */}
        <div className="vision-page__upload-section">
          <div className="vision-page__card">
            <h3 className="vision-page__card-title">
              <i className="ph-bold ph-upload"></i>
              上传图像
            </h3>
            <ImageUpload
              onUpload={handleUpload}
              isLoading={isLoading}
              preview={previewUrl}
            />

            <div className="vision-page__tips">
              <h4>拍摄建议</h4>
              <ul>
                <li>使用高分辨率图像 (推荐 2880×1620)</li>
                <li>保持光线充足均匀</li>
                <li>避免图像模糊或过曝</li>
                <li>尽量包含完整的植株</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 右侧 - 结果区 */}
        <div className="vision-page__result-section">
          {/* 分割结果 */}
          <div className="vision-page__card vision-page__card--large">
            <h3 className="vision-page__card-title">
              <i className="ph-bold ph-image"></i>
              分割结果
            </h3>
            <ImageViewer
              originalBase64={previewUrl?.split(',')[1]}
              segmentedBase64={result?.visualization || undefined}
              isLoading={isLoading}
            />
          </div>

          {/* 指标统计 */}
          <div className="vision-page__card">
            <h3 className="vision-page__card-title">
              <i className="ph-bold ph-chart-bar"></i>
              分割指标
            </h3>
            <MetricsDisplay
              metrics={formatMetrics(result?.metrics || null)}
              isLoading={isLoading}
            />

            {result?.metrics?.is_mock && (
              <div className="vision-page__mock-notice">
                <i className="ph-bold ph-warning"></i>
                <span>当前为模拟数据，模型可能未正确加载</span>
              </div>
            )}
          </div>

          {/* 处理信息 */}
          {result && (
            <div className="vision-page__card vision-page__card--info">
              <div className="vision-page__info-row">
                <span>处理时间</span>
                <span>{new Date(result.metrics.processed_at).toLocaleString()}</span>
              </div>
              <div className="vision-page__info-row">
                <span>文件名</span>
                <span>{result.filename}</span>
              </div>
              <div className="vision-page__info-row">
                <span>总实例数</span>
                <span>{result.metrics.total_instances}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Vision
