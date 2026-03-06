// Predict - 灌水量预测页面
import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'
import { ImageUpload } from '@/components/vision'
import { EnvDataForm, PredictionResult } from '@/components/prediction'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

interface EnvData {
  temperature: number
  humidity: number
  light: number
  date: string
}

interface Prediction {
  irrigation_amount: number
  unit: string
  confidence?: number
  predicted_at: string
  is_mock?: boolean
}

interface InputSummary {
  temperature: number
  humidity: number
  light: number
  date: string
  leaf_count?: number
  flower_count?: number
  fruit_count?: number
}

interface PredictResult {
  prediction: Prediction
  yolo_metrics: Record<string, any>
  visualization: string | null
  input_summary: InputSummary
}

export function Predict() {
  const [isLoading, setIsLoading] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [result, setResult] = useState<PredictResult | null>(null)
  const [envData, setEnvData] = useState<EnvData>({
    temperature: 25,
    humidity: 70,
    light: 50000,
    date: new Date().toISOString().split('T')[0]
  })

  const handleImageUpload = useCallback((file: File) => {
    setSelectedFile(file)
    const reader = new FileReader()
    reader.onload = () => setPreviewUrl(reader.result as string)
    reader.readAsDataURL(file)
  }, [])

  const handlePredict = useCallback(async (data: EnvData) => {
    setEnvData(data)
    setIsLoading(true)
    setResult(null)

    try {
      if (selectedFile) {
        // 有图片，使用 /predict/with-image
        const formData = new FormData()
        formData.append('file', selectedFile)
        formData.append('temperature', data.temperature.toString())
        formData.append('humidity', data.humidity.toString())
        formData.append('light', data.light.toString())
        formData.append('date', data.date)

        const response = await fetch(`${API_BASE}/predict/with-image`, {
          method: 'POST',
          body: formData
        })

        const responseData = await response.json()

        if (responseData.success) {
          setResult(responseData.data)
          toast.success(`预测完成: ${responseData.data.prediction.irrigation_amount} L/m²`)
        } else {
          throw new Error(responseData.detail || '预测失败')
        }
      } else {
        // 没有图片，使用 /predict (默认 YOLO 指标)
        const response = await fetch(`${API_BASE}/predict/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            env_data: data,
            yolo_metrics: null
          })
        })

        const responseData = await response.json()

        if (responseData.success) {
          setResult({
            prediction: responseData.data.prediction,
            yolo_metrics: {},
            visualization: null,
            input_summary: responseData.data.input_summary
          })
          toast.success(`预测完成: ${responseData.data.prediction.irrigation_amount} L/m²`)
        } else {
          throw new Error(responseData.detail || '预测失败')
        }
      }
    } catch (error) {
      console.error('Prediction failed:', error)
      toast.error('预测失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }, [selectedFile])

  return (
    <div className="predict-page">
      {/* 页面头部 */}
      <header className="predict-page__header">
        <div className="predict-page__title-section">
          <h1 className="predict-page__title">
            <i className="ph-bold ph-lightning"></i>
            灌水量预测
          </h1>
          <p className="predict-page__desc">
            基于 TSMixer 时序模型 + YOLO 视觉特征的智能灌水决策
          </p>
        </div>
      </header>

      {/* 主内容区 */}
      <div className="predict-page__content">
        {/* 左侧 - 输入区 */}
        <div className="predict-page__input-section">
          {/* 图像上传 */}
          <div className="predict-page__card">
            <h3 className="predict-page__card-title">
              <i className="ph-bold ph-image"></i>
              植株图像 (可选)
            </h3>
            <ImageUpload
              onUpload={handleImageUpload}
              isLoading={isLoading}
              preview={previewUrl}
            />
            <p className="predict-page__hint">
              上传植株图片可自动提取视觉特征，提高预测精度
            </p>
          </div>

          {/* 环境数据 */}
          <div className="predict-page__card">
            <EnvDataForm
              onSubmit={handlePredict}
              isLoading={isLoading}
              defaultValues={envData}
            />
          </div>
        </div>

        {/* 右侧 - 结果区 */}
        <div className="predict-page__result-section">
          {/* 预测结果 */}
          <div className="predict-page__card predict-page__card--result">
            <h3 className="predict-page__card-title">
              <i className="ph-bold ph-drop"></i>
              预测结果
            </h3>
            <PredictionResult
              prediction={result?.prediction || null}
              inputSummary={result?.input_summary || null}
              isLoading={isLoading}
            />
          </div>

          {/* 分割可视化 (如果有) */}
          {result?.visualization && (
            <div className="predict-page__card">
              <h3 className="predict-page__card-title">
                <i className="ph-bold ph-scan"></i>
                视觉分析结果
              </h3>
              <div className="predict-page__visualization">
                <img
                  src={`data:image/jpeg;base64,${result.visualization}`}
                  alt="分割结果"
                />
              </div>

              {/* YOLO 指标 */}
              {result.yolo_metrics && (
                <div className="predict-page__yolo-metrics">
                  <div className="predict-page__metric">
                    <span>叶片</span>
                    <strong>{result.yolo_metrics.leaf_instance_count || 0} 个</strong>
                  </div>
                  <div className="predict-page__metric">
                    <span>花朵</span>
                    <strong>{result.yolo_metrics.flower_instance_count || 0} 个</strong>
                  </div>
                  <div className="predict-page__metric">
                    <span>果实</span>
                    <strong>{result.yolo_metrics.fruit_instance_count || 0} 个</strong>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 模型说明 */}
          <div className="predict-page__card predict-page__card--info">
            <h4>模型说明</h4>
            <ul>
              <li>使用 TSMixer 时序混合模型</li>
              <li>基于 96 天历史数据预测</li>
              <li>融合 11 维特征 (3 环境 + 8 视觉)</li>
              <li>使用 FAO56 作物需水量知识验证</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Predict
