// PredictionResult - 预测结果展示组件
import clsx from 'clsx'

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

interface PredictionResultProps {
  prediction: Prediction | null
  inputSummary?: InputSummary | null
  isLoading?: boolean
}

export function PredictionResult({ prediction, inputSummary, isLoading = false }: PredictionResultProps) {
  if (isLoading) {
    return (
      <div className="prediction-result prediction-result--loading">
        <div className="prediction-result__loader">
          <i className="ph-bold ph-spinner animate-spin"></i>
          <span>正在预测...</span>
        </div>
      </div>
    )
  }

  if (!prediction) {
    return (
      <div className="prediction-result prediction-result--empty">
        <div className="prediction-result__empty-icon">
          <i className="ph-bold ph-drop"></i>
        </div>
        <h3>等待预测</h3>
        <p>上传图片并填写环境数据后点击"开始预测"</p>
      </div>
    )
  }

  // 根据灌水量确定等级
  const getIrrigationLevel = (amount: number) => {
    if (amount < 2) return { level: '低', color: 'success' }
    if (amount < 3.5) return { level: '适中', color: 'primary' }
    if (amount < 5) return { level: '较高', color: 'warning' }
    return { level: '高', color: 'danger' }
  }

  const { level, color } = getIrrigationLevel(prediction.irrigation_amount)

  return (
    <div className="prediction-result">
      {/* 主要结果 */}
      <div className={clsx('prediction-result__main', `prediction-result__main--${color}`)}>
        <div className="prediction-result__icon">
          <i className="ph-bold ph-drop"></i>
        </div>
        <div className="prediction-result__value">
          <span className="prediction-result__amount">{prediction.irrigation_amount}</span>
          <span className="prediction-result__unit">{prediction.unit}</span>
        </div>
        <div className="prediction-result__level">
          <span className={`prediction-result__badge prediction-result__badge--${color}`}>
            {level}
          </span>
        </div>
      </div>

      {/* 置信度 */}
      {prediction.confidence && (
        <div className="prediction-result__confidence">
          <span className="prediction-result__confidence-label">预测置信度</span>
          <div className="prediction-result__confidence-bar">
            <div
              className="prediction-result__confidence-fill"
              style={{ width: `${prediction.confidence * 100}%` }}
            />
          </div>
          <span className="prediction-result__confidence-value">
            {Math.round(prediction.confidence * 100)}%
          </span>
        </div>
      )}

      {/* 输入摘要 */}
      {inputSummary && (
        <div className="prediction-result__summary">
          <h4>输入数据摘要</h4>
          <div className="prediction-result__summary-grid">
            <div className="prediction-result__summary-item">
              <i className="ph-bold ph-thermometer"></i>
              <span>{inputSummary.temperature}°C</span>
            </div>
            <div className="prediction-result__summary-item">
              <i className="ph-bold ph-drop"></i>
              <span>{inputSummary.humidity}%</span>
            </div>
            <div className="prediction-result__summary-item">
              <i className="ph-bold ph-sun"></i>
              <span>{inputSummary.light} lux</span>
            </div>
            {inputSummary.leaf_count !== undefined && (
              <div className="prediction-result__summary-item">
                <i className="ph-bold ph-leaf"></i>
                <span>{inputSummary.leaf_count} 叶</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 时间戳 */}
      <div className="prediction-result__timestamp">
        <i className="ph-bold ph-clock"></i>
        <span>预测时间: {new Date(prediction.predicted_at).toLocaleString()}</span>
      </div>

      {/* Mock 警告 */}
      {prediction.is_mock && (
        <div className="prediction-result__mock-notice">
          <i className="ph-bold ph-warning"></i>
          <span>当前为模拟数据，模型可能未正确加载</span>
        </div>
      )}
    </div>
  )
}

export default PredictionResult
