// TrendChart - 灌水量趋势图表组件 (使用真实数据)
import { useRef, useState, useEffect, useCallback } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import type { ChartOptions, ChartData } from 'chart.js'
import { Line } from 'react-chartjs-2'

// 注册 Chart.js 组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface TrendDataPoint {
  date: string
  irrigation: number
  trend?: 'better' | 'same' | 'worse'
  source?: 'TSMixer' | 'Override'
}

interface TrendChartProps {
  data?: TrendDataPoint[]
  isLoading?: boolean
  days?: 7 | 14 | 30
  onDaysChange?: (days: 7 | 14 | 30) => void
  animate?: boolean
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export function TrendChart({ data, isLoading: externalLoading, days = 7, onDaysChange, animate = true }: TrendChartProps) {
  const chartRef = useRef<ChartJS<'line'>>(null)
  const [activeTab, setActiveTab] = useState<7 | 14 | 30>(days)
  const [apiData, setApiData] = useState<TrendDataPoint[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [displayIndex, setDisplayIndex] = useState(0)
  const animationRef = useRef<number | null>(null)

  const fetchTrendData = useCallback(async (numDays: number) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/stats/trend?days=${numDays}`)
      const result = await response.json()
      if (result.success && result.data) {
        const { dates, irrigation, trends } = result.data
        const trendData: TrendDataPoint[] = dates.map((date: string, i: number) => ({
          date,
          irrigation: irrigation[i],
          trend: trends[i] || 'same',
          source: 'TSMixer' as const
        }))
        setApiData(trendData)
        if (animate) {
          setDisplayIndex(0)
        } else {
          setDisplayIndex(trendData.length)
        }
      }
    } catch (err) {
      console.error('Failed to fetch trend data:', err)
    } finally {
      setIsLoading(false)
    }
  }, [animate])

  useEffect(() => {
    if (!data || data.length === 0) {
      fetchTrendData(activeTab)
    }
  }, [activeTab, data, fetchTrendData])

  useEffect(() => {
    if (!animate || apiData.length === 0) return
    if (displayIndex >= apiData.length) return
    animationRef.current = window.setTimeout(() => {
      setDisplayIndex(prev => Math.min(prev + 1, apiData.length))
    }, 200)
    return () => {
      if (animationRef.current) clearTimeout(animationRef.current)
    }
  }, [displayIndex, apiData.length, animate])

  const handleTabClick = (newDays: 7 | 14 | 30) => {
    setActiveTab(newDays)
    setDisplayIndex(0)
    onDaysChange?.(newDays)
  }

  const sourceData = data && data.length > 0 ? data : apiData
  const chartData = animate ? sourceData.slice(0, displayIndex) : sourceData

  const lineData: ChartData<'line'> = {
    labels: chartData.map(d => {
      const date = new Date(d.date)
      return `${date.getMonth() + 1}/${date.getDate()}`
    }),
    datasets: [{
      label: '灌水量 (L/m²)',
      data: chartData.map(d => d.irrigation),
      borderColor: '#8AB4F8',
      backgroundColor: 'rgba(138, 180, 248, 0.1)',
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: chartData.map(d => d.source === 'Override' ? 6 : 4),
      pointBackgroundColor: chartData.map(d => d.source === 'Override' ? '#F28B82' : '#8AB4F8'),
      pointBorderColor: chartData.map(d => d.source === 'Override' ? '#F28B82' : '#8AB4F8'),
      pointHoverRadius: 8,
    }]
  }

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1E1F20',
        titleColor: '#E3E3E3',
        bodyColor: '#9AA0A6',
        borderColor: '#3C4043',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          title: (items) => chartData[items[0].dataIndex]?.date || '',
          label: (item) => {
            const point = chartData[item.dataIndex]
            if (!point) return []
            const lines = [`灌水量: ${point.irrigation.toFixed(2)} L/m²`, `来源: ${point.source || 'TSMixer'}`]
            if (point.trend) {
              const trendText = { better: '📈 生长趋势良好', same: '➡️ 生长趋势稳定', worse: '📉 生长趋势下降' }
              lines.push(trendText[point.trend])
            }
            return lines
          }
        }
      }
    },
    scales: {
      x: { grid: { color: 'rgba(60, 64, 67, 0.3)' }, ticks: { color: '#9AA0A6', maxRotation: 0, autoSkip: true, maxTicksLimit: 10 } },
      y: { beginAtZero: true, max: 10, grid: { color: 'rgba(60, 64, 67, 0.3)' }, ticks: { color: '#9AA0A6', callback: (value) => `${value} L` } }
    },
    interaction: { intersect: false, mode: 'index' }
  }

  if (isLoading || externalLoading) {
    return (
      <div className="chart-loading">
        <i className="ph-bold ph-spinner" style={{ animation: 'spin 1s linear infinite' }}></i>
        <p>加载趋势数据...</p>
      </div>
    )
  }

  const dateRange = chartData.length > 0 ? `${chartData[0]?.date} ~ ${chartData[chartData.length - 1]?.date}` : ''

  return (
    <div className="trend-chart">
      <div className="trend-chart__header">
        <div className="trend-chart__legend">
          <span className="trend-chart__legend-item"><span className="trend-chart__dot trend-chart__dot--ai"></span>AI 决策</span>
          <span className="trend-chart__legend-item"><span className="trend-chart__dot trend-chart__dot--override"></span>人工覆盖</span>
          {dateRange && <span className="trend-chart__date-range" style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{dateRange}</span>}
        </div>
        <div className="trend-chart__tabs">
          <button className={`trend-chart__tab ${activeTab === 7 ? 'active' : ''}`} onClick={() => handleTabClick(7)}>7D</button>
          <button className={`trend-chart__tab ${activeTab === 14 ? 'active' : ''}`} onClick={() => handleTabClick(14)}>14D</button>
          <button className={`trend-chart__tab ${activeTab === 30 ? 'active' : ''}`} onClick={() => handleTabClick(30)}>30D</button>
        </div>
      </div>
      <div className="trend-chart__canvas"><Line ref={chartRef} data={lineData} options={options} /></div>
    </div>
  )
}

export default TrendChart
