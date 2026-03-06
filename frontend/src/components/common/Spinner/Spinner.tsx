// Spinner - 加载动画组件
import clsx from 'clsx'
import './Spinner.css'

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  color?: 'primary' | 'white' | 'inherit'
  className?: string
}

export function Spinner({ size = 'md', color = 'primary', className }: SpinnerProps) {
  return (
    <div className={clsx('spinner', `spinner--${size}`, `spinner--${color}`, className)}>
      <i className="ph-bold ph-spinner-gap" />
    </div>
  )
}

export default Spinner
