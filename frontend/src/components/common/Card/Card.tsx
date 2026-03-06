// Card - 卡片容器组件
import { forwardRef, type HTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'
import './Card.css'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'glass' | 'solid'
  hover?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
  header?: ReactNode
  footer?: ReactNode
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'glass',
      hover = false,
      padding = 'md',
      header,
      footer,
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'card',
          `card--${variant}`,
          `card--padding-${padding}`,
          hover && 'card--hover',
          className
        )}
        {...props}
      >
        {header && <div className="card__header">{header}</div>}
        <div className="card__body">{children}</div>
        {footer && <div className="card__footer">{footer}</div>}
      </div>
    )
  }
)

Card.displayName = 'Card'

export default Card
