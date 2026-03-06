// Badge - 状态标签组件
import { forwardRef, type HTMLAttributes } from 'react'
import clsx from 'clsx'
import './Badge.css'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'info' | 'success' | 'warning' | 'danger' | 'neutral'
  size?: 'sm' | 'md'
  dot?: boolean
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'info', size = 'md', dot = false, className, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={clsx(
          'badge',
          `badge--${variant}`,
          `badge--${size}`,
          dot && 'badge--dot',
          className
        )}
        {...props}
      >
        {dot && <span className="badge__dot" />}
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'

export default Badge
