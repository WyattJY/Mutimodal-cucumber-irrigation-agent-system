import { useState } from 'react'
import { useEpisodesQuery } from '@/hooks/useEpisodes'
import { TrendChart } from '@/components/TrendChart'
import type { Episode } from '@/types'

type TabType = 'overview' | 'weekly'
type DateRange = '7d' | '14d' | '30d'

export function History() {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [dateRange, setDateRange] = useState<DateRange>('7d')
  const { data: episodesData, isLoading } = useEpisodesQuery()
  const episodes: Episode[] = episodesData?.items || []

  // Calculate statistics from real data
  const calculateStats = () => {
    if (!episodes || episodes.length === 0) {
      return {
        totalIrrigation: 0,
        avgIrrigation: 0,
        daysCount: 0,
        overrideCount: 0,
        betterDays: 0,
        worseDays: 0
      }
    }

    const daysLimit = dateRange === '7d' ? 7 : dateRange === '14d' ? 14 : 30
    const recentEpisodes = episodes.slice(0, daysLimit)

    const total = recentEpisodes.reduce((sum: number, ep: Episode) => sum + (ep.irrigation_amount || 0), 0)
    const overrides = recentEpisodes.filter((ep: Episode) => ep.decision_source === 'Override').length
    const better = recentEpisodes.filter((ep: Episode) => ep.response?.trend === 'better').length
    const worse = recentEpisodes.filter((ep: Episode) => ep.response?.trend === 'worse').length

    return {
      totalIrrigation: total,
      avgIrrigation: recentEpisodes.length > 0 ? total / recentEpisodes.length : 0,
      daysCount: recentEpisodes.length,
      overrideCount: overrides,
      betterDays: better,
      worseDays: worse
    }
  }

  const stats = calculateStats()

  // Generate DLI data from episodes
  const getDLIData = () => {
    if (!episodes || episodes.length === 0) {
      return [
        { day: 'M', value: 14, status: 'low' as const },
        { day: 'T', value: 18, status: 'optimal' as const },
        { day: 'W', value: 16, status: 'optimal' as const },
        { day: 'T', value: 12, status: 'low' as const },
        { day: 'F', value: 21, status: 'high' as const },
        { day: 'S', value: 19, status: 'optimal' as const },
        { day: 'S', value: 15, status: 'optimal' as const }
      ]
    }

    const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S']
    return episodes.slice(0, 7).map((ep: Episode) => {
      const date = new Date(ep.date)
      const radiation = ep.env_today?.solar_radiation || 15000
      const dli = radiation / 1000 // Simplified DLI calculation
      return {
        day: days[date.getDay()],
        value: Math.round(dli),
        status: dli < 15 ? 'low' as const : dli > 20 ? 'high' as const : 'optimal' as const
      }
    }).reverse()
  }

  const dliData = getDLIData()

  // Generate anomalies from recent episodes
  const getAnomalies = () => {
    const anomalies: { title: string; desc: string; time: string; level: 'critical' | 'warning' | 'info' }[] = []

    if (!episodes || episodes.length === 0) return anomalies

    episodes.slice(0, 10).forEach((ep: Episode) => {
      // High humidity warning
      if (ep.env_today?.humidity && ep.env_today.humidity > 85) {
        anomalies.push({
          title: '湿度过高',
          desc: `检测到湿度 ${ep.env_today.humidity.toFixed(0)}%`,
          time: ep.date,
          level: 'warning'
        })
      }

      // High temperature warning
      if (ep.env_today?.temperature && ep.env_today.temperature > 35) {
        anomalies.push({
          title: '温度过高',
          desc: `检测到温度 ${ep.env_today.temperature.toFixed(1)}°C`,
          time: ep.date,
          level: 'critical'
        })
      }

      // Growth trend warning
      if (ep.response?.trend === 'worse') {
        anomalies.push({
          title: '生长趋势下降',
          desc: `${ep.date} 作物长势变差`,
          time: ep.date,
          level: 'warning'
        })
      }
    })

    return anomalies.slice(0, 5)
  }

  const anomalies = getAnomalies()

  // Weekly data for week selector
  const getWeeklyData = () => {
    const weeks: { range: string; episodes: typeof episodes }[] = []
    if (!episodes) return weeks

    for (let i = 0; i < 4; i++) {
      const endIdx = i * 7
      const startIdx = (i + 1) * 7
      const weekEpisodes = episodes.slice(endIdx, startIdx)

      if (weekEpisodes.length > 0) {
        const startDate = weekEpisodes[weekEpisodes.length - 1]?.date || ''
        const endDate = weekEpisodes[0]?.date || ''
        weeks.push({
          range: `${startDate} ~ ${endDate.slice(5)}`,
          episodes: weekEpisodes
        })
      }
    }

    return weeks
  }

  const weeklyData = getWeeklyData()
  const [selectedWeek, setSelectedWeek] = useState(0)

  // Generate insights from data
  const getInsights = () => {
    const insights: { text: string; type: 'warning' | 'info' | 'alert' }[] = []

    if (stats.worseDays > 0) {
      insights.push({
        text: `过去 ${stats.daysCount} 天中有 ${stats.worseDays} 天长势下降，需要关注`,
        type: stats.worseDays > 2 ? 'alert' : 'warning'
      })
    }

    insights.push({
      text: `灌溉总量 ${stats.totalIrrigation.toFixed(1)} L/m²，日均 ${stats.avgIrrigation.toFixed(2)} L/m²`,
      type: 'info'
    })

    if (stats.overrideCount > 0) {
      insights.push({
        text: `有 ${stats.overrideCount} 次人工覆盖决策，建议分析原因优化模型`,
        type: 'info'
      })
    }

    if (stats.betterDays > stats.daysCount / 2) {
      insights.push({
        text: `超过一半的天数长势良好 (${stats.betterDays}/${stats.daysCount})，灌溉策略有效`,
        type: 'info'
      })
    }

    return insights
  }

  const insights = getInsights()

  if (isLoading) {
    return (
      <div className="chat-container">
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <i className="ph-bold ph-spinner" style={{ fontSize: '2rem', animation: 'spin 1s linear infinite' }}></i>
          <p style={{ marginTop: '1rem', color: 'var(--color-text-secondary)' }}>Loading history data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-container">
      {/* Analytics Header */}
      <div className="analytics-header">
        <div className="analytics-search">
          <i className="ph-fill ph-magic-wand analytics-search__icon"></i>
          <input
            type="text"
            className="analytics-search__input"
            placeholder="询问数据趋势 (例如: '对比上周灌水量与ET0')"
          />
          <span className="analytics-search__shortcut">Ctrl+K</span>
        </div>

        <div className="date-pills">
          <button
            className={`date-pill ${dateRange === '7d' ? 'date-pill--active' : ''}`}
            onClick={() => setDateRange('7d')}
          >
            最近 7 天
          </button>
          <button
            className={`date-pill ${dateRange === '14d' ? 'date-pill--active' : ''}`}
            onClick={() => setDateRange('14d')}
          >
            最近 14 天
          </button>
          <button
            className={`date-pill ${dateRange === '30d' ? 'date-pill--active' : ''}`}
            onClick={() => setDateRange('30d')}
          >
            最近 30 天
          </button>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="chat-messages scrollbar-hide" style={{ paddingBottom: '2rem' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

          {/* Tab Switcher */}
          <div className="analytics-card" style={{ padding: '0.5rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => setActiveTab('overview')}
                className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${
                  activeTab === 'overview'
                    ? 'bg-[#A8C7FA]/20 text-[#A8C7FA] border border-[#A8C7FA]/30'
                    : 'text-[#C4C7C5] hover:text-white hover:bg-white/5'
                }`}
              >
                <i className="ph-bold ph-chart-pie mr-2"></i>
                数据概览
              </button>
              <button
                onClick={() => setActiveTab('weekly')}
                className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${
                  activeTab === 'weekly'
                    ? 'bg-[#A8C7FA]/20 text-[#A8C7FA] border border-[#A8C7FA]/30'
                    : 'text-[#C4C7C5] hover:text-white hover:bg-white/5'
                }`}
              >
                <i className="ph-bold ph-calendar-blank mr-2"></i>
                周度报告
              </button>
            </div>
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <>
              {/* AI Summary Card */}
              <div className="analytics-card ai-summary">
                <div className="ai-summary__gradient-bar"></div>
                <div className="ai-summary__header">
                  <div className="ai-summary__title">
                    <span className="ai-summary__title-text">灌溉洞察</span>
                    <span className="ai-summary__badge">AI 生成</span>
                  </div>
                  <div className="ai-summary__actions">
                    <button className="ai-summary__action">
                      <i className="ph-bold ph-share-network"></i> 分享
                    </button>
                    <button className="ai-summary__action">
                      <i className="ph-bold ph-file-pdf"></i> 导出 PDF
                    </button>
                  </div>
                </div>

                <div className="ai-summary__content">
                  <div className="ai-summary__text">
                    <p>
                      <strong>过去 {stats.daysCount} 天数据分析：</strong>
                      总灌水量 {stats.totalIrrigation.toFixed(1)} L/m²，日均 {stats.avgIrrigation.toFixed(2)} L/m²。
                    </p>
                    <p>
                      {stats.betterDays > 0 && (
                        <><span className="ai-summary__highlight">{stats.betterDays} 天</span>长势良好，</>
                      )}
                      {stats.worseDays > 0 && (
                        <><span className="ai-summary__highlight" style={{ color: '#F28B82' }}>{stats.worseDays} 天</span>长势下降需关注。</>
                      )}
                      {stats.overrideCount > 0 && (
                        <>有 <span className="ai-summary__highlight">{stats.overrideCount} 次</span>人工覆盖操作。</>
                      )}
                    </p>
                  </div>
                  <div className="ai-summary__stat">
                    <div>
                      <div className="ai-summary__stat-label">平均灌水量</div>
                      <div className="ai-summary__stat-value">{stats.avgIrrigation.toFixed(1)} L</div>
                      <div className="ai-summary__stat-note">每日每平方米</div>
                    </div>
                    <div className="ai-summary__stat-icon">
                      <i className="ph-fill ph-drop"></i>
                    </div>
                  </div>
                </div>
              </div>

              {/* Main Chart with TrendChart */}
              <div className="analytics-card chart-section">
                <div className="chart-section__header">
                  <div>
                    <h3 className="chart-section__subtitle">趋势分析</h3>
                    <h2 className="chart-section__title">灌溉量趋势图</h2>
                  </div>
                </div>
                <div className="chart-section__canvas" style={{ height: '300px' }}>
                  <TrendChart
                    days={dateRange === '7d' ? 7 : dateRange === '14d' ? 14 : 30}
                    onDaysChange={(days) => setDateRange(days === 7 ? '7d' : days === 14 ? '14d' : '30d')}
                  />
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="metrics-grid">
                {/* DLI Analysis */}
                <div className="analytics-card metric-card">
                  <h3 className="metric-card__title">日光照积分 (DLI)</h3>
                  <p className="metric-card__subtitle">目标: 15-20 mol/m²/day</p>
                  <div className="metric-card__chart">
                    <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: '100%', padding: '0.5rem 0' }}>
                      {dliData.map((item: {day: string; value: number; status: string}, idx: number) => (
                        <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                          <div
                            style={{
                              width: '24px',
                              borderRadius: '4px',
                              height: `${(item.value / 25) * 100}%`,
                              minHeight: '20px',
                              background: item.status === 'optimal' ? '#6DD58C' : item.status === 'high' ? '#A8C7FA' : '#5E5E5E',
                            }}
                          ></div>
                          <span style={{ fontSize: '0.625rem', color: '#8E918F' }}>{item.day}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="metric-card__footer">
                    <span className="metric-card__footer-label">平均: {(dliData.reduce((s: number, d: {value: number}) => s + d.value, 0) / dliData.length).toFixed(1)}</span>
                    <span className="metric-card__footer-value">
                      {dliData.filter((d: {status: string}) => d.status === 'optimal').length >= 4 ? '最优' : '需改进'}
                    </span>
                  </div>
                </div>

                {/* Stats Summary */}
                <div className="analytics-card metric-card">
                  <h3 className="metric-card__title">数据统计</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1rem 0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: 'var(--color-text-muted)' }}>总灌水量</span>
                      <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>{stats.totalIrrigation.toFixed(1)} L/m²</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: 'var(--color-text-muted)' }}>日均灌水</span>
                      <span style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>{stats.avgIrrigation.toFixed(2)} L/m²</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: 'var(--color-text-muted)' }}>长势良好天数</span>
                      <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{stats.betterDays} 天</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: 'var(--color-text-muted)' }}>人工覆盖次数</span>
                      <span style={{ color: 'var(--color-warning)', fontWeight: 600 }}>{stats.overrideCount} 次</span>
                    </div>
                  </div>
                </div>

                {/* Anomaly Detection */}
                <div className="analytics-card metric-card">
                  <h3 className="metric-card__title" style={{ marginBottom: '1rem' }}>异常检测</h3>
                  <div className="anomaly-list scrollbar-hide">
                    {anomalies.length > 0 ? anomalies.map((item, idx) => (
                      <div key={idx} className="anomaly-item">
                        <div className={`anomaly-item__dot anomaly-item__dot--${item.level}`}></div>
                        <div className="anomaly-item__content">
                          <div className="anomaly-item__title">{item.title}</div>
                          <div className="anomaly-item__desc">{item.desc}</div>
                        </div>
                        <span className="anomaly-item__time">{item.time}</span>
                      </div>
                    )) : (
                      <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', padding: '2rem' }}>
                        <i className="ph-bold ph-check-circle" style={{ fontSize: '2rem', marginBottom: '0.5rem', display: 'block' }}></i>
                        <p>无异常检测</p>
                      </div>
                    )}
                  </div>
                  <button className="anomaly-list__btn">
                    查看系统日志
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Weekly Tab */}
          {activeTab === 'weekly' && (
            <div className="weekly-insights">
              {/* Week Selector */}
              <div className="analytics-card week-selector">
                <h3 className="week-selector__title">
                  <i className="ph-bold ph-calendar-blank"></i>
                  周度报告
                </h3>
                <div className="week-selector__list">
                  {weeklyData.length > 0 ? weeklyData.map((week, i) => (
                    <button
                      key={week.range}
                      onClick={() => setSelectedWeek(i)}
                      className={`week-selector__item ${selectedWeek === i ? 'week-selector__item--active' : ''}`}
                    >
                      <i className="ph-bold ph-calendar"></i>
                      {week.range}
                    </button>
                  )) : (
                    <p style={{ color: 'var(--color-text-muted)', padding: '1rem' }}>暂无周度数据</p>
                  )}
                </div>
              </div>

              {/* Week Detail */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* Stats Row */}
                <div className="stats-row">
                  <div className="analytics-card stat-box">
                    <p className="stat-box__label">总灌水量</p>
                    <p className="stat-box__value">
                      {stats.totalIrrigation.toFixed(1)} <span className="stat-box__unit">L/m²</span>
                    </p>
                  </div>
                  <div className="analytics-card stat-box">
                    <p className="stat-box__label">日均灌水</p>
                    <p className="stat-box__value">
                      {stats.avgIrrigation.toFixed(2)} <span className="stat-box__unit">L/m²</span>
                    </p>
                  </div>
                  <div className="analytics-card stat-box">
                    <p className="stat-box__label">长势评分</p>
                    <p className="stat-box__value stat-box__value--accent">
                      {stats.betterDays >= 5 ? 'A' : stats.betterDays >= 3 ? 'B+' : stats.betterDays >= 2 ? 'B' : 'C'}
                    </p>
                  </div>
                </div>

                {/* Key Insights */}
                <div className="analytics-card" style={{ padding: '1.5rem' }}>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#E3E3E3', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <i className="ph-bold ph-lightbulb" style={{ color: '#FDD663' }}></i>
                    关键洞察
                  </h3>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {insights.map((insight, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '1rem',
                          borderRadius: '0.75rem',
                          border: `1px solid ${
                            insight.type === 'alert'
                              ? 'rgba(242, 139, 130, 0.3)'
                              : insight.type === 'warning'
                                ? 'rgba(253, 214, 99, 0.3)'
                                : 'rgba(255, 255, 255, 0.1)'
                          }`,
                          background:
                            insight.type === 'alert'
                              ? 'rgba(242, 139, 130, 0.1)'
                              : insight.type === 'warning'
                                ? 'rgba(253, 214, 99, 0.1)'
                                : 'rgba(255, 255, 255, 0.03)',
                        }}
                      >
                        <p style={{ color: '#E3E3E3', display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                          <span
                            style={{
                              fontSize: '1.125rem',
                              color:
                                insight.type === 'alert'
                                  ? '#F28B82'
                                  : insight.type === 'warning'
                                    ? '#FDD663'
                                    : '#6DD58C',
                            }}
                          >
                            {insight.type === 'alert' ? (
                              <i className="ph-fill ph-warning-circle"></i>
                            ) : insight.type === 'warning' ? (
                              <i className="ph-fill ph-warning"></i>
                            ) : (
                              <i className="ph-fill ph-info"></i>
                            )}
                          </span>
                          <span>
                            {idx + 1}. {insight.text}
                          </span>
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Trend Chart */}
                <div className="analytics-card chart-section">
                  <div className="chart-section__header">
                    <div>
                      <h3 className="chart-section__subtitle">趋势分析</h3>
                      <h2 className="chart-section__title">周灌溉趋势</h2>
                    </div>
                  </div>
                  <div className="chart-section__canvas" style={{ height: '250px' }}>
                    <TrendChart days={7} />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default History
