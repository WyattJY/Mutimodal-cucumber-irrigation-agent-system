// ChatPanel - 聊天面板组件 (AGRI-COPILOT)
import { useEffect, useRef } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { ChatInput } from './ChatInput'
import { ChatMessage } from './ChatMessage'
import clsx from 'clsx'

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const { messages, isStreaming, sendMessage, clearHistory } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  // ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  return (
    <div className={clsx('chat-panel', isOpen && 'chat-panel--open')}>
      {/* 头部 */}
      <div className="chat-panel__header">
        <div className="chat-panel__title">
          <i className="ph-bold ph-plant"></i>
          <span>AGRI-COPILOT</span>
        </div>
        <div className="chat-panel__actions">
          <button
            onClick={clearHistory}
            className="chat-panel__action"
            title="清除对话"
          >
            <i className="ph-bold ph-trash"></i>
          </button>
          <button
            onClick={onClose}
            className="chat-panel__action"
            title="关闭"
          >
            <i className="ph-bold ph-x"></i>
          </button>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="chat-panel__messages">
        {messages.length === 0 ? (
          <div className="chat-panel__empty">
            <div className="chat-panel__empty-icon">
              <i className="ph-bold ph-chats-circle"></i>
            </div>
            <h3>欢迎使用 AGRI-COPILOT</h3>
            <p>我是您的温室农业专家助手，可以回答关于黄瓜种植、灌溉管理、病虫害防治等问题。</p>
            <div className="chat-panel__suggestions">
              <button onClick={() => sendMessage('黄瓜灌溉量如何计算？')}>
                黄瓜灌溉量如何计算？
              </button>
              <button onClick={() => sendMessage('温室黄瓜常见病害有哪些？')}>
                温室黄瓜常见病害有哪些？
              </button>
              <button onClick={() => sendMessage('如何根据天气调整灌溉？')}>
                如何根据天气调整灌溉？
              </button>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入框 */}
      <div className="chat-panel__input">
        <ChatInput
          onSend={sendMessage}
          isLoading={isStreaming}
          placeholder="询问农业问题..."
        />
      </div>
    </div>
  )
}

export default ChatPanel
