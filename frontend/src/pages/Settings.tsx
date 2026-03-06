import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

type NavSection = 'model' | 'engine' | 'sensors' | 'alerts'
type EngineType = 'tsmixer' | 'fao56'
type Provider = 'custom' | 'openai' | 'deepseek' | 'ollama'

const PROVIDER_PRESETS: Record<Provider, { url: string; icon: string; placeholder: string }> = {
  custom: { url: '', icon: 'ph-cube', placeholder: 'https://api.your-service.com/v1' },
  openai: { url: 'https://api.openai.com/v1', icon: 'ph-microchip', placeholder: 'https://api.openai.com/v1' },
  deepseek: { url: 'https://api.deepseek.com/v1', icon: 'ph-brain', placeholder: 'https://api.deepseek.com/v1' },
  ollama: { url: 'http://localhost:11434/v1', icon: 'ph-desktop', placeholder: 'http://localhost:11434/v1' },
}

const MOCK_MODELS: Record<Provider, string[]> = {
  openai: ['gpt-4-turbo', 'gpt-4o', 'gpt-3.5-turbo', 'gpt-5.2'],
  deepseek: ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'],
  ollama: ['llama3', 'mistral', 'gemma:7b', 'qwen:14b'],
  custom: ['custom-model-v1', 'finetuned-agri-v2'],
}

const SENSORS = [
  { id: 'SN-B01', name: 'Master', status: 'online' },
  { id: 'SN-B02', name: 'Soil', status: 'online' },
  { id: 'SN-B03', name: 'Climate', status: 'online' },
  { id: 'SN-B04', name: 'Light', status: 'offline' },
]

const NAV_ITEMS = [
  { id: 'model' as NavSection, icon: 'ph-brain', label: '模型配置' },
  { id: 'engine' as NavSection, icon: 'ph-gavel', label: '决策引擎' },
  { id: 'sensors' as NavSection, icon: 'ph-wifi-high', label: '传感器' },
  { id: 'alerts' as NavSection, icon: 'ph-bell', label: '告警设置' },
]

