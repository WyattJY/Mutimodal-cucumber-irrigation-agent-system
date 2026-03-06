// T3.4 EvidenceList - 证据列表组件
import React, { useState } from 'react'

interface Evidence {
  leaves?: string
  flowers?: string
  fruits?: string
  apex?: string
}

interface EvidenceListProps {
  evidence: Evidence
  expandable?: boolean
  defaultExpanded?: boolean
}

interface EvidenceItemProps {
  icon: string
  label: string
  content: string | undefined
}

const EvidenceItem: React.FC<EvidenceItemProps> = ({ icon, label, content }) => {
  if (!content) return null

  return (
    <div className="flex items-start gap-2 py-2 border-b border-gray-100 last:border-0">
      <span className="text-lg flex-shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="text-xs text-gray-500 mb-0.5">{label}</div>
        <div className="text-sm text-gray-700">{content}</div>
      </div>
    </div>
  )
}

export const EvidenceList: React.FC<EvidenceListProps> = ({
  evidence,
  expandable = true,
  defaultExpanded = false
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded)

  const hasContent =
    evidence.leaves || evidence.flowers || evidence.fruits || evidence.apex

  if (!hasContent) {
    return (
      <div className="text-sm text-gray-400 italic py-2">
        暂无观察记录
      </div>
    )
  }

  const evidenceItems = [
    { icon: '🌿', label: '叶片观察', content: evidence.leaves },
    { icon: '🌸', label: '花朵观察', content: evidence.flowers },
    { icon: '🥒', label: '果实观察', content: evidence.fruits },
    { icon: '🌱', label: '顶芽观察', content: evidence.apex }
  ]

  const visibleItems = expandable && !expanded ? evidenceItems.slice(0, 2) : evidenceItems
  const hiddenCount = evidenceItems.filter(item => item.content).length - 2

  return (
    <div className="space-y-0">
      {visibleItems.map((item, index) => (
        <EvidenceItem
          key={index}
          icon={item.icon}
          label={item.label}
          content={item.content}
        />
      ))}

      {expandable && hiddenCount > 0 && !expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="w-full py-2 text-sm text-blue-600 hover:text-blue-800 transition-colors"
        >
          展开更多 ({hiddenCount}项)
        </button>
      )}

      {expandable && expanded && (
        <button
          onClick={() => setExpanded(false)}
          className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          收起
        </button>
      )}
    </div>
  )
}

export default EvidenceList
