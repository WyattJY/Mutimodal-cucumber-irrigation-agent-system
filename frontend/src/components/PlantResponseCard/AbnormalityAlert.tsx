// T3.5 AbnormalityAlert - 异常警告组件
import React from 'react'

type SeverityType = 'none' | 'mild' | 'severe'

interface Abnormalities {
  wilting?: SeverityType
  yellowing?: SeverityType
  pests?: SeverityType
  disease?: SeverityType
}

interface AbnormalityAlertProps {
  abnormalities: Abnormalities
}

interface AbnormalityConfig {
  label: string
  icon: string
  description: string
}

const abnormalityConfig: Record<keyof Abnormalities, AbnormalityConfig> = {
  wilting: {
    label: '萎蔫',
    icon: '💧',
    description: '植株出现缺水萎蔫症状'
  },
  yellowing: {
    label: '黄化',
    icon: '🍂',
    description: '叶片出现黄化现象'
  },
  pests: {
    label: '虫害',
    icon: '🐛',
    description: '发现害虫或虫害痕迹'
  },
  disease: {
    label: '病害',
    icon: '🦠',
    description: '发现病害症状'
  }
}

const severityStyles = {
  mild: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-300',
    text: 'text-yellow-800',
    badge: 'bg-yellow-200 text-yellow-800'
  },
  severe: {
    bg: 'bg-red-50',
    border: 'border-red-300',
    text: 'text-red-800',
    badge: 'bg-red-200 text-red-800'
  }
}

export const AbnormalityAlert: React.FC<AbnormalityAlertProps> = ({
  abnormalities
}) => {
  // 过滤掉 severity 为 'none' 的异常
  const activeAbnormalities = Object.entries(abnormalities)
    .filter(([, severity]) => severity && severity !== 'none')
    .map(([key, severity]) => ({
      key: key as keyof Abnormalities,
      severity: severity as 'mild' | 'severe',
      ...abnormalityConfig[key as keyof Abnormalities]
    }))

  if (activeAbnormalities.length === 0) {
    return null
  }

  // 按严重程度排序，severe 在前
  activeAbnormalities.sort((a, b) => {
    if (a.severity === 'severe' && b.severity !== 'severe') return -1
    if (a.severity !== 'severe' && b.severity === 'severe') return 1
    return 0
  })

  return (
    <div className="space-y-2">
      {activeAbnormalities.map(({ key, severity, label, icon, description }) => {
        const styles = severityStyles[severity]

        return (
          <div
            key={key}
            className={`
              flex items-start gap-3 p-3 rounded-lg border
              ${styles.bg} ${styles.border}
              transition-all duration-200 hover:shadow-sm
            `}
          >
            <span className="text-xl flex-shrink-0">{icon}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className={`font-medium ${styles.text}`}>{label}</span>
                <span
                  className={`
                    px-1.5 py-0.5 text-xs rounded-full font-medium
                    ${styles.badge}
                  `}
                >
                  {severity === 'severe' ? '严重' : '轻微'}
                </span>
              </div>
              <p className={`text-sm ${styles.text} opacity-80`}>
                {description}
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default AbnormalityAlert
