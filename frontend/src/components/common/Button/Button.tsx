// Button - 通用按钮组件
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'
import './Button.css'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'override'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  icon?: ReactNode
  iconPosition?: 'left' | 'right'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      icon,
      iconPosition = 'left',
      className,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading

    return (
      <button
        ref={ref}
        className={clsx(
          'btn',
          `btn--${variant}`,
          `btn--${size}`,
          loading && 'btn--loading',
          className
        )}
        disabled={isDisabled}
        {...props}
      >
        {loading ? (
          <i className="ph-bold ph-spinner-gap btn__spinner" />
        ) : (
          <>
            {icon && iconPosition === 'left' && (
              <span className="btn__icon btn__icon--left">{icon}</span>
            )}
            {children}
            {icon && iconPosition === 'right' && (
              <span className="btn__icon btn__icon--right">{icon}</span>
            )}
          </>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button
