import { useState } from 'react'
import { useEpisodesQuery } from '@/hooks/useEpisodes'
import { TrendChart } from '@/components/TrendChart'
import type { Episode } from '@/types'

interface WeekData {
  range: string
  startDate: string
  endDate: string
  totalIrrigation: number
  avgIrrigation: number
  betterDays: number
  worseDays: number
  sameDays: number
  overrideCount: number
}

export function Weekly() {
  const { data: episodesData, isLoading } = useEpisodesQuery()
  const episodes: Episode[] = episodesData?.items || []
  const [selectedWeekIdx, setSelectedWeekIdx] = useState(0)

  // Generate weekly data from episodes
  const getWeeklyData = (): WeekData[] => {
    if (!episodes || episodes.length === 0) {
      return []
    }

    const weeks: WeekData[] = []

    for (let i = 0; i < 4; i++) {
      const startIdx = i * 7
      const endIdx = (i + 1) * 7
      const weekEpisodes = episodes.slice(startIdx, endIdx)

      if (weekEpisodes.length === 0) continue

      const startDate = weekEpisodes[weekEpisodes.length - 1]?.date || ''
      const endDate = weekEpisodes[0]?.date || ''

      const total = weekEpisodes.reduce((sum: number, ep: Episode) => sum + (ep.irrigation_amount || 0), 0)
      const better = weekEpisodes.filter((ep: Episode) => ep.response?.trend === 'better').length
      const worse = weekEpisodes.filter((ep: Episode) => ep.response?.trend === 'worse').length
      const same = weekEpisodes.filter((ep: Episode) => ep.response?.trend === 'same').length
      const overrides = weekEpisodes.filter((ep: Episode) => ep.decision_source === 'Override').length

      weeks.push({
        range: `${startDate} ~ ${endDate.slice(5)}`,
        startDate,
        endDate,
        totalIrrigation: total,
        avgIrrigation: weekEpisodes.length > 0 ? total / weekEpisodes.length : 0,
        betterDays: better,
        worseDays: worse,
        sameDays: same,
        overrideCount: overrides
      })
    }

    return weeks
  }

  const weeklyData = getWeeklyData()
  const selectedWeek = weeklyData[selectedWeekIdx] || null

  // Generate insights for selected week
  const getInsights = (): { text: string; type: 'success' | 'warning' | 'danger' | 'info' }[] => {
    if (!selectedWeek) return []

    const insights: { text: string; type: 'success' | 'warning' | 'danger' | 'info' }[] = []

    // Growth trend insight
    if (selectedWeek.betterDays > selectedWeek.worseDays) {
      insights.push({
        text: `本周长势良好 (${selectedWeek.betterDays} 天好转，${selectedWeek.worseDays} 天下降)`,
        type: 'success'
      })
    } else if (selectedWeek.worseDays > selectedWeek.betterDays) {
      insights.push({
        text: `本周长势需关注 (${selectedWeek.worseDays} 天下降，${selectedWeek.betterDays} 天好转)`,
        type: 'warning'
      })
    } else {
      insights.push({
        text: `本周长势平稳 (${selectedWeek.sameDays} 天保持稳定)`,
        type: 'info'
      })
    }

    // Irrigation insight
    insights.push({
      text: `灌溉总量 ${selectedWeek.totalIrrigation.toFixed(1)} L/m²，日均 ${selectedWeek.avgIrrigation.toFixed(2)} L/m²`,
      type: 'info'
    })

    // High irrigation warning
    if (selectedWeek.avgIrrigation > 8) {
      insights.push({
        text: `日均灌水量偏高 (${selectedWeek.avgIrrigation.toFixed(2)} L/m²)，建议检查蒸发量和土壤湿度`,
        type: 'warning'
      })
    } else if (selectedWeek.avgIrrigation < 4) {
      insights.push({
        text: `日均灌水量偏低 (${selectedWeek.avgIrrigation.toFixed(2)} L/m²)，注意防止水分胁迫`,
        type: 'warning'
      })
    }

    // Override insight
    if (selectedWeek.overrideCount > 0) {
      insights.push({
        text: `有 ${selectedWeek.overrideCount} 次人工覆盖决策，建议分析原因以优化模型`,
        type: 'info'
      })
    }

    return insights
  }

  const insights = getInsights()

  // Calculate grade based on performance
  const getGrade = (): string => {
    if (!selectedWeek) return '-'
    const score = selectedWeek.betterDays * 2 + selectedWeek.sameDays - selectedWeek.worseDays * 2
    if (score >= 8) return 'A'
    if (score >= 5) return 'A-'
    if (score >= 3) return 'B+'
    if (score >= 1) return 'B'
    if (score >= -1) return 'B-'
    if (score >= -3) return 'C+'
    return 'C'
  }

  if (isLoading) {
    return (
      <div className="page-container">
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <i className="ph-bold ph-spinner" style={{ fontSize: '2rem', animation: 'spin 1s linear infinite' }}></i>
          <p style={{ marginTop: '1rem', color: 'var(--color-text-secondary)' }}>Loading weekly data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container" style={{ paddingBottom: '2rem' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{
          fontSize: '1.75rem',
          fontWeight: 700,
          color: 'var(--color-text-primary)',
          marginBottom: '0.5rem'
        }}>
          <i className="ph-bold ph-calendar-check" style={{ marginRight: '0.75rem', color: 'var(--color-primary)' }}></i>
          周度分析
        </h1>
        <p style={{ color: 'var(--color-text-muted)' }}>
          查看每周总结报告和关键洞察
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
        {/* Week List */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{
            fontSize: '1rem',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <i className="ph-bold ph-list-bullets"></i>
            周度报告列表
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {weeklyData.length > 0 ? weeklyData.map((week, i) => (
              <button
                key={week.range}
                onClick={() => setSelectedWeekIdx(i)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '0.875rem 1rem',
                  borderRadius: '0.75rem',
                  transition: 'all 0.2s',
                  background: selectedWeekIdx === i ? 'rgba(168, 199, 250, 0.15)' : 'transparent',
                  color: selectedWeekIdx === i ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                  border: selectedWeekIdx === i ? '1px solid rgba(168, 199, 250, 0.3)' : '1px solid transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                <i className="ph-bold ph-calendar"></i>
                {week.range}
                {i === 0 && (
                  <span style={{
                    marginLeft: 'auto',
                    fontSize: '0.625rem',
                    padding: '0.125rem 0.375rem',
                    borderRadius: '0.25rem',
                    background: 'var(--color-success)',
                    color: '#1E1F20'
                  }}>
                    本周
                  </span>
                )}
              </button>
            )) : (
              <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '2rem' }}>
                暂无周度数据
              </p>
            )}
          </div>
        </div>

        {/* Week Detail */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {selectedWeek ? (
            <>
              {/* Stats Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                <div className="glass-panel" style={{ padding: '1rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                    总灌水量
                  </p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-primary)' }}>
                    {selectedWeek.totalIrrigation.toFixed(1)}
                  </p>
                  <p style={{ fontSize: '0.625rem', color: 'var(--color-text-muted)' }}>L/m²</p>
                </div>

                <div className="glass-panel" style={{ padding: '1rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                    日均灌水
                  </p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                    {selectedWeek.avgIrrigation.toFixed(2)}
                  </p>
                  <p style={{ fontSize: '0.625rem', color: 'var(--color-text-muted)' }}>L/m²</p>
                </div>

                <div className="glass-panel" style={{ padding: '1rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                    长势评分
                  </p>
                  <p style={{
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    color: getGrade().startsWith('A') ? 'var(--color-success)' :
                           getGrade().startsWith('B') ? 'var(--color-warning)' : 'var(--color-danger)'
                  }}>
                    {getGrade()}
                  </p>
                  <p style={{ fontSize: '0.625rem', color: 'var(--color-text-muted)' }}>综合评估</p>
                </div>

                <div className="glass-panel" style={{ padding: '1rem', textAlign: 'center' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
                    人工覆盖
                  </p>
                  <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-warning)' }}>
                    {selectedWeek.overrideCount}
                  </p>
                  <p style={{ fontSize: '0.625rem', color: 'var(--color-text-muted)' }}>次</p>
                </div>
              </div>

              {/* Growth Trend Summary */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <h3 style={{
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  marginBottom: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <i className="ph-bold ph-plant" style={{ color: 'var(--color-success)' }}></i>
                  长势分布
                </h3>

                <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
                  {/* Progress Bar */}
                  <div style={{ flex: 1 }}>
                    <div style={{
                      display: 'flex',
                      height: '24px',
                      borderRadius: '12px',
                      overflow: 'hidden',
                      background: 'var(--color-surface-hover)'
                    }}>
                      <div style={{
                        width: `${(selectedWeek.betterDays / 7) * 100}%`,
                        background: 'var(--color-success)',
                        transition: 'width 0.3s'
                      }}></div>
                      <div style={{
                        width: `${(selectedWeek.sameDays / 7) * 100}%`,
                        background: 'var(--color-primary)',
                        transition: 'width 0.3s'
                      }}></div>
                      <div style={{
                        width: `${(selectedWeek.worseDays / 7) * 100}%`,
                        background: 'var(--color-danger)',
                        transition: 'width 0.3s'
                      }}></div>
                    </div>
                  </div>

                  {/* Legend */}
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--color-text-secondary)' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-success)' }}></span>
                      好转 {selectedWeek.betterDays}天
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--color-text-secondary)' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-primary)' }}></span>
                      稳定 {selectedWeek.sameDays}天
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--color-text-secondary)' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-danger)' }}></span>
                      下降 {selectedWeek.worseDays}天
                    </span>
                  </div>
                </div>
              </div>

              {/* Insights */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <h3 style={{
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  marginBottom: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <i className="ph-bold ph-lightbulb" style={{ color: 'var(--color-warning)' }}></i>
                  关键洞察
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {insights.map((insight, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '0.875rem 1rem',
                        borderRadius: '0.5rem',
                        background: insight.type === 'success' ? 'rgba(109, 213, 140, 0.1)' :
                                    insight.type === 'warning' ? 'rgba(253, 214, 99, 0.1)' :
                                    insight.type === 'danger' ? 'rgba(242, 139, 130, 0.1)' :
                                    'rgba(168, 199, 250, 0.1)',
                        border: `1px solid ${
                          insight.type === 'success' ? 'rgba(109, 213, 140, 0.25)' :
                          insight.type === 'warning' ? 'rgba(253, 214, 99, 0.25)' :
                          insight.type === 'danger' ? 'rgba(242, 139, 130, 0.25)' :
                          'rgba(168, 199, 250, 0.25)'
                        }`,
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.75rem'
                      }}
                    >
                      <i className={`ph-fill ${
                        insight.type === 'success' ? 'ph-check-circle' :
                        insight.type === 'warning' ? 'ph-warning' :
                        insight.type === 'danger' ? 'ph-warning-circle' :
                        'ph-info'
                      }`} style={{
                        color: insight.type === 'success' ? 'var(--color-success)' :
                               insight.type === 'warning' ? 'var(--color-warning)' :
                               insight.type === 'danger' ? 'var(--color-danger)' :
                               'var(--color-primary)',
                        fontSize: '1.125rem',
                        marginTop: '2px'
                      }}></i>
                      <span style={{ color: 'var(--color-text-primary)' }}>
                        {idx + 1}. {insight.text}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Trend Chart */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <h3 style={{
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  marginBottom: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <i className="ph-bold ph-chart-line-up" style={{ color: 'var(--color-primary)' }}></i>
                  周灌溉趋势
                </h3>
                <div style={{ height: '200px' }}>
                  <TrendChart days={7} />
                </div>
              </div>
            </>
          ) : (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
              <i className="ph-bold ph-calendar-x" style={{ fontSize: '3rem', color: 'var(--color-text-muted)', marginBottom: '1rem', display: 'block' }}></i>
              <p style={{ color: 'var(--color-text-muted)' }}>请选择一个周度报告查看详情</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Weekly