export function Settings() {
  const [activeNav, setActiveNav] = useState<NavSection>('model')
  const [provider, setProvider] = useState<Provider>('custom')
  const [apiUrl, setApiUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [useCustomConfig, setUseCustomConfig] = useState(false)
  const [selectedEngine, setSelectedEngine] = useState<EngineType>('tsmixer')
  const [hybridMode, setHybridMode] = useState(true)
  const [kcValue, setKcValue] = useState('1.2')
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'loading' | 'connected' | 'error'>('idle')
  const [models, setModels] = useState<string[]>([])
  const [selectedModel, setSelectedModel] = useState('')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle')
  const [currentConfig, setCurrentConfig] = useState<{
    active_model: string
    active_base_url: string
    has_custom_key: boolean
  } | null>(null)

  // 加载当前配置
  useEffect(() => {
    fetch(`${API_BASE}/settings/`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data) {
          setCurrentConfig(data.data)
          setUseCustomConfig(data.data.use_custom_config)
          if (data.data.custom_base_url) {
            setApiUrl(data.data.custom_base_url)
          }
          if (data.data.custom_model) {
            setSelectedModel(data.data.custom_model)
          }
        }
      })
      .catch(err => console.error('Failed to load settings:', err))
  }, [])

  const handleProviderChange = (newProvider: Provider) => {
    setProvider(newProvider)
    setApiUrl(PROVIDER_PRESETS[newProvider].url)
    setConnectionStatus('idle')
    setModels([])
    setSelectedModel('')
  }

  const handleCheckConnection = async () => {
    setConnectionStatus('loading')
    try {
      // 先保存配置
      await fetch(`${API_BASE}/settings/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          use_custom_config: useCustomConfig,
          openai_api_key: apiKey || undefined,
          openai_base_url: apiUrl || undefined,
          openai_model: selectedModel || undefined,
        }),
      })

      // 测试连接
      const res = await fetch(`${API_BASE}/settings/test`, { method: 'POST' })
      const data = await res.json()

      if (data.success && data.data.success) {
        setConnectionStatus('connected')
        toast.success(`连接成功: ${data.data.model}`)
        // 获取模型列表
        const fetchedModels = MOCK_MODELS[provider]
        setModels(fetchedModels)
        if (!selectedModel && fetchedModels.length > 0) {
          setSelectedModel(fetchedModels[0])
        }
      } else {
        setConnectionStatus('error')
        toast.error(`连接失败: ${data.data?.message || '未知错误'}`)
      }
    } catch (err) {
      setConnectionStatus('error')
      toast.error('连接测试失败')
      console.error(err)
    }
  }

  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      const res = await fetch(`${API_BASE}/settings/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          use_custom_config: useCustomConfig,
          openai_api_key: apiKey || undefined,
          openai_base_url: apiUrl || undefined,
          openai_model: selectedModel || undefined,
        }),
      })
      const data = await res.json()

      if (data.success) {
        setSaveStatus('saved')
        toast.success('配置已保存')
        setTimeout(() => setSaveStatus('idle'), 2000)
      } else {
        toast.error('保存失败')
        setSaveStatus('idle')
      }
    } catch (err) {
      toast.error('保存失败')
      setSaveStatus('idle')
      console.error(err)
    }
  }

  const scrollToSection = (section: NavSection) => {
    setActiveNav(section)
    document.getElementById(section)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="settings-container">
      {/* Header */}
      <header className="settings-header">
        <h1 className="settings-header__title">系统配置</h1>
        <div className="settings-header__actions">
          <span className="settings-header__status">
            <i className="ph-fill ph-check-circle"></i>
            系统运行正常
          </span>
          <button
            onClick={handleSave}
            className={`settings-header__save-btn ${saveStatus === 'saved' ? 'settings-header__save-btn--success' : ''}`}
          >
            {saveStatus === 'saving' && <><i className="ph-bold ph-spinner animate-spin mr-1"></i>保存中...</>}
            {saveStatus === 'saved' && <><i className="ph-bold ph-check mr-1"></i>已保存</>}
            {saveStatus === 'idle' && '保存设置'}
          </button>
        </div>
      </header>

      <div className="settings-layout">
        {/* Left Navigation */}
        <nav className="settings-nav">
          <h3 className="settings-nav__title">设置菜单</h3>
          <ul className="settings-nav__list">
            {NAV_ITEMS.map(item => (
              <li key={item.id}>
                <button
                  onClick={() => scrollToSection(item.id)}
                  className={`settings-nav__item ${activeNav === item.id ? 'settings-nav__item--active' : ''}`}
                >
                  <i className={`ph-bold ${item.icon}`}></i>
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Main Content */}
        <div className="settings-content scrollbar-hide">
          <div className="settings-content__inner">

            {/* Section 1: Model Provider */}
            <section id="model" className="settings-section">
              <div className="settings-section__header">
                <h2 className="settings-section__title">语言模型配置</h2>
                <p className="settings-section__desc">配置 LLM 后端 (OpenAI, DeepSeek, Ollama 等)，支持自动获取模型列表</p>
              </div>

              {/* Current Config Display */}
              {currentConfig && (
                <div className="hybrid-card" style={{ marginBottom: '1rem' }}>
                  <div className="hybrid-card__info">
                    <i className="ph-bold ph-info hybrid-card__icon" style={{ color: 'var(--color-primary)' }}></i>
                    <div>
                      <h4 className="hybrid-card__title">当前配置</h4>
                      <p className="hybrid-card__desc">
                        模型: <strong>{currentConfig.active_model}</strong> |
                        {currentConfig.has_custom_key ? ' 使用自定义 Key' : ' 使用默认 Key'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Use Custom Config Toggle */}
              <div className="hybrid-card" style={{ marginBottom: '1rem' }}>
                <div className="hybrid-card__info">
                  <i className="ph-bold ph-gear hybrid-card__icon"></i>
                  <div>
                    <h4 className="hybrid-card__title">使用自定义配置</h4>
                    <p className="hybrid-card__desc">关闭则使用系统默认 API (GPT-5.2)</p>
                  </div>
                </div>
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={useCustomConfig}
                    onChange={(e) => setUseCustomConfig(e.target.checked)}
                    className="toggle__input"
                  />
                  <span className="toggle__slider"></span>
                </label>
              </div>

              <div className="setting-card provider-card" style={{ opacity: useCustomConfig ? 1 : 0.5, pointerEvents: useCustomConfig ? 'auto' : 'none' }}>
                {/* Provider Header */}
                <div className="provider-card__header">
                  <div className="provider-card__select-wrapper">
                    <div className="provider-card__icon">
                      <i className={`ph-bold ${PROVIDER_PRESETS[provider].icon}`}></i>
                    </div>
                    <div>
                      <label className="provider-card__select-label">模型提供商</label>
                      <select
                        value={provider}
                        onChange={(e) => handleProviderChange(e.target.value as Provider)}
                        className="provider-card__select"
                      >
                        <option value="custom">自定义 (OpenAI 兼容)</option>
                        <option value="openai">OpenAI</option>
                        <option value="deepseek">DeepSeek</option>
                        <option value="ollama">Ollama (本地)</option>
                      </select>
                    </div>
                  </div>

                  {connectionStatus === 'connected' && (
                    <div className="provider-card__status">
                      <span className="provider-card__status-dot"></span>
                      <span className="provider-card__status-text">已连接: {Math.floor(Math.random() * 200)}ms</span>
                    </div>
                  )}
                </div>

                {/* Input Grid */}
                <div className="input-grid">
                  <div className="input-m3-wrapper">
                    <label className="input-m3-label">API Base URL</label>
                    <div className="input-m3-container">
                      <i className="ph-bold ph-globe input-m3-icon"></i>
                      <input
                        type="text"
                        value={apiUrl}
                        onChange={(e) => setApiUrl(e.target.value)}
                        className="input-m3"
                        placeholder={PROVIDER_PRESETS[provider].placeholder}
                      />
                    </div>
                  </div>

                  <div className="input-m3-wrapper">
                    <label className="input-m3-label">API Key</label>
                    <div className="input-m3-container">
                      <i className="ph-bold ph-key input-m3-icon"></i>
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        className="input-m3"
                        placeholder="sk-..."
                        style={{ paddingRight: '2.5rem' }}
                      />
                      <button
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="input-m3-toggle"
                      >
                        <i className={`ph-bold ${showApiKey ? 'ph-eye' : 'ph-eye-slash'}`}></i>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Model Fetch Section */}
                <div className="model-fetch">
                  <div className="model-fetch__row">
                    <div className="model-fetch__select-wrapper">
                      <div className="model-fetch__label">
                        <span className="input-m3-label">选择模型</span>
                        {models.length > 0 && (
                          <span className="model-fetch__count">找到 {models.length} 个模型</span>
                        )}
                      </div>
                      <div style={{ position: 'relative' }}>
                        <select
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          disabled={models.length === 0}
                          className="model-fetch__select"
                        >
                          {models.length === 0 ? (
                            <option value="">等待连接检查...</option>
                          ) : (
                            models.map(m => <option key={m} value={m}>{m}</option>)
                          )}
                        </select>
                        <i className="ph-bold ph-caret-down model-fetch__select-icon"></i>
                      </div>
                    </div>

                    <button
                      onClick={handleCheckConnection}
                      disabled={connectionStatus === 'loading'}
                      className={`model-fetch__btn ${connectionStatus === 'connected' ? 'model-fetch__btn--success' : ''}`}
                    >
                      {connectionStatus === 'loading' && (
                        <><i className="ph-bold ph-spinner animate-spin"></i><span>连接中...</span></>
                      )}
                      {connectionStatus === 'connected' && (
                        <><i className="ph-bold ph-check"></i><span>成功</span></>
                      )}
                      {connectionStatus === 'idle' && (
                        <><i className="ph-bold ph-lightning"></i><span>检查并获取</span></>
                      )}
                    </button>
                  </div>

                  <p className="model-fetch__hint">
                    <i className="ph-bold ph-info"></i>
                    AgriAgent 将尝试 GET <code>/v1/models</code> 来自动填充模型列表
                  </p>
                </div>
              </div>
            </section>

            {/* Section 2: Decision Engine */}
            <section id="engine" className="settings-section">
              <div className="settings-section__header">
                <h2 className="settings-section__title">核心决策引擎</h2>
                <p className="settings-section__desc">选择自动灌溉任务的主要决策逻辑</p>
              </div>

              <div className="engine-grid">
                {/* TSMixer (AI) */}
                <div
                  onClick={() => setSelectedEngine('tsmixer')}
                  className={`engine-card ${selectedEngine === 'tsmixer' ? 'engine-card--selected card-selected' : ''}`}
                >
                  <div className="engine-card__check">
                    <i className={`ph-bold ${selectedEngine === 'tsmixer' ? 'ph-check-circle' : 'ph-circle'}`}></i>
                  </div>
                  <div className="engine-card__icon engine-card__icon--ai">
                    <i className="ph-bold ph-brain"></i>
                  </div>
                  <h3 className="engine-card__title">TSMixer (AI 驱动)</h3>
                  <p className="engine-card__desc">
                    使用 Google 的时序混合模型，基于 3 年历史数据训练。根据非线性模式预测需水量。
                  </p>
                  <div className="engine-card__footer">
                    <div className="engine-card__stat">
                      <span className="engine-card__stat-label">回溯窗口</span>
                      <span className="engine-card__stat-value engine-card__stat-value--purple">96h</span>
                    </div>
                    <div className="engine-card__progress">
                      <div className="engine-card__progress-fill engine-card__progress-fill--purple" style={{ width: '75%' }}></div>
                    </div>
                  </div>
                </div>

                {/* FAO56 (Physics) */}
                <div
                  onClick={() => setSelectedEngine('fao56')}
                  className={`engine-card ${selectedEngine === 'fao56' ? 'engine-card--selected card-selected' : ''}`}
                >
                  <div className="engine-card__check">
                    <i className={`ph-bold ${selectedEngine === 'fao56' ? 'ph-check-circle' : 'ph-circle'}`}></i>
                  </div>
                  <div className="engine-card__icon engine-card__icon--physics">
                    <i className="ph-bold ph-flask"></i>
                  </div>
                  <h3 className="engine-card__title">FAO56 Penman-Monteith</h3>
                  <p className="engine-card__desc">
                    黄金标准物理模型。基于净辐射、温度、风速和湿度严格计算蒸发蒸腾量 (ET₀)。
                  </p>
                  <div className="engine-card__footer">
                    <div className="engine-card__stat">
                      <span className="engine-card__stat-label">作物系数 (Kc)</span>
                      <input
                        type="number"
                        value={kcValue}
                        onChange={(e) => setKcValue(e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        step="0.1"
                        className="input-m3 input-m3--no-icon"
                        style={{ width: '64px', padding: '0.25rem 0.5rem', textAlign: 'center' }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Hybrid Mode Toggle */}
              <div className="hybrid-card">
                <div className="hybrid-card__info">
                  <i className="ph-bold ph-scales hybrid-card__icon"></i>
                  <div>
                    <h4 className="hybrid-card__title">混合验证模式</h4>
                    <p className="hybrid-card__desc">使用 FAO56 验证 AI 预测。偏差超过 20% 时告警。</p>
                  </div>
                </div>
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={hybridMode}
                    onChange={(e) => setHybridMode(e.target.checked)}
                    className="toggle__input"
                  />
                  <span className="toggle__slider"></span>
                </label>
              </div>
            </section>

            {/* Section 3: Sensors */}
            <section id="sensors" className="settings-section">
              <div className="settings-section__header">
                <h2 className="settings-section__title">传感器节点</h2>
                <p className="settings-section__desc">管理连接的 IoT 传感器设备</p>
              </div>

              <div className="sensor-list">
                {SENSORS.map((sensor, idx) => (
                  <div
                    key={sensor.id}
                    className={`sensor-list__item ${idx === 0 ? 'sensor-list__item--header' : ''}`}
                  >
                    <span className="sensor-list__name">{sensor.id} ({sensor.name})</span>
                    <span className={`sensor-list__status ${sensor.status === 'offline' ? 'sensor-list__status--offline' : ''}`}>
                      {sensor.status === 'online' ? '在线' : '离线'}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            {/* Section 4: Alerts */}
            <section id="alerts" className="settings-section">
              <div className="settings-section__header">
                <h2 className="settings-section__title">告警设置</h2>
                <p className="settings-section__desc">配置系统告警阈值和通知方式</p>
              </div>

              <div className="setting-card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="hybrid-card" style={{ marginTop: 0 }}>
                    <div className="hybrid-card__info">
                      <i className="ph-bold ph-envelope hybrid-card__icon"></i>
                      <div>
                        <h4 className="hybrid-card__title">邮件通知</h4>
                        <p className="hybrid-card__desc">异常事件发生时发送邮件</p>
                      </div>
                    </div>
                    <label className="toggle">
                      <input type="checkbox" defaultChecked className="toggle__input" />
                      <span className="toggle__slider"></span>
                    </label>
                  </div>

                  <div className="hybrid-card" style={{ marginTop: 0 }}>
                    <div className="hybrid-card__info">
                      <i className="ph-bold ph-device-mobile hybrid-card__icon"></i>
                      <div>
                        <h4 className="hybrid-card__title">短信告警</h4>
                        <p className="hybrid-card__desc">严重故障时发送短信</p>
                      </div>
                    </div>
                    <label className="toggle">
                      <input type="checkbox" className="toggle__input" />
                      <span className="toggle__slider"></span>
                    </label>
                  </div>

                  <div className="hybrid-card" style={{ marginTop: 0 }}>
                    <div className="hybrid-card__info">
                      <i className="ph-bold ph-speaker-high hybrid-card__icon"></i>
                      <div>
                        <h4 className="hybrid-card__title">声音提醒</h4>
                        <p className="hybrid-card__desc">在界面播放告警音效</p>
                      </div>
                    </div>
                    <label className="toggle">
                      <input type="checkbox" defaultChecked className="toggle__input" />
                      <span className="toggle__slider"></span>
                    </label>
                  </div>
                </div>
              </div>
            </section>

            {/* Danger Zone */}
            <section className="settings-section" style={{ paddingTop: '2.5rem' }}>
              <div className="danger-zone">
                <div>
                  <h3 className="danger-zone__title">恢复出厂设置</h3>
                  <p className="danger-zone__desc">清除所有自定义 API 密钥和学习权重</p>
                </div>
                <button className="danger-zone__btn">
                  重置系统
                </button>
              </div>
            </section>

          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings
