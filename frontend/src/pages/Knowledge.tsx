import { useRef, useEffect } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { CompactRAGReferences } from '@/components/RAGReferences'

const SUGGESTED_PROMPTS = [
  '开花期最佳灌水量是多少？',
  '计算今日参考蒸发蒸腾量 ET₀',
  '什么是作物系数 Kc？',
  'VPD 偏高时应该怎么调整？',
]

export function Knowledge() {
  const { messages, isStreaming, sendMessage, clearHistory } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    const input = inputRef.current
    if (!input || !input.value.trim() || isStreaming) return

    const message = input.value.trim()
    input.value = ''
    await sendMessage(message)
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

  return (
    <div className="chat-container">
      {/* Messages Area */}
      <div className="chat-messages scrollbar-hide">
        <div className="chat-messages__inner">
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
                    <div className="chat-msg__user-bubble">{msg.content}</div>
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
                        <span className="chat-msg__model">• GPT-5.2</span>
                      </div>

                      <div className="chat-prose">
                        <p style={{ whiteSpace: 'pre-wrap' }}>
                          {msg.content || (msg.isStreaming ? '' : '思考中...')}
                          {msg.isStreaming && <span className="chat-message__cursor">▋</span>}
                        </p>
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

            <input
              ref={inputRef}
              type="text"
              className="chat-input-field"
              placeholder={isStreaming ? '回复中...' : '询问 FAO56、作物系数 (Kc)，或模拟灌溉场景...'}
              onKeyPress={handleKeyPress}
              disabled={isStreaming}
            />

            <button
              className="chat-input-btn chat-input-btn--send"
              onClick={handleSend}
              disabled={isStreaming}
              style={{ opacity: isStreaming ? 0.5 : 1 }}
            >
              {isStreaming ? (
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
