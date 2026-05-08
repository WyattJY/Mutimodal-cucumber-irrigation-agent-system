// Skeleton - 骨架屏组件
import clsx from 'clsx'
import './Skeleton.css'

export interface SkeletonProps {
  variant?: 'text' | 'rectangular' | 'circular'
  width?: string | number
  height?: string | number
  className?: string
  animation?: 'pulse' | 'wave' | 'none'
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  className,
  animation = 'pulse',
}: SkeletonProps) {
  return (
    <div
      className={clsx(
        'skeleton',
        `skeleton--${variant}`,
        `skeleton--${animation}`,
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  )
}

// 预设骨架屏组件
export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="skeleton-text">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === lines - 1 ? '60%' : '100%'}
        />
      ))}
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <Skeleton variant="rectangular" height={120} />
      <div className="skeleton-card__content">
        <Skeleton variant="text" width="70%" />
        <Skeleton variant="text" width="90%" />
        <Skeleton variant="text" width="50%" />
      </div>
    </div>
  )
}

export default Skeleton
