// Application Constants

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Risk Levels
export const RISK_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical',
} as const

export type RiskLevel = (typeof RISK_LEVELS)[keyof typeof RISK_LEVELS]

// Growth Trends
export const GROWTH_TRENDS = {
  BETTER: 'better',
  SAME: 'same',
  WORSE: 'worse',
} as const

export type GrowthTrend = (typeof GROWTH_TRENDS)[keyof typeof GROWTH_TRENDS]

// Decision Sources
export const DECISION_SOURCES = {
  TSMIXER: 'TSMixer',
  OVERRIDE: 'Override',
} as const

export type DecisionSource = (typeof DECISION_SOURCES)[keyof typeof DECISION_SOURCES]

// Navigation Items
export const NAV_ITEMS = [
  { path: '/', icon: 'ph-squares-four', label: '指挥舱', sublabel: 'DASHBOARD' },
  { path: '/daily/latest', icon: 'ph-git-commit', label: '今日决策链', sublabel: 'DECISION CHAIN' },
  { path: '/predict', icon: 'ph-lightning', label: '灌水预测', sublabel: 'PREDICT' },
  { path: '/vision', icon: 'ph-scan', label: '视觉分析', sublabel: 'VISION' },
  { path: '/history', icon: 'ph-chart-bar', label: '数据分析', sublabel: 'ANALYTICS' },
  { path: '/knowledge', icon: 'ph-chats-circle', label: '智能问答', sublabel: 'AI ASSISTANT' },
  { path: '/settings', icon: 'ph-gear-six', label: '系统设置', sublabel: 'SETTINGS' },
] as const

// Override Reasons (Quick Select)
export const OVERRIDE_REASONS = [
  '高温预警，需增加水量',
  '观察到轻微萎蔫',
  '实验需要',
  '其他（请手动输入）',
] as const

// Chart Colors
export const CHART_COLORS = {
  primary: '#00FF94',
  secondary: '#38BDF8',
  warning: '#FB923C',
  danger: '#EF4444',
  muted: '#64748B',
} as const

// Pagination
export const DEFAULT_PAGE_SIZE = 10
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const

// Polling Interval (ms)
export const POLLING_INTERVAL = 10000 // 10 seconds

// Cache Time (ms)
export const STALE_TIME = 60000 // 1 minute
export const CACHE_TIME = 300000 // 5 minutes
