// Input - 输入框组件
import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'
import './Input.css'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  icon?: ReactNode
  iconPosition?: 'left' | 'right'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      icon,
      iconPosition = 'left',
      className,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).slice(2, 9)}`

    return (
      <div className={clsx('input-wrapper', error && 'input-wrapper--error', className)}>
        {label && (
          <label htmlFor={inputId} className="input-label">
            {label}
          </label>
        )}
        <div className="input-container">
          {icon && iconPosition === 'left' && (
            <span className="input-icon input-icon--left">{icon}</span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              'input-field',
              icon && iconPosition === 'left' && 'input-field--icon-left',
              icon && iconPosition === 'right' && 'input-field--icon-right'
            )}
            {...props}
          />
          {icon && iconPosition === 'right' && (
            <span className="input-icon input-icon--right">{icon}</span>
          )}
        </div>
        {error && <span className="input-error">{error}</span>}
        {hint && !error && <span className="input-hint">{hint}</span>}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input
