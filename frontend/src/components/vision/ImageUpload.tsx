// ImageUpload - 图像上传组件
import { useCallback, useState } from 'react'
import clsx from 'clsx'

interface ImageUploadProps {
  onUpload: (file: File) => void
  isLoading?: boolean
  accept?: string
  maxSize?: number  // MB
  preview?: string | null
}

export function ImageUpload({
  onUpload,
  isLoading = false,
  accept = 'image/jpeg,image/png,image/jpg',
  maxSize = 20,
  preview = null
}: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFile = useCallback((file: File): boolean => {
    setError(null)

    // 检查文件类型
    const acceptedTypes = accept.split(',').map(t => t.trim())
    if (!acceptedTypes.some(type => file.type === type || file.type.startsWith(type.replace('*', '')))) {
      setError('不支持的文件类型')
      return false
    }

    // 检查文件大小
    if (file.size > maxSize * 1024 * 1024) {
      setError(`文件过大，最大 ${maxSize}MB`)
      return false
    }

    return true
  }, [accept, maxSize])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file && validateFile(file)) {
      onUpload(file)
    }
  }, [onUpload, validateFile])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && validateFile(file)) {
      onUpload(file)
    }
    // Reset input
    e.target.value = ''
  }, [onUpload, validateFile])

  return (
    <div className="image-upload">
      <div
        className={clsx(
          'image-upload__dropzone',
          isDragging && 'image-upload__dropzone--dragging',
          isLoading && 'image-upload__dropzone--loading',
          preview && 'image-upload__dropzone--has-preview'
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {isLoading ? (
          <div className="image-upload__loading">
            <i className="ph-bold ph-spinner animate-spin"></i>
            <span>正在分析...</span>
          </div>
        ) : preview ? (
          <div className="image-upload__preview">
            <img src={preview} alt="Preview" />
            <div className="image-upload__overlay">
              <label className="image-upload__change-btn">
                <i className="ph-bold ph-upload"></i>
                <span>更换图片</span>
                <input
                  type="file"
                  accept={accept}
                  onChange={handleFileSelect}
                  hidden
                />
              </label>
            </div>
          </div>
        ) : (
          <label className="image-upload__content">
            <div className="image-upload__icon">
              <i className="ph-bold ph-image"></i>
            </div>
            <div className="image-upload__text">
              <p className="image-upload__title">拖拽或点击上传图片</p>
              <p className="image-upload__hint">支持 JPG, PNG 格式，最大 {maxSize}MB</p>
            </div>
            <input
              type="file"
              accept={accept}
              onChange={handleFileSelect}
              hidden
            />
          </label>
        )}
      </div>

      {error && (
        <div className="image-upload__error">
          <i className="ph-bold ph-warning-circle"></i>
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}

export default ImageUpload
