import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLatestEpisode } from '@/hooks/useEpisodes'
import { imageService } from '@/services/imageService'
import { TrendChart } from '@/components/TrendChart'
import { OverrideModal } from '@/components/OverrideModal'

export function Dashboard() {
  const navigate = useNavigate()
  const { data: episode, isLoading, error } = useLatestEpisode()
  const [imageError, setImageError] = useState<Record<string, boolean>>({})
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState(false)

  // 获取日期的短格式 (MMDD)
  const getShortDate = (dateStr: string) => {
    if (!dateStr) return ''
    if (dateStr.includes('-')) {
      const parts = dateStr.split('-')
      return `${parts[1]}${parts[2]}`
    }
    return dateStr
  }

  // 获取昨日日期
  const getYesterdayDate = (dateStr: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    date.setDate(date.getDate() - 1)
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${month}${day}`
  }

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    return {
      date: dateStr,
      day: days[date.getDay()]
    }
  }

  // Get growth stage from response
  const getGrowthStage = () => {
    if (!episode?.response) return '营养生长期 (Vegetative)'
    const stage = episode.response.growth_stage
    const stageMap: Record<string, string> = {
      'seedling': '苗期 (Seedling)',
      'vegetative': '营养生长期 (Vegetative)',
      'flowering': '开花期 (Flowering)',
      'fruiting': '结果期 (Fruiting)',
      'harvest': '采收期 (Harvest)'
    }
    return stageMap[stage] || stage
  }

  // Calculate irrigation amount
  const getIrrigationAmount = () => {
    return episode?.irrigation_amount ?? 5.2
  }

  // Get trend icon and text
  const getTrend = () => {
    const trend = episode?.response?.trend || 'same'
    const trendMap = {
      'better': { icon: 'ph-trend-up', text: 'Better', class: 'stat-pill__icon--green' },
      'same': { icon: 'ph-minus', text: 'Stable', class: 'stat-pill__icon--blue' },
      'worse': { icon: 'ph-trend-down', text: 'Worse', class: 'stat-pill__icon--red' }
    }
    return trendMap[trend as keyof typeof trendMap] || trendMap.same
  }

  const dateInfo = episode ? formatDate(episode.date) : { date: new Date().toISOString().split('T')[0], day: 'Today' }
  const trend = getTrend()

  // Handle override confirmation
  const handleOverrideConfirm = async (amount: number, reason: string) => {
    console.log('Override:', { amount, reason, date: episode?.date })
    // TODO: Call API to save override
    // await episodeService.saveOverride(episode?.date, amount, reason)
  }

  if (isLoading) {
    return (
      <div className="page-container">
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
          <i className="ph-bold ph-spinner" style={{ fontSize: '2rem', animation: 'spin 1s linear infinite' }}></i>
          <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Loading latest episode...</p>
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
    <div className="page-container">
      {/* Top Bar */}
      <div className="top-bar">
        <div>
          <div className="top-bar__status">
            <span className="status-badge">● LIVE</span>
            <span className="status-text">SYSTEM: ONLINE</span>
          </div>
          <h1 className="top-bar__title">
            {dateInfo.date}
            <span className="top-bar__title-day">{dateInfo.day}</span>
          </h1>
          <p className="top-bar__meta">
            <i className="ph-fill ph-map-pin"></i> Greenhouse Alpha
            <span className="top-bar__divider">|</span>
            <span className="top-bar__growth">
              <i className="ph-fill ph-leaf"></i> {getGrowthStage()}
            </span>
          </p>
        </div>

        {/* Environment Capsules */}
        <div className="env-capsules">
          <div className="glass-panel env-capsule">
            <i className="ph-fill ph-thermometer env-capsule__icon env-capsule__icon--temp"></i>
            <div>
              <span className="env-capsule__label">Temp</span>
              <span className="env-capsule__value">{episode?.env_today?.temperature ?? 25}°C</span>
            </div>
          </div>
          <div className="glass-panel env-capsule">
            <i className="ph-fill ph-drop env-capsule__icon env-capsule__icon--humidity"></i>
            <div>
              <span className="env-capsule__label">Humidity</span>
              <span className="env-capsule__value">{episode?.env_today?.humidity ?? 70}%</span>
            </div>
          </div>
          <div className="glass-panel env-capsule">
            <i className="ph-fill ph-sun env-capsule__icon env-capsule__icon--light"></i>
            <div>
              <span className="env-capsule__label">Light</span>
              <span className="env-capsule__value">{episode?.env_today?.solar_radiation ? `${Math.round(episode.env_today.solar_radiation / 100)}k lux` : '8k lux'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid-main">
        {/* Hero Decision Card */}
        <div className="glass-panel hero-card">
          <div className="hero-card__glow"></div>
          <div className="hero-card__watermark">H2O</div>

          <div className="hero-card__content">
            <div>
              <div className="hero-card__header">
                <div>
                  <div className="hero-card__label">
                    <span className="hero-card__dot"></span>
                    <span className="hero-card__label-text">AI Decision</span>
                  </div>
                  <h3 className="hero-card__title">今日建议灌水量</h3>
                </div>
                <span className="hero-card__badge">
                  <i className="ph-bold ph-brain"></i> TSMixer v2.1
                </span>
              </div>

              <div className="hero-card__value">
                <span className="hero-card__number">{getIrrigationAmount().toFixed(1)}</span>
                <span className="hero-card__unit">L/m²</span>
              </div>

              <div className="stat-pills">
                <div className="stat-pill">
                  <div className={`stat-pill__icon ${trend.class}`}>
                    <i className={`ph-fill ${trend.icon}`}></i>
                  </div>
                  <div>
                    <span className="stat-pill__label">Growth Trend</span>
                    <span className="stat-pill__value">{trend.text}</span>
                  </div>
                </div>
                <div className="stat-pill">
                  <div className="stat-pill__icon stat-pill__icon--blue">
                    <i className="ph-fill ph-check-circle"></i>
                  </div>
                  <div>
                    <span className="stat-pill__label">Confidence</span>
                    <span className="stat-pill__value">{episode?.response?.confidence ? `${Math.round(episode.response.confidence * 100)}%` : '85%'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="btn-group">
              <button
                className="btn btn--primary"
                onClick={() => navigate(`/daily/${episode?.date || 'latest'}`)}
              >
                <i className="ph-bold ph-list-magnifying-glass btn__icon"></i>
                查看决策详情
              </button>
              <button
                className="btn btn--secondary"
                onClick={() => navigate('/predict')}
              >
                <i className="ph-bold ph-lightning btn__icon"></i>
                手动预测
              </button>
              <button className="btn btn--override" onClick={() => setIsOverrideModalOpen(true)}>
                <i className="ph-bold ph-pencil-simple"></i>
                人工覆盖
              </button>
            </div>
          </div>
        </div>

        {/* Side Widgets */}
        <div className="side-widgets">
          {/* Warning Card */}
          <div className="glass-panel warning-card">
            <i className="ph-fill ph-warning-octagon warning-card__icon"></i>
            <div className="warning-card__content">
              <div className="warning-card__header">
                <span className="warning-card__badge">Medium Risk</span>
                <span className="warning-card__time">10:30 AM</span>
              </div>
              <h4 className="warning-card__title">环境湿度偏高 (82%)</h4>
              <p className="warning-card__desc">
                连续 3 天检测到高湿环境，AI 建议检查通风系统以预防霉菌。
              </p>
            </div>
          </div>

          {/* Info Card */}
          <div className="glass-panel info-card">
            <div className="info-card__header">
              <span className="info-card__label">
                <i className="ph-fill ph-clock"></i> Yesterday
              </span>
            </div>
            <h4 className="info-card__title">灌溉执行完毕</h4>
            <div className="progress-bar">
              <div className="progress-bar__fill" style={{ width: '100%' }}></div>
            </div>
            <div className="info-card__stats">
              <span className="info-card__stat">Target: 5.0 L</span>
              <span className="info-card__stat info-card__stat--highlight">Actual: 5.0 L</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid-charts">
        {/* Trend Chart */}
        <div className="glass-panel chart-card">
          <TrendChart days={30} />
        </div>

        {/* Vision Card */}
        <div className="glass-panel vision-card">
          <div className="vision-card__header">
            <h3 className="vision-card__title">
              <i className="ph-fill ph-eye"></i> 视觉生长分析
            </h3>
            <span className="vision-card__badge">YOLOv11 Segmentation</span>
          </div>

          <div className="grid-vision">
            {/* Yesterday */}
            <div className="vision-preview">
              <div className="vision-preview__label">
                <span className="vision-preview__date">YESTERDAY</span>
              </div>
              <div className="vision-preview__image">
                {episode?.date && !imageError[`yesterday-${episode.date}`] ? (
                  <img
                    src={imageService.getSegmentedImageUrl(getYesterdayDate(episode.date))}
                    alt="Yesterday's segmented image"
                    style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '0.5rem' }}
                    onError={() => setImageError(prev => ({ ...prev, [`yesterday-${episode.date}`]: true }))}
                  />
                ) : (
                  <div className="vision-preview__placeholder">
                    <i className="ph-bold ph-image"></i>
                    <p>No Image</p>
                  </div>
                )}
                <div className="vision-preview__overlay">
                  <span className="vision-preview__mask">
                    <i className="ph-fill ph-leaf"></i> {episode?.yolo_yesterday?.['leaf Instance Count'] ?? 0} leaves
                  </span>
                </div>
              </div>
            </div>

            {/* Today */}
            <div className="vision-preview">
              <div className="vision-preview__label">
                <span className="vision-preview__date vision-preview__date--today">TODAY</span>
                <span className="vision-preview__change">
                  {episode?.yolo_today && episode?.yolo_yesterday ?
                    `${episode.yolo_today['leaf average mask'] > episode.yolo_yesterday['leaf average mask'] ? '+' : ''}${(((episode.yolo_today['leaf average mask'] - episode.yolo_yesterday['leaf average mask']) / episode.yolo_yesterday['leaf average mask']) * 100).toFixed(0)}%` :
                    ''}
                </span>
              </div>
              <div className="vision-preview__image vision-preview__image--today">
                {episode?.date && !imageError[`today-${episode.date}`] ? (
                  <img
                    src={imageService.getSegmentedImageUrl(getShortDate(episode.date))}
                    alt="Today's segmented image"
                    style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '0.5rem' }}
                    onError={() => setImageError(prev => ({ ...prev, [`today-${episode.date}`]: true }))}
                  />
                ) : (
                  <div className="vision-preview__placeholder">
                    <i className="ph-bold ph-image"></i>
                    <p>No Image</p>
                  </div>
                )}
                {/* YOLO Stats Overlay */}
                <div className="yolo-box">
                  <span className="yolo-box__label">
                    <i className="ph-fill ph-leaf"></i> {episode?.yolo_today?.['leaf Instance Count'] ?? 0}
                    {episode?.yolo_today?.['flower Instance Count'] ? (
                      <> | <i className="ph-fill ph-flower-lotus"></i> {episode.yolo_today['flower Instance Count']}</>
                    ) : null}
                  </span>
                </div>
                <div className="vision-preview__overlay">
                  <span className="vision-preview__mask vision-preview__mask--today">
                    Mask: {episode?.yolo_today?.['leaf average mask']?.toFixed(0) ?? 0}px
                  </span>
                </div>
              </div>
            </div>
          </div>

          <button
            className="btn btn--secondary"
            style={{ width: '100%', marginTop: '1.5rem' }}
            onClick={() => navigate('/vision')}
          >
            进入视觉分析实验室
            <i className="ph-bold ph-arrow-right btn__icon"></i>
          </button>
        </div>
      </div>

      {/* Override Modal */}
      <OverrideModal
        isOpen={isOverrideModalOpen}
        onClose={() => setIsOverrideModalOpen(false)}
        onConfirm={handleOverrideConfirm}
        currentAmount={getIrrigationAmount()}
        date={episode?.date || new Date().toISOString().split('T')[0]}
      />
    </div>
  )
}

export default Dashboard
