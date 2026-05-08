import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { NAV_ITEMS } from '@/utils/constants'
import { useChatStore } from '@/stores/chatStore'

export function Sidebar() {
  const [copilotInput, setCopilotInput] = useState('')
  const navigate = useNavigate()

  // 使用 chat store
  const { messages, isStreaming, sendMessage, clearHistory } = useChatStore()

  // 获取最近的消息 (最多显示4条)
  const recentMessages = messages.slice(-4)

  const handleCopilotSubmit = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && copilotInput.trim() && !isStreaming) {
      const message = copilotInput.trim()
      setCopilotInput('')
      await sendMessage(message)
    }
  }

  const handleSendClick = async () => {
    if (copilotInput.trim() && !isStreaming) {
      const message = copilotInput.trim()
      setCopilotInput('')
      await sendMessage(message)
    }
  }

  return (
    <aside className="sidebar glass-sidebar">
      {/* Brand */}
      <div className="sidebar__brand">
        <div className="sidebar__logo">
          <i className="ph-bold ph-plant"></i>
        </div>
        <div>
          <span className="sidebar__title">AgriAgent</span>
          <span className="sidebar__subtitle">Intelligence</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav scrollbar-hide">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <i className={`ph ${item.icon} nav-item__icon`}></i>
            <div>
              <span className="nav-item__label">{item.label}</span>
              <span className="nav-item__sublabel">{item.sublabel}</span>
            </div>
          </NavLink>
        ))}
      </nav>

      {/* Copilot */}
      <div className="copilot">
        <div className="copilot__card">
          <div className="copilot__header">
            <div className="copilot__dot"></div>
            <span className="copilot__title">AGRI-COPILOT</span>
            {messages.length > 0 && (
              <button
                className="copilot__clear"
                onClick={clearHistory}
                title="清空对话"
                style={{
                  marginLeft: 'auto',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--color-text-muted)',
                  cursor: 'pointer',
                  fontSize: '12px',
                }}
              >
                <i className="ph-bold ph-trash"></i>
              </button>
            )}
          </div>

          {recentMessages.length > 0 && (
            <div className="scrollbar-hide" style={{ maxHeight: '128px', overflowY: 'auto', marginBottom: '0.75rem' }}>
              {recentMessages.map((msg) => (
                <div
                  key={msg.id}
                  className="animate-fade-in"
                  style={{
                    fontSize: '10px',
                    padding: '0.5rem',
                    borderRadius: '0.5rem',
                    marginBottom: '0.5rem',
                    ...(msg.role === 'user'
                      ? {
                          color: '#E3E3E3',
                          background: 'rgba(109, 213, 140, 0.15)',
                          borderTopRightRadius: 0,
                          marginLeft: '1rem',
                          border: '1px solid rgba(109, 213, 140, 0.25)',
                        }
                      : {
                          color: '#C4C7C5',
                          background: 'rgba(255, 255, 255, 0.05)',
                          borderTopLeftRadius: 0,
                          marginRight: '1rem',
                          border: '1px solid rgba(255, 255, 255, 0.08)',
                        }),
                  }}
                >
                  {msg.content || (msg.isStreaming ? '思考中...' : '')}
                  {msg.isStreaming && <span className="chat-message__cursor">▋</span>}
                </div>
              ))}
            </div>
          )}

          {messages.length === 0 && (
            <p className="copilot__placeholder">
              基于 FAO56 知识库与 GPT 模型。您可以询问："开花期最佳灌水量是多少？"
            </p>
          )}

          <div className="copilot__input-wrapper">
            <input
              type="text"
              className="copilot__input"
              placeholder={isStreaming ? '回复中...' : '向智能体提问...'}
              value={copilotInput}
              onChange={(e) => setCopilotInput(e.target.value)}
              onKeyPress={handleCopilotSubmit}
              disabled={isStreaming}
            />
            <button
              className="copilot__send"
              onClick={handleSendClick}
              disabled={isStreaming || !copilotInput.trim()}
              style={{ opacity: isStreaming || !copilotInput.trim() ? 0.5 : 1 }}
            >
              {isStreaming ? (
                <i className="ph-bold ph-spinner" style={{ animation: 'spin 1s linear infinite' }}></i>
              ) : (
                <i className="ph-bold ph-paper-plane-right"></i>
              )}
            </button>
          </div>

          {/* 快捷进入完整对话页面 */}
          <button
            className="copilot__expand"
            onClick={() => navigate('/knowledge')}
            style={{
              marginTop: '0.5rem',
              width: '100%',
              padding: '0.5rem',
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: '0.375rem',
              color: 'var(--color-text-muted)',
              fontSize: '10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.25rem',
              transition: 'all 0.2s',
            }}
          >
            <i className="ph-bold ph-arrows-out-simple"></i>
            展开完整对话
          </button>
        </div>
      </div>

      {/* User Profile */}
      <div className="user-profile">
        <div className="user-profile__inner">
          <div className="user-profile__avatar">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="User" />
            <span className="user-profile__status"></span>
          </div>
          <div className="user-profile__info">
            <p className="user-profile__name">Admin User</p>
            <p className="user-profile__location">Greenhouse #A-102</p>
          </div>
          <button className="user-profile__settings" onClick={() => navigate('/settings')}>
            <i className="ph-bold ph-gear"></i>
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
