// ImageViewer - 图像查看器组件 (支持原图/分割图切换)
import { useState } from 'react'
import clsx from 'clsx'

interface ImageViewerProps {
  originalUrl?: string
  segmentedUrl?: string
  originalBase64?: string
  segmentedBase64?: string
  isLoading?: boolean
  onCompare?: () => void
}

export function ImageViewer({
  originalUrl,
  segmentedUrl,
  originalBase64,
  segmentedBase64,
  isLoading = false,
  onCompare
}: ImageViewerProps) {
  const [showOriginal, setShowOriginal] = useState(false)
  const [isZoomed, setIsZoomed] = useState(false)

  const originalSrc = originalBase64 ? `data:image/jpeg;base64,${originalBase64}` : originalUrl
  const segmentedSrc = segmentedBase64 ? `data:image/jpeg;base64,${segmentedBase64}` : segmentedUrl
  const currentSrc = showOriginal ? originalSrc : segmentedSrc

  const hasImage = !!(originalSrc || segmentedSrc)

  return (
    <div className="image-viewer">
      {/* 工具栏 */}
      <div className="image-viewer__toolbar">
        <div className="image-viewer__tabs">
          <button
            onClick={() => setShowOriginal(false)}
            className={clsx('image-viewer__tab', !showOriginal && 'image-viewer__tab--active')}
            disabled={!segmentedSrc}
          >
            <i className="ph-bold ph-scan"></i>
            分割图
          </button>
          <button
            onClick={() => setShowOriginal(true)}
            className={clsx('image-viewer__tab', showOriginal && 'image-viewer__tab--active')}
            disabled={!originalSrc}
          >
            <i className="ph-bold ph-image"></i>
            原图
          </button>
        </div>

        <div className="image-viewer__actions">
          {onCompare && (
            <button onClick={onCompare} className="image-viewer__action" title="对比">
              <i className="ph-bold ph-arrows-out-line-horizontal"></i>
            </button>
          )}
          <button
            onClick={() => setIsZoomed(!isZoomed)}
            className="image-viewer__action"
            title={isZoomed ? '缩小' : '放大'}
          >
            <i className={`ph-bold ${isZoomed ? 'ph-arrows-in' : 'ph-arrows-out'}`}></i>
          </button>
        </div>
      </div>

      {/* 图像区域 */}
      <div className={clsx('image-viewer__container', isZoomed && 'image-viewer__container--zoomed')}>
        {isLoading ? (
          <div className="image-viewer__loading">
            <i className="ph-bold ph-spinner animate-spin"></i>
            <span>正在分析图像...</span>
          </div>
        ) : hasImage ? (
          <img
            src={currentSrc}
            alt={showOriginal ? '原始图像' : '分割结果'}
            className="image-viewer__image"
            onClick={() => setIsZoomed(!isZoomed)}
          />
        ) : (
          <div className="image-viewer__empty">
            <i className="ph-bold ph-image-broken"></i>
            <span>暂无图像</span>
          </div>
        )}
      </div>

      {/* 图例 */}
      {!showOriginal && hasImage && !isLoading && (
        <div className="image-viewer__legend">
          <div className="image-viewer__legend-item">
            <span className="image-viewer__legend-color" style={{ background: '#ff0000' }}></span>
            <span>叶片 (Leaf)</span>
          </div>
          <div className="image-viewer__legend-item">
            <span className="image-viewer__legend-color" style={{ background: '#00ff00' }}></span>
            <span>花朵 (Flower)</span>
          </div>
          <div className="image-viewer__legend-item">
            <span className="image-viewer__legend-color" style={{ background: '#969600' }}></span>
            <span>顶芽 (Terminal)</span>
          </div>
          <div className="image-viewer__legend-item">
            <span className="image-viewer__legend-color" style={{ background: '#0000ff' }}></span>
            <span>果实 (Fruit)</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default ImageViewer
