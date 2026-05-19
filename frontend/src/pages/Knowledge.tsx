import { useRef, useEffect, useState, type ChangeEvent } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { CompactRAGReferences } from '@/components/RAGReferences'
import { RichChatContent } from '@/components/chat'
import knowledgeService from '@/services/knowledgeService'
import chatService from '@/services/chatService'
import settingsService from '@/services/settingsService'
import type { ChatImageAttachment, KnowledgeUploadItem, UploadProgressSnapshot } from '@/types'

const SUGGESTED_PROMPTS = [
  '开花期最佳灌水量是多少？',
  '计算今日参考蒸发蒸腾量 ET₀',
  '什么是作物系数 Kc？',
  'VPD 偏高时应该怎么调整？',
]

const formatUploadSummary = (item: KnowledgeUploadItem) => {
  const parts = [`${item.chunk_count} chunks`]
  if (typeof item.image_count === 'number') parts.push(`${item.image_count} images`)
  if (item.index_status) parts.push(item.index_status)
  return `${item.original_filename} · ${parts.join(' · ')}`
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const BACKEND_ORIGIN = API_BASE.startsWith('http') ? API_BASE.replace(/\/api\/?$/, '') : ''

const resolveAssetUrl = (url?: string) => {
  if (!url) return ''
  if (/^https?:\/\//i.test(url) || url.startsWith('data:')) return url
  if (BACKEND_ORIGIN && url.startsWith('/')) return `${BACKEND_ORIGIN}${url}`
  return url
}

const formatEta = (seconds?: number) => {
  if (typeof seconds !== 'number' || !Number.isFinite(seconds) || seconds <= 0) return '计算中'
  if (seconds < 60) return `约 ${seconds} 秒`
  return `约 ${Math.ceil(seconds / 60)} 分钟`
}

const formatBytes = (bytes?: number) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = bytes
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value >= 10 || unitIndex === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[unitIndex]}`
}

const attachmentLabel = (attachment: ChatImageAttachment) =>
  `${attachment.original_filename} · ${formatBytes(attachment.size_bytes)}`

export function Knowledge() {
  const { messages, isStreaming, sendMessage, clearHistory } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const uploadInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const [uploads, setUploads] = useState<KnowledgeUploadItem[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgressSnapshot | null>(null)
  const [uploadStatus, setUploadStatus] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null)
  const [selectedImagePreviewUrl, setSelectedImagePreviewUrl] = useState<string | null>(null)
  const [chatUploadProgress, setChatUploadProgress] = useState<UploadProgressSnapshot | null>(null)
  const [chatUploadError, setChatUploadError] = useState<string | null>(null)
  const [isChatUploading, setIsChatUploading] = useState(false)
  const [activeModel, setActiveModel] = useState('')
  const isInputBusy = isStreaming || isChatUploading

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    void refreshUploads()
    void refreshActiveModel()
  }, [])

  useEffect(() => {
    return () => {
      if (selectedImagePreviewUrl) URL.revokeObjectURL(selectedImagePreviewUrl)
    }
  }, [selectedImagePreviewUrl])

  const refreshUploads = async () => {
    try {
      const result = await knowledgeService.listUploads()
      setUploads(result.items)
    } catch {
      setUploads([])
    }
  }

  const refreshActiveModel = async () => {
    try {
      const settings = await settingsService.getSettings()
      setActiveModel(settings.active_model || settings.default_model || '')
    } catch {
      setActiveModel('')
    }
  }

  const handleSend = async () => {
    const input = inputRef.current
    if (!input || isInputBusy) return

    const message = input.value.trim()
    if (!message && !selectedImageFile) return

    const outgoingText = message || '请分析这张图片'
    let attachment: ChatImageAttachment | undefined
    setChatUploadError(null)

    if (selectedImageFile) {
      setIsChatUploading(true)
      setChatUploadProgress({ loaded: 0, total: selectedImageFile.size, percent: 0 })
      try {
        attachment = await chatService.uploadImageAttachment(selectedImageFile, setChatUploadProgress)
      } catch (error) {
        setChatUploadError(getUploadErrorMessage(error))
        setIsChatUploading(false)
        return
      } finally {
        setIsChatUploading(false)
      }
    }

    input.value = ''
    setSelectedImageFile(null)
    setSelectedImagePreviewUrl(null)
    setChatUploadProgress(null)
    await sendMessage(outgoingText, attachment)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  const handlePromptClick = (prompt: string) => {
    if (inputRef.current) {
      inputRef.current.value = prompt
      inputRef.current.focus()
    }
  }

  const getUploadErrorMessage = (error: unknown) => {
    if (typeof error === 'object' && error && 'response' in error) {
      const response = (error as {
        response?: { data?: { detail?: string; error?: string | { message?: string } } }
      }).response
      const data = response?.data
      if (typeof data?.detail === 'string') return data.detail
      if (typeof data?.error === 'string') return data.error
      if (data?.error?.message) return data.error.message
    }
    return error instanceof Error ? error.message : '上传失败'
  }

  const handleImageSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    setChatUploadError(null)
    setChatUploadProgress(null)
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setChatUploadError('请选择图片文件')
      return
    }

    setSelectedImageFile(file)
    setSelectedImagePreviewUrl(URL.createObjectURL(file))
  }

  const clearSelectedImage = () => {
    setSelectedImageFile(null)
    setSelectedImagePreviewUrl(null)
    setChatUploadProgress(null)
    setChatUploadError(null)
  }

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || isUploading) return

    setIsUploading(true)
    setUploadStatus(null)
    setUploadProgress({ loaded: 0, total: file.size, percent: 0 })
    try {
      const result = await knowledgeService.uploadDocument(
        file,
        undefined,
        'user_literature',
        setUploadProgress
      )
      setUploadStatus({
        message: `已加入 ${formatUploadSummary(result)}`,
        type: 'success',
      })
      await refreshUploads()
    } catch (error) {
      setUploadStatus({ message: getUploadErrorMessage(error), type: 'error' })
    } finally {
      setIsUploading(false)
      setUploadProgress(null)
      event.target.value = ''
    }
  }

  return (
    <div className="chat-container knowledge-chat-container">
      {/* Messages Area */}
      <div className="chat-messages scrollbar-hide">
        <div className="chat-messages__inner">
          <div
            className="knowledge-upload"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              padding: '12px 16px',
              marginBottom: 16,
              border: '1px solid rgba(148, 163, 184, 0.22)',
              borderRadius: 8,
              background: 'rgba(15, 23, 42, 0.32)',
            }}
          >
            <div style={{ minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#dbeafe', fontWeight: 700 }}>
                <i className="ph-bold ph-books"></i>
                <span>知识库文献</span>
              </div>
              <div style={{ marginTop: 6, color: '#94a3b8', fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {uploads.length > 0
                  ? uploads.slice(0, 3).map(formatUploadSummary).join(' · ')
                  : 'FAO56 + 用户文献'}
              </div>
              {uploadStatus && (
                <div
                  style={{
                    marginTop: 6,
                    color: uploadStatus.type === 'error' ? '#fca5a5' : '#6ee7b7',
                    fontSize: 12,
                  }}
                >
                  {uploadStatus.message}
                </div>
              )}
              {isUploading && uploadProgress && (
                <div className="upload-progress">
                  <div className="upload-progress__meta">
                    <span>{uploadProgress.percent >= 100 ? '已上传，正在解析入库' : `上传 ${uploadProgress.percent}%`}</span>
                    <span>
                      {uploadProgress.percent >= 100
                        ? '服务端索引中'
                        : `${formatBytes(uploadProgress.loaded)}${uploadProgress.total ? ` / ${formatBytes(uploadProgress.total)}` : ''} · 剩余 ${formatEta(uploadProgress.etaSeconds)}`}
                    </span>
                  </div>
                  <div className="upload-progress__track">
                    <div
                      className="upload-progress__fill"
                      style={{ width: `${Math.max(4, uploadProgress.percent)}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
            <input
              ref={uploadInputRef}
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleUpload}
              style={{ display: 'none' }}
            />
            <button
              type="button"
              className="chat-input-btn"
              onClick={() => uploadInputRef.current?.click()}
              disabled={isUploading}
              title="上传 PDF/TXT/MD"
              style={{
                width: 'auto',
                minWidth: 132,
                paddingInline: 14,
                opacity: isUploading ? 0.6 : 1,
              }}
            >
              <i className={isUploading ? 'ph-bold ph-spinner' : 'ph-bold ph-upload-simple'} style={isUploading ? { animation: 'spin 1s linear infinite' } : undefined}></i>
              <span>{isUploading ? '上传中' : '上传文献'}</span>
            </button>
          </div>

          {messages.length === 0 ? (
            /* Welcome State */
            <div className="chat-welcome">
              <h1 className="chat-welcome__title">你好，操作员</h1>
              <p className="chat-welcome__subtitle">今天我能帮你解决什么灌溉问题？</p>

              {/* Suggested Prompts */}
              <div className="suggested-prompts">
                {SUGGESTED_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    className="suggested-prompt"
                    onClick={() => handlePromptClick(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Chat Messages */
            <>
              {messages.map((msg) =>
                msg.role === 'user' ? (
                  /* User Message */
                  <div key={msg.id} className="chat-msg--user">
                    <div className="chat-msg__user-bubble">
                      {msg.attachments && msg.attachments.length > 0 && (
                        <div className="chat-msg__user-attachments">
                          {msg.attachments.map((attachment) => {
                            const src = resolveAssetUrl(attachment.public_url)
                            return (
                              <a
                                key={attachment.attachment_id}
                                className="chat-msg__user-attachment"
                                href={src}
                                target="_blank"
                                rel="noreferrer"
                                title={attachmentLabel(attachment)}
                              >
                                <img src={src} alt={attachment.original_filename} />
                                <span>{attachmentLabel(attachment)}</span>
                              </a>
                            )
                          })}
                        </div>
                      )}
                      <span>{msg.content}</span>
                    </div>
                  </div>
                ) : (
                  /* Agent Message */
                  <div key={msg.id} className="chat-msg--agent">
                    <div className="chat-msg__avatar">
                      <i className="ph-fill ph-magic-wand"></i>
                    </div>
                    <div className="chat-msg__content">
                      <div className="chat-msg__header">
                        <span className="chat-msg__name">AgriAgent</span>
                        <span className="chat-msg__model">• {activeModel || '当前模型'}</span>
                      </div>

                      <div className="chat-prose">
                        {msg.content ? (
                          <RichChatContent
                            content={msg.content}
                            assets={msg.assets}
                            isStreaming={msg.isStreaming}
                          />
                        ) : (
                          !msg.isStreaming && <p>思考中...</p>
                        )}
                        {msg.isStreaming && <span className="chat-message__cursor">▋</span>}
                      </div>

                      {/* RAG References - show if available */}
                      {!msg.isStreaming && msg.references && msg.references.length > 0 && (
                        <CompactRAGReferences references={msg.references} maxDisplay={3} />
                      )}

                      {/* Action Chips - only show for completed messages */}
                      {!msg.isStreaming && msg.content && (
                        <div className="action-chips">
                          <button
                            className="action-chip"
                            onClick={() => navigator.clipboard.writeText(msg.content)}
                          >
                            <i className="ph-bold ph-copy"></i>
                            <span>复制</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )
              )}

              {/* Typing Indicator - show when streaming hasn't started receiving content yet */}
              {isStreaming && messages.length > 0 && !messages[messages.length - 1]?.content && (
                <div className="chat-msg--agent">
                  <div className="chat-msg__avatar">
                    <i className="ph-fill ph-magic-wand"></i>
                  </div>
                  <div className="chat-typing">
                    <div className="chat-typing__dots">
                      <div className="chat-typing__dot"></div>
                      <div className="chat-typing__dot"></div>
                      <div className="chat-typing__dot"></div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <div className="chat-input-container">
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            style={{ display: 'none' }}
          />
          {(selectedImageFile || chatUploadError) && (
            <div className="chat-attachment-preview">
              {selectedImageFile && selectedImagePreviewUrl && (
                <>
                  <img src={selectedImagePreviewUrl} alt={selectedImageFile.name} />
                  <div className="chat-attachment-preview__body">
                    <div className="chat-attachment-preview__title">{selectedImageFile.name}</div>
                    <div className="chat-attachment-preview__meta">
                      {formatBytes(selectedImageFile.size)}
                      {isChatUploading && chatUploadProgress
                        ? chatUploadProgress.percent >= 100
                          ? ' · 已上传，正在进入 Agent'
                          : ` · 上传 ${chatUploadProgress.percent}% · 剩余 ${formatEta(chatUploadProgress.etaSeconds)}`
                        : ' · 待发送给 AgriAgent'}
                    </div>
                    {isChatUploading && chatUploadProgress && (
                      <div className="upload-progress__track">
                        <div
                          className="upload-progress__fill"
                          style={{ width: `${Math.max(4, chatUploadProgress.percent)}%` }}
                        />
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    className="chat-input-btn"
                    onClick={clearSelectedImage}
                    disabled={isChatUploading}
                    title="移除图片"
                  >
                    <i className="ph-bold ph-x"></i>
                  </button>
                </>
              )}
              {chatUploadError && <div className="chat-attachment-preview__error">{chatUploadError}</div>}
            </div>
          )}
          <div className="chat-input-box">
            {messages.length > 0 && (
              <button
                className="chat-input-btn"
                onClick={clearHistory}
                title="清空对话"
              >
                <i className="ph-bold ph-trash"></i>
              </button>
            )}

            <button
              type="button"
              className="chat-input-btn"
              onClick={() => imageInputRef.current?.click()}
              disabled={isInputBusy}
              title="上传图片并让 AgriAgent 分析"
            >
              <i className="ph-bold ph-image-square"></i>
            </button>

            <input
              ref={inputRef}
              type="text"
              className="chat-input-field"
              placeholder={isInputBusy ? '处理中...' : '询问 FAO56、作物系数 (Kc)，或上传图片让 Agent 分析...'}
              onKeyPress={handleKeyPress}
              disabled={isInputBusy}
            />

            <button
              className="chat-input-btn chat-input-btn--send"
              onClick={handleSend}
              disabled={isInputBusy}
              style={{ opacity: isInputBusy ? 0.5 : 1 }}
            >
              {isInputBusy ? (
                <i className="ph-bold ph-spinner" style={{ animation: 'spin 1s linear infinite' }}></i>
              ) : (
                <i className="ph-bold ph-paper-plane-right"></i>
              )}
            </button>
          </div>

          <p className="chat-input-footer">
            AgriAgent 可能会显示不准确的信息，请仔细核对其回复。
          </p>
        </div>
      </div>
    </div>
  )
}

export default Knowledge
