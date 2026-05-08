// Image Service - 图像相关 API
import { apiClient } from './api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export interface ImageInfo {
  filename: string
  date: string
  size: number
  has_segmentation: boolean
  has_metrics: boolean
}

export interface YoloMetrics {
  'leaf Instance Count': number
  'leaf average mask': number
  'flower Instance Count': number
  'flower average mask': number
  'fruit Instance Count': number
  'fruit average mask': number
  'other Instance Count': number
  processed_at: string
  visualization_path?: string
  is_mock?: boolean
}

export interface UploadResponse {
  filename: string
  path: string
  date: string
  size: number
  yolo_metrics?: YoloMetrics
  segmented_image?: string
  yolo_error?: string
}

export const imageService = {
  /**
   * 获取原始图像 URL
   */
  getOriginalImageUrl(date: string): string {
    const shortDate = date.includes('-')
      ? date.split('-').slice(1).join('')
      : date
    return `${API_BASE}/vision/image/${shortDate}?original=true`
  },

  /**
   * 获取分割后图像 URL
   */
  getSegmentedImageUrl(date: string): string {
    const shortDate = date.includes('-')
      ? date.split('-').slice(1).join('')
      : date
    return `${API_BASE}/vision/image/${shortDate}`
  },

  /**
   * 获取图像的 YOLO 指标
   */
  async getMetrics(date: string): Promise<YoloMetrics> {
    const shortDate = date.includes('-')
      ? date.split('-').slice(1).join('')
      : date
    const response = await apiClient.get(`/upload/images/${shortDate}/metrics`)
    return response.data.data
  },

  /**
   * 列出所有图像
   */
  async listImages(): Promise<{ images: ImageInfo[], total: number }> {
    const response = await apiClient.get('/upload/images')
    return response.data.data
  },

  /**
   * 上传图像
   */
  async uploadImage(file: File, date: string, processYolo: boolean = true): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('date', date)
    formData.append('process_yolo', String(processYolo))

    const response = await apiClient.post('/upload/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data.data
  },

  /**
   * 上传环境数据 CSV
   */
  async uploadEnvData(file: File): Promise<{ rows: number, columns: string[], date_range: { start: string, end: string } }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/upload/env', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data.data
  },

  /**
   * 触发 YOLO 处理
   */
  async processImage(date: string): Promise<YoloMetrics> {
    const shortDate = date.includes('-')
      ? date.split('-').slice(1).join('')
      : date
    const response = await apiClient.post(`/upload/process/${shortDate}`)
    return response.data.data
  },

  /**
   * 批量处理所有图像
   */
  async batchProcess(): Promise<{ processed: number, success: number, failed: number }> {
    const response = await apiClient.post('/upload/batch-process')
    return response.data.data
  },

  /**
   * 检查图像是否存在
   */
  async checkImageExists(date: string): Promise<boolean> {
    try {
      const shortDate = date.includes('-')
        ? date.split('-').slice(1).join('')
        : date
      await apiClient.head(`/vision/image/${shortDate}?original=true`)
      return true
    } catch {
      return false
    }
  }
}
