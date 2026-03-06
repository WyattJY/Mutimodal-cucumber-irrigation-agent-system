// OverrideModal - 人工覆盖对话框组件
import { useState } from 'react'

interface OverrideModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (amount: number, reason: string) => void
  currentAmount: number
  date: string
}

export function OverrideModal({ isOpen, onClose, onConfirm, currentAmount, date }: OverrideModalProps) {
  const [amount, setAmount] = useState(currentAmount)
  const [reason, setReason] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async () => {
    if (!reason.trim()) {
      return
    }
    setIsSubmitting(true)
    try {
      await onConfirm(amount, reason)
      onClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const presetReasons = [
    '土壤湿度传感器显示水分充足',
    '天气预报显示即将降雨',
    '作物表现异常，需要调整',
    '设备维护，暂停灌溉',
    '其他原因'
  ]

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="glass-panel modal-content" style={{ maxWidth: '28rem' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              marginBottom: '0.25rem'
            }}>
              <i className="ph-fill ph-hand" style={{ marginRight: '0.5rem', color: 'var(--color-warning)' }}></i>
              人工覆盖决策
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
              {date} - 覆盖 AI 推荐的灌水量
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              padding: '0.5rem',
              borderRadius: '0.5rem',
              transition: 'all 0.2s'
            }}
          >
            <i className="ph-bold ph-x" style={{ fontSize: '1.25rem' }}></i>
          </button>
        </div>

        {/* Current vs Override */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '1rem',
          marginBottom: '1.5rem'
        }}>
          {/* Current */}
          <div style={{
            padding: '1rem',
            background: 'var(--color-surface-hover)',
            borderRadius: '0.75rem',
            border: '1px solid var(--color-border)'
          }}>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
              AI 推荐
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--color-primary)' }}>
              {currentAmount.toFixed(1)} <span style={{ fontSize: '0.875rem', fontWeight: 400 }}>L/m²</span>
            </p>
          </div>

          {/* Override */}
          <div style={{
            padding: '1rem',
            background: 'rgba(253, 214, 99, 0.1)',
            borderRadius: '0.75rem',
            border: '1px solid rgba(253, 214, 99, 0.3)'
          }}>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-warning)', marginBottom: '0.25rem' }}>
              覆盖值
            </p>
            <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--color-warning)' }}>
              {amount.toFixed(1)} <span style={{ fontSize: '0.875rem', fontWeight: 400 }}>L/m²</span>
            </p>
          </div>
        </div>

        {/* Slider */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
            marginBottom: '0.5rem'
          }}>
            调整灌水量
          </label>
          <input
            type="range"
            min="0"
            max="15"
            step="0.1"
            value={amount}
            onChange={(e) => setAmount(parseFloat(e.target.value))}
            style={{
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              background: `linear-gradient(to right, var(--color-warning) 0%, var(--color-warning) ${(amount / 15) * 100}%, var(--color-surface-hover) ${(amount / 15) * 100}%, var(--color-surface-hover) 100%)`,
              appearance: 'none',
              cursor: 'pointer'
            }}
          />
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.75rem',
            color: 'var(--color-text-muted)',
            marginTop: '0.25rem'
          }}>
            <span>0 L/m²</span>
            <span>15 L/m²</span>
          </div>
        </div>

        {/* Quick Presets */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
            marginBottom: '0.5rem'
          }}>
            快速设置
          </label>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {[0, 2, 4, 6, 8, 10].map((preset) => (
              <button
                key={preset}
                onClick={() => setAmount(preset)}
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  background: amount === preset ? 'var(--color-warning)' : 'var(--color-surface-hover)',
                  color: amount === preset ? '#1E1F20' : 'var(--color-text-secondary)',
                  border: '1px solid',
                  borderColor: amount === preset ? 'var(--color-warning)' : 'var(--color-border)',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {preset} L
              </button>
            ))}
          </div>
        </div>

        {/* Reason Selection */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
            marginBottom: '0.5rem'
          }}>
            覆盖原因 <span style={{ color: 'var(--color-danger)' }}>*</span>
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {presetReasons.map((presetReason) => (
              <button
                key={presetReason}
                onClick={() => setReason(presetReason)}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  textAlign: 'left',
                  background: reason === presetReason ? 'rgba(168, 199, 250, 0.15)' : 'var(--color-surface-hover)',
                  color: reason === presetReason ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                  border: '1px solid',
                  borderColor: reason === presetReason ? 'var(--color-primary)' : 'var(--color-border)',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {presetReason}
              </button>
            ))}
          </div>
        </div>

        {/* Custom Reason Input */}
        {reason === '其他原因' && (
          <div style={{ marginBottom: '1.5rem' }}>
            <textarea
              placeholder="请输入具体原因..."
              className="input-field"
              style={{ minHeight: '80px', resize: 'vertical' }}
              onChange={(e) => setReason(e.target.value || '其他原因')}
            />
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={onClose}
            className="btn-secondary"
            style={{ flex: 1, padding: '0.75rem' }}
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={!reason.trim() || isSubmitting}
            style={{
              flex: 1,
              padding: '0.75rem',
              borderRadius: '0.75rem',
              fontWeight: 600,
              background: reason.trim() ? 'var(--color-warning)' : 'var(--color-surface-hover)',
              color: reason.trim() ? '#1E1F20' : 'var(--color-text-muted)',
              border: 'none',
              cursor: reason.trim() ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem'
            }}
          >
            {isSubmitting ? (
              <i className="ph-bold ph-spinner" style={{ animation: 'spin 1s linear infinite' }}></i>
            ) : (
              <>
                <i className="ph-bold ph-check"></i>
                确认覆盖
              </>
            )}
          </button>
        </div>

        {/* Warning */}
        <p style={{
          marginTop: '1rem',
          fontSize: '0.75rem',
          color: 'var(--color-text-muted)',
          textAlign: 'center'
        }}>
          <i className="ph-fill ph-info" style={{ marginRight: '0.25rem' }}></i>
          覆盖操作将被记录并用于模型优化
        </p>
      </div>
    </div>
  )
}

export default OverrideModal
