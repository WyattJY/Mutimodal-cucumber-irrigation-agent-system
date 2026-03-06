import { useState, useEffect } from 'react'
import { useLatestEpisode } from '@/hooks/useEpisodes'
import { usePlantResponse } from '@/hooks/useDailyPredict'
import { imageService } from '@/services/imageService'
import { TrendChart } from '@/components/TrendChart'
import { OverrideModal } from '@/components/OverrideModal'
import { PlantResponseCard } from '@/components/PlantResponseCard'
import { ImageCompare } from '@/components/ImageCompare'
import type { YoloMetrics } from '@/types/episode'

// Transform YoloMetrics to ImageCompare's expected format
const transformYoloMetrics = (yolo: YoloMetrics | undefined) => {
  if (!yolo) return undefined
  return {
    leaf_area: yolo['leaf average mask'] || 0,
    flower_count: yolo['flower Instance Count'] || 0,
    fruit_count: yolo['fruit Mask average'] ? 1 : 0,
    health_score: 0.85, // Default health score
    detection_confidence: 0.9
  }
}

export function DailyDecision() {
  const { data: episode, isLoading, error } = useLatestEpisode()
  const { data: plantResponse, isLoading: isPlantResponseLoading, refetch: refetchPlantResponse } = usePlantResponse(episode?.date || '')
  const [currentTime, setCurrentTime] = useState(new Date())
  const [imageError, setImageError] = useState(false)
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState(false)
  const [showImageCompare, setShowImageCompare] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // 获取日期的短格式 (MMDD)
  const getShortDate = (dateStr: string) => {
    if (!dateStr) return ''
    if (dateStr.includes('-')) {
      const parts = dateStr.split('-')
      return `${parts[1]}${parts[2]}`
    }
    return dateStr
  }

  const getYesterdayDate = (dateStr: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    date.setDate(date.getDate() - 1)
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${month}${day}`
  }

  // 获取趋势信息
  const getTrend = () => {
    const trend = episode?.response?.trend || 'same'
    const trendMap = {
      'better': { icon: 'ph-trend-up', text: 'Better', desc: 'Growth rate +12% vs avg', class: 'step-card--green' },
      'same': { icon: 'ph-minus', text: 'Stable', desc: 'Growth rate stable', class: 'step-card--cyan' },
      'worse': { icon: 'ph-trend-down', text: 'Worse', desc: 'Growth rate -8% vs avg', class: 'step-card--orange' }
    }
    return trendMap[trend as keyof typeof trendMap] || trendMap.same
  }

  // 获取风险等级
  const getRiskLevel = () => {
    const confidence = episode?.response?.confidence || 0.85
    if (confidence >= 0.9) return { level: 'Low Risk', class: 'step-card__badge--cyan', icon: 'ph-check-circle' }
    if (confidence >= 0.7) return { level: 'Medium Risk', class: 'step-card__badge--yellow', icon: 'ph-warning' }
    return { level: 'High Risk', class: 'step-card__badge--red', icon: 'ph-x-circle' }
  }

  const trend = getTrend()
  const risk = getRiskLevel()
  const irrigationAmount = episode?.irrigation_amount ?? 5.2
  const confidence = episode?.response?.confidence ? Math.round(episode.response.confidence * 100) : 94

  // Handle override confirmation
  const handleOverrideConfirm = async (amount: number, reason: string) => {
    console.log('Override:', { amount, reason, date: episode?.date })
    // TODO: Call API to save override
  }

  if (isLoading) {
    return (
      <div className="page-container">
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <i className="ph-bold ph-spinner" style={{ fontSize: '2rem', animation: 'spin 1s linear infinite' }}></i>
          <p style={{ marginTop: '1rem', color: 'var(--color-text-secondary)' }}>Loading decision data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="glass-panel warning-card" style={{ padding: '2rem' }}>
          <i className="ph-fill ph-warning-octagon warning-card__icon"></i>
          <div>
            <h4 className="warning-card__title">Failed to load data</h4>
            <p className="warning-card__desc">{error.message}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container" style={{ paddingBottom: '2rem' }}>
      {/* Page Header */}
      <div className="page-header" style={{ margin: '-1.5rem -2rem 1.5rem', padding: '1rem 2rem' }}>
        <div className="page-header__breadcrumb">
          <span>Dashboards</span>
          <i className="ph ph-caret-right page-header__breadcrumb-sep"></i>
          <span className="page-header__breadcrumb-current">智能灌溉决策</span>
        </div>
        <div className="page-header__right">
          <div className="page-header__status">
            <span className="page-header__status-dot"></span>
            <span className="page-header__status-text">System Normal</span>
          </div>
          <div className="page-header__clock">
            <p className="page-header__time">
              {currentTime.toLocaleTimeString('en-GB', { hour12: false })}
            </p>
            <p className="page-header__date">
              {episode?.date || currentTime.toISOString().split('T')[0]}
            </p>
          </div>
        </div>
      </div>

      {/* Sensor Grid */}
      <div className="sensor-grid">
        {/* Temperature */}
        <div className="glass-panel sensor-card">
          <div className="sensor-card__glow sensor-card__glow--green"></div>
          <div className="sensor-card__header">
            <div>
              <span className="sensor-card__label">Temperature</span>
              <div className="sensor-card__value">
                {episode?.env_today?.temperature?.toFixed(1) ?? '25.0'}<span className="sensor-card__unit">°C</span>
              </div>
            </div>
            <div className="sensor-card__icon sensor-card__icon--green">
              <i className="ph-fill ph-thermometer"></i>
            </div>
          </div>
          <div className="sensor-card__progress">
            <div className="sensor-card__progress-fill sensor-card__progress-fill--green" style={{ width: `${((episode?.env_today?.temperature ?? 25) / 40) * 100}%` }}></div>
          </div>
          <p className="sensor-card__trend sensor-card__trend--neutral">
            {episode?.env_today?.temperature && episode?.env_today?.temperature > 25 ? (
              <><i className="ph-fill ph-trend-up"></i> Above optimal</>
            ) : (
              <><i className="ph-fill ph-check"></i> Optimal range</>
            )}
          </p>
        </div>

        {/* Humidity */}
        <div className="glass-panel sensor-card">
          <div className="sensor-card__glow sensor-card__glow--cyan"></div>
          <div className="sensor-card__header">
            <div>
              <span className="sensor-card__label">Humidity</span>
              <div className="sensor-card__value">
                {episode?.env_today?.humidity?.toFixed(0) ?? '70'}<span className="sensor-card__unit">%</span>
              </div>
            </div>
            <div className="sensor-card__icon sensor-card__icon--cyan">
              <i className="ph-fill ph-drop"></i>
            </div>
          </div>
          <div className="sensor-card__progress">
            <div className="sensor-card__progress-fill sensor-card__progress-fill--cyan" style={{ width: `${episode?.env_today?.humidity ?? 70}%` }}></div>
          </div>
          <p className="sensor-card__trend sensor-card__trend--neutral">
            Optimal Range (65-75%)
          </p>
        </div>

        {/* Light */}
        <div className="glass-panel sensor-card">
          <div className="sensor-card__glow sensor-card__glow--yellow"></div>
          <div className="sensor-card__header">
            <div>
              <span className="sensor-card__label">Solar Radiation</span>
              <div className="sensor-card__value">
                {episode?.env_today?.solar_radiation ? (episode.env_today.solar_radiation / 1000).toFixed(1) : '8.0'}<span className="sensor-card__unit">kW/m²</span>
              </div>
            </div>
            <div className="sensor-card__icon sensor-card__icon--yellow">
              <i className="ph-fill ph-sun"></i>
            </div>
          </div>
          <div className="sensor-card__progress">
            <div className="sensor-card__progress-fill sensor-card__progress-fill--yellow" style={{ width: '60%' }}></div>
          </div>
          <p className="sensor-card__trend sensor-card__trend--neutral">
            Daylight cycle: Peak
          </p>
        </div>
      </div>

      {/* Decision Grid */}
      <div className="decision-grid">
        {/* Left Column: Decision Flow */}
        <div className="decision-flow">
          {/* Step Cards Row */}
          <div className="step-row">
            {/* Plant Response */}
            <div className={`glass-panel step-card ${trend.class}`}>
              <div className="step-card__header">
                <h3 className="step-card__title">Plant Response</h3>
                <span className="step-card__badge step-card__badge--green">STEP 2</span>
              </div>
              <div className="step-card__content">
                <div className="step-card__icon step-card__icon--green" style={{ animation: 'pulse 2s infinite' }}>
                  <i className="ph-fill ph-plant"></i>
                </div>
                <div>
                  <p className="step-card__value">{trend.text}</p>
                  <p className="step-card__desc">{trend.desc}</p>
                </div>
              </div>
            </div>

            {/* Sanity Check */}
            <div className="glass-panel step-card step-card--cyan">
              <div className="step-card__header">
                <h3 className="step-card__title">Sanity Check</h3>
                <span className={`step-card__badge ${risk.class}`}>STEP 4</span>
              </div>
              <div className="step-card__content">
                <div className="step-card__icon step-card__icon--cyan">
                  <i className="ph-fill ph-shield-check"></i>
                </div>
                <div style={{ flex: 1 }}>
                  <p className="step-card__value">{risk.level}</p>
                  <p className="step-card__desc">Confidence: {confidence}%</p>
                </div>
                <i className={`ph-fill ${risk.icon}`} style={{ fontSize: '1.5rem', color: 'rgba(52, 211, 153, 0.5)' }}></i>
              </div>
            </div>
          </div>

          {/* Prediction Card with Chart */}
          <div className="glass-panel prediction-card">
            <div className="prediction-card__header">
              <div>
                <h3 className="prediction-card__title">
                  <i className="ph-fill ph-brain"></i>
                  TSMixer Prediction
                </h3>
                <p className="prediction-card__subtitle">Model Confidence: {confidence}%</p>
              </div>
              <span className="prediction-card__value">
                {irrigationAmount.toFixed(1)} <span className="prediction-card__unit">L/m²</span>
              </span>
            </div>
            <div className="prediction-card__chart" style={{ height: '200px' }}>
              <TrendChart days={7} />
            </div>
          </div>

          {/* Final Decision Card */}
          <div className="final-decision">
            <div className="final-decision__inner">
              <div className="final-decision__glow"></div>
              <div className="final-decision__content">
                <div>
                  <h2 className="final-decision__label">Final Decision</h2>
                  <div className="final-decision__value">
                    <span className="final-decision__number">{irrigationAmount.toFixed(1)}</span>
                    <span className="final-decision__unit">L / m²</span>
                  </div>
                  <div className="final-decision__status">
                    <span className="final-decision__status-dot"></span>
                    <span className="final-decision__status-text">AI Decision • {episode?.date || 'Today'}</span>
                  </div>
                </div>
                <div className="final-decision__actions">
                  <button className="btn--approve">
                    <i className="ph-bold ph-play"></i> Approve Now
                  </button>
                  <button className="btn--manual" onClick={() => setIsOverrideModalOpen(true)}>
                    <i className="ph-bold ph-hand"></i> Manual Override
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="right-panel">
          {/* Live Feed - Real Image */}
          <div className="glass-panel live-feed">
            <div className="live-feed__badge">
              <div className="live-feed__dot"></div>
              <span className="live-feed__badge-text">YOLO Segmentation</span>
            </div>
            <div className="live-feed__image">
              {episode?.date && !imageError ? (
                <img
                  src={imageService.getSegmentedImageUrl(getShortDate(episode.date))}
                  alt="Segmented greenhouse image"
                  onError={() => setImageError(true)}
                />
              ) : (
                <div style={{
                  width: '100%',
                  height: '200px',
                  background: 'var(--color-surface-hover)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '0.5rem'
                }}>
                  <i className="ph-bold ph-image" style={{ fontSize: '2rem', color: 'var(--color-text-muted)' }}></i>
                </div>
              )}
              {episode?.yolo_today && (
                <div className="live-feed__ai-box">
                  <div className="live-feed__ai-label">
                    <i className="ph-fill ph-leaf"></i> {episode.yolo_today['leaf Instance Count'] || 0} leaves
                    {episode.yolo_today['flower Instance Count'] ? (
                      <> | <i className="ph-fill ph-flower-lotus"></i> {episode.yolo_today['flower Instance Count']}</>
                    ) : null}
                  </div>
                </div>
              )}
            </div>
            <div className="live-feed__footer">
              <span className="live-feed__cam">Date: {episode?.date || 'N/A'}</span>
              <span className="live-feed__signal">
                <i className="ph-fill ph-check-circle"></i> Processed
              </span>
            </div>
          </div>

          {/* Agent Insights - Now using PlantResponseCard */}
          <div className="glass-panel insights-card">
            <div className="insights-card__header">
              <h3 className="insights-card__title">
                <i className="ph-fill ph-robot"></i> Agent Insights
              </h3>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <button
                  onClick={() => setShowImageCompare(!showImageCompare)}
                  className="action-chip"
                  style={{ padding: '0.25rem 0.75rem' }}
                >
                  <i className={`ph-bold ${showImageCompare ? 'ph-chart-line' : 'ph-images'}`}></i>
                  <span>{showImageCompare ? '分析' : '对比'}</span>
                </button>
                <span className="insights-card__indicator">
                  <span className="insights-card__indicator-ping"></span>
                  <span className="insights-card__indicator-dot"></span>
                </span>
              </div>
            </div>

            {showImageCompare && episode?.date ? (
              /* Image Compare Mode */
              <div style={{ padding: '1rem' }}>
                <ImageCompare
                  imageYesterday={imageService.getSegmentedImageUrl(getYesterdayDate(episode.date))}
                  imageToday={imageService.getSegmentedImageUrl(getShortDate(episode.date))}
                  yoloYesterday={transformYoloMetrics(episode.yolo_yesterday)}
                  yoloToday={transformYoloMetrics(episode.yolo_today)}
                  mode="side-by-side"
                />
              </div>
            ) : (
              /* PlantResponseCard or Classic Insights */
              <>
                {plantResponse ? (
                  <div style={{ padding: '1rem' }}>
                    <PlantResponseCard
                      response={plantResponse}
                      isLoading={isPlantResponseLoading}
                      onRefresh={() => refetchPlantResponse()}
                    />
                  </div>
                ) : (
                  /* Fallback to classic insights */
                  <>
                  <div className="insights-card__messages scrollbar-hide">
              {/* Growth Insight based on real data */}
              {episode?.yolo_today && (
                <div className="insight-msg">
                  <div className="insight-msg__bubble">
                    <div className="insight-msg__header">
                      <span className="insight-msg__tag insight-msg__tag--growth">Vision</span>
                      <span className="insight-msg__time">{currentTime.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <p className="insight-msg__text">
                      YOLO 检测到 <span className="insight-msg__highlight">{episode.yolo_today['leaf Instance Count'] || 0}</span> 片叶子，
                      平均面积 <span className="insight-msg__highlight">{episode.yolo_today['leaf average mask']?.toFixed(0) || 0} px</span>。
                      {episode.yolo_today['flower Instance Count'] ? (
                        <>检测到 <span className="insight-msg__highlight--green">{episode.yolo_today['flower Instance Count']} 朵花</span>，进入开花期。</>
                      ) : (
                        <>作物处于<span className="insight-msg__highlight--green">营养生长期</span>。</>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* Environment Insight */}
              {episode?.env_today && (
                <div className="insight-msg">
                  <div className="insight-msg__bubble insight-msg__bubble--warning">
                    <div className="insight-msg__header">
                      <span className="insight-msg__tag insight-msg__tag--warning">Environment</span>
                      <span className="insight-msg__time">{currentTime.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <p className="insight-msg__text">
                      当前温度 {episode.env_today.temperature?.toFixed(1)}°C，
                      湿度 {episode.env_today.humidity?.toFixed(0)}%。
                      {episode.env_today.humidity && episode.env_today.humidity > 80 ? (
                        <><i className="ph-fill ph-warning" style={{ color: '#F59E0B', marginRight: '4px' }}></i>湿度偏高，注意通风。</>
                      ) : (
                        <>环境参数在正常范围内。</>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* Irrigation Insight */}
              <div className="insight-msg">
                <div className="insight-msg__bubble insight-msg__bubble--forecast">
                  <div className="insight-msg__header">
                    <span className="insight-msg__tag insight-msg__tag--forecast">Decision</span>
                    <span className="insight-msg__time">{currentTime.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <p className="insight-msg__text">
                    TSMixer 模型推荐灌水量 <span className="insight-msg__highlight">{irrigationAmount.toFixed(1)} L/m²</span>，
                    置信度 {confidence}%。
                    {episode?.response?.reasoning || '基于环境数据和作物生长状态综合分析。'}
                  </p>
                </div>
              </div>
              </div>

            {/* Typing Indicator */}
            <div className="insights-card__typing">
              <span className="insights-card__typing-text">Agri-Copilot analyzing data</span>
              <span className="insights-card__typing-cursor"></span>
            </div>

            {/* Input */}
            <div className="insights-card__input">
              <div className="insights-card__input-wrapper">
                <input
                  type="text"
                  className="insights-card__input-field"
                  placeholder="Ask Agent about crop health..."
                />
                <button className="insights-card__input-btn">
                  <i className="ph-bold ph-paper-plane-right"></i>
                </button>
              </div>
            </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Override Modal */}
      <OverrideModal
        isOpen={isOverrideModalOpen}
        onClose={() => setIsOverrideModalOpen(false)}
        onConfirm={handleOverrideConfirm}
        currentAmount={irrigationAmount}
        date={episode?.date || new Date().toISOString().split('T')[0]}
      />
    </div>
  )
}

export default DailyDecision
