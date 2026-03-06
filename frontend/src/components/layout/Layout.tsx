import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { AuroraBackground } from './AuroraBackground'
import { ChatPanel } from '@/components/chat'
import { useChatStore } from '@/stores/chatStore'

export function Layout() {
  const location = useLocation()
  const { isOpen, toggleChat, setOpen } = useChatStore()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [location.pathname])

  return (
    <div className="app-container">
      {/* Aurora Background */}
      <AuroraBackground />

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="main-content">
        <div className="content-scroll">
          <Outlet />
        </div>
      </main>

      {/* Chat Panel */}
      <ChatPanel isOpen={isOpen} onClose={() => setOpen(false)} />

      {/* Floating Chat Toggle Button */}
      {!isOpen && (
        <button className="chat-toggle" onClick={toggleChat} title="AGRI-COPILOT">
          <i className="ph-bold ph-chats-circle"></i>
        </button>
      )}
    </div>
  )
}

export default Layout
