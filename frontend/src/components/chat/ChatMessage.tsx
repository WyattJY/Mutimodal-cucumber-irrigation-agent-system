// ChatMessage - 聊天消息气泡组件
import type { Message } from '@/stores/chatStore'
import clsx from 'clsx'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const isStreaming = message.isStreaming

  return (
    <div
      className={clsx(
        'chat-message',
        isUser ? 'chat-message--user' : 'chat-message--assistant'
      )}
    >
      {/* 头像 */}
      <div className="chat-message__avatar">
        {isUser ? (
          <i className="ph-bold ph-user"></i>
        ) : (
          <i className="ph-bold ph-plant"></i>
        )}
      </div>

      {/* 消息内容 */}
      <div className="chat-message__content">
        <div className="chat-message__bubble">
          {message.content || (isStreaming && (
            <span className="chat-message__typing">
              <span className="chat-message__dot"></span>
              <span className="chat-message__dot"></span>
              <span className="chat-message__dot"></span>
            </span>
          ))}
          {isStreaming && message.content && (
            <span className="chat-message__cursor">|</span>
          )}
        </div>
        <div className="chat-message__time">
          {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
