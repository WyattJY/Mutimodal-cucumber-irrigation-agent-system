// MetricsDisplay - 分割指标显示组件
import clsx from 'clsx'

interface MetricData {
  count: number
  avgMask?: number
  totalMask?: number
  change?: number  // 与昨日变化
}

interface VisionMetrics {
  leaf: MetricData
  flower: MetricData
  terminal: MetricData
  fruit: MetricData
  total_instances?: number
  processed_at?: string
}

interface MetricsDisplayProps {
  metrics: VisionMetrics | null
  isLoading?: boolean
  showChange?: boolean
}

const METRIC_CONFIG = {
  leaf: {
    icon: 'ph-leaf',
    label: '叶片',
    color: '#ff6b6b',
    bgColor: 'rgba(255, 107, 107, 0.1)'
  },
  flower: {
    icon: 'ph-flower',
    label: '花朵',
    color: '#51cf66',
    bgColor: 'rgba(81, 207, 102, 0.1)'
  },
  terminal: {
    icon: 'ph-plant',
    label: '顶芽',
    color: '#fcc419',
    bgColor: 'rgba(252, 196, 25, 0.1)'
  },
  fruit: {
    icon: 'ph-orange-slice',
    label: '果实',
    color: '#339af0',
    bgColor: 'rgba(51, 154, 240, 0.1)'
  }
}

export function MetricsDisplay({ metrics, isLoading = false, showChange = false }: MetricsDisplayProps) {
  if (isLoading) {
    return (
      <div className="metrics-display metrics-display--loading">
        {Object.keys(METRIC_CONFIG).map(key => (
          <div key={key} className="metrics-display__card metrics-display__card--skeleton">
            <div className="skeleton-box" style={{ width: '40px', height: '40px', borderRadius: '50%' }}></div>
            <div className="skeleton-box" style={{ width: '60%', height: '1rem', marginTop: '0.5rem' }}></div>
            <div className="skeleton-box" style={{ width: '40%', height: '1.5rem', marginTop: '0.25rem' }}></div>
          </div>
        ))}
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="metrics-display metrics-display--empty">
        <i className="ph-bold ph-chart-bar"></i>
        <span>暂无指标数据</span>
      </div>
    )
  }

  return (
    <div className="metrics-display">
      {(Object.keys(METRIC_CONFIG) as Array<keyof typeof METRIC_CONFIG>).map(key => {
        const config = METRIC_CONFIG[key]
        const data = metrics[key]
        const change = data?.change

        return (
          <div
            key={key}
            className="metrics-display__card"
            style={{ '--accent-color': config.color, '--accent-bg': config.bgColor } as React.CSSProperties}
          >
            <div className="metrics-display__icon">
              <i className={`ph-bold ${config.icon}`}></i>
            </div>

            <div className="metrics-display__content">
              <span className="metrics-display__label">{config.label}</span>
              <div className="metrics-display__value-row">
                <span className="metrics-display__value">{data?.count ?? 0}</span>
                <span className="metrics-display__unit">个</span>
              </div>

              {showChange && change !== undefined && change !== 0 && (
                <div className={clsx(
                  'metrics-display__change',
                  change > 0 ? 'metrics-display__change--up' : 'metrics-display__change--down'
                )}>
                  <i className={`ph-bold ${change > 0 ? 'ph-arrow-up' : 'ph-arrow-down'}`}></i>
                  <span>{Math.abs(change)}</span>
                </div>
              )}

              {data?.avgMask !== undefined && (
                <div className="metrics-display__sub">
                  <span>平均面积: {Math.round(data.avgMask)}</span>
                </div>
              )}
            </div>
          </div>
        )
      })}

      {/* 总计 */}
      {metrics.total_instances !== undefined && (
        <div className="metrics-display__total">
          <span>总实例数</span>
          <strong>{metrics.total_instances}</strong>
        </div>
      )}
    </div>
  )
}

export default MetricsDisplay
