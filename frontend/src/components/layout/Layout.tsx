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
    const scroller = document.querySelector('.content-scroll')
    if (scroller) {
      scroller.scrollTo({ top: 0, left: 0, behavior: 'auto' })
      return
    }
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
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
