import type { ChatAsset } from '@/stores/chatStore'
import type { ReactNode } from 'react'

interface RichChatContentProps {
  content: string
  assets?: ChatAsset[]
  isStreaming?: boolean
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const BACKEND_ORIGIN = API_BASE.startsWith('http') ? API_BASE.replace(/\/api\/?$/, '') : ''
const ASSET_TOKEN_PATTERN = /\[\[asset:([^\]]+)\]\]/g

const resolveAssetUrl = (url?: string) => {
  if (!url) return ''
  if (/^https?:\/\//i.test(url) || url.startsWith('data:')) return url
  if (BACKEND_ORIGIN && url.startsWith('/')) return `${BACKEND_ORIGIN}${url}`
  return url
}

const assetLabel = (asset: ChatAsset, index: number) => {
  const title = asset.source_title || asset.source_file || '上传文献'
  const page = asset.page_num ? `P${asset.page_num}` : 'P?'
  return `${title} · ${page} · 图${index + 1}`
}

const stripMarkdownImages = (value: string) =>
  value.replace(/!\[[^\]]*\]\([^)]+\)/g, '').replace(/\n{3,}/g, '\n\n')

const renderInline = (text: string) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    return <span key={index}>{part}</span>
  })
}

const renderTextSegment = (text: string, keyPrefix: string) => {
  const cleaned = stripMarkdownImages(text).trim()
  if (!cleaned) return null

  return cleaned.split(/\n{2,}/).map((block, index) => {
    const trimmed = block.trim()
    if (!trimmed) return null

    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/)
    if (heading) {
      return (
        <h4 key={`${keyPrefix}-h-${index}`} className="chat-rich__heading">
          {renderInline(heading[2])}
        </h4>
      )
    }

    const lines = trimmed.split('\n').map(line => line.trim()).filter(Boolean)
    const unorderedItems = lines.every(line => /^[-*]\s+/.test(line))
    const orderedItems = lines.every(line => /^\d+[.)]\s+/.test(line))

    if (unorderedItems || orderedItems) {
      const Tag = orderedItems ? 'ol' : 'ul'
      return (
        <Tag key={`${keyPrefix}-list-${index}`} className="chat-rich__list">
          {lines.map((line, itemIndex) => (
            <li key={itemIndex}>{renderInline(line.replace(/^([-*]|\d+[.)])\s+/, ''))}</li>
          ))}
        </Tag>
      )
    }

    const paragraph = lines.join(' ')
    return (
      <p key={`${keyPrefix}-p-${index}`} className="chat-rich__paragraph">
        {renderInline(paragraph)}
      </p>
    )
  })
}

export function RichChatContent({ content, assets = [], isStreaming }: RichChatContentProps) {
  const assetById = new Map(assets.map((asset, index) => [asset.asset_id, { asset, index }]))
  const nodes: ReactNode[] = []
  let lastIndex = 0

  for (const match of content.matchAll(ASSET_TOKEN_PATTERN)) {
    const before = content.slice(lastIndex, match.index)
    const textNodes = renderTextSegment(before, `text-${lastIndex}`)
    if (textNodes) nodes.push(textNodes)

    const matchId = match[1]
    const assetEntry = assetById.get(matchId)
    if (assetEntry) {
      const { asset, index } = assetEntry
      const src = resolveAssetUrl(asset.public_url)
      if (src) {
        nodes.push(
          <figure key={`asset-${matchId}`} className="chat-rich__asset">
            <a href={src} target="_blank" rel="noreferrer">
              <img src={src} alt={assetLabel(asset, index)} loading="lazy" />
            </a>
            <figcaption>
              <span>{assetLabel(asset, index)}</span>
              {asset.caption && <small>{asset.caption}</small>}
            </figcaption>
          </figure>
        )
      }
    }
    lastIndex = (match.index || 0) + match[0].length
  }

  const tailNodes = renderTextSegment(content.slice(lastIndex), `text-${lastIndex}`)
  if (tailNodes) nodes.push(tailNodes)

  if (!nodes.length && isStreaming) return null

  return <div className="chat-rich">{nodes}</div>
}

export default RichChatContent
