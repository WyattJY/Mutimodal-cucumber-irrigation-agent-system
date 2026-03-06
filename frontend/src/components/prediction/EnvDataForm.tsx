// EnvDataForm - 环境数据输入表单
import { useState } from 'react'

interface EnvData {
  temperature: number
  humidity: number
  light: number
  date: string
}

interface EnvDataFormProps {
  onSubmit: (data: EnvData) => void
  isLoading?: boolean
  defaultValues?: Partial<EnvData>
}

export function EnvDataForm({ onSubmit, isLoading = false, defaultValues }: EnvDataFormProps) {
  const today = new Date().toISOString().split('T')[0]

  const [formData, setFormData] = useState<EnvData>({
    temperature: defaultValues?.temperature ?? 25,
    humidity: defaultValues?.humidity ?? 70,
    light: defaultValues?.light ?? 50000,
    date: defaultValues?.date ?? today
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (field: keyof EnvData, value: number | string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <form className="env-form" onSubmit={handleSubmit}>
      <h3 className="env-form__title">
        <i className="ph-bold ph-thermometer"></i>
        环境数据
      </h3>

      {/* 温度 */}
      <div className="env-form__field">
        <label className="env-form__label">
          <i className="ph-bold ph-thermometer-hot"></i>
          日均温度 (°C)
        </label>
        <div className="env-form__slider-wrapper">
          <input
            type="range"
            min="15"
            max="35"
            step="0.5"
            value={formData.temperature}
            onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
            className="env-form__slider"
          />
          <span className="env-form__value">{formData.temperature}°C</span>
        </div>
        <div className="env-form__range">
          <span>15°C</span>
          <span>35°C</span>
        </div>
      </div>

      {/* 湿度 */}
      <div className="env-form__field">
        <label className="env-form__label">
          <i className="ph-bold ph-drop"></i>
          日均湿度 (%)
        </label>
        <div className="env-form__slider-wrapper">
          <input
            type="range"
            min="40"
            max="95"
            step="1"
            value={formData.humidity}
            onChange={(e) => handleChange('humidity', parseFloat(e.target.value))}
            className="env-form__slider"
          />
          <span className="env-form__value">{formData.humidity}%</span>
        </div>
        <div className="env-form__range">
          <span>40%</span>
          <span>95%</span>
        </div>
      </div>

      {/* 光照 */}
      <div className="env-form__field">
        <label className="env-form__label">
          <i className="ph-bold ph-sun"></i>
          日均光照 (lux)
        </label>
        <div className="env-form__input-wrapper">
          <input
            type="number"
            min="0"
            max="100000"
            step="1000"
            value={formData.light}
            onChange={(e) => handleChange('light', parseFloat(e.target.value))}
            className="env-form__input"
          />
          <span className="env-form__unit">lux</span>
        </div>
      </div>

      {/* 日期 */}
      <div className="env-form__field">
        <label className="env-form__label">
          <i className="ph-bold ph-calendar"></i>
          预测日期
        </label>
        <input
          type="date"
          value={formData.date}
          onChange={(e) => handleChange('date', e.target.value)}
          className="env-form__date"
        />
      </div>

      {/* 提交按钮 */}
      <button
        type="submit"
        disabled={isLoading}
        className="env-form__submit"
      >
        {isLoading ? (
          <>
            <i className="ph-bold ph-spinner animate-spin"></i>
            预测中...
          </>
        ) : (
          <>
            <i className="ph-bold ph-lightning"></i>
            开始预测
          </>
        )}
      </button>
    </form>
  )
}

export default EnvDataForm
