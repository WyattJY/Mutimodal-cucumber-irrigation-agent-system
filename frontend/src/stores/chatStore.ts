// Chat Store - 聊天状态管理
import { create } from 'zustand'
import type { RAGReference } from '@/types/predict'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
  references?: RAGReference[]  // RAG 引用来源
}

interface ChatState {
  // 状态
  messages: Message[]
  isStreaming: boolean
  currentStreamContent: string
  isOpen: boolean
  error: string | null

  // Actions
  sendMessage: (content: string) => Promise<void>
  clearHistory: () => void
  toggleChat: () => void
  setOpen: (open: boolean) => void
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  currentStreamContent: '',
  isOpen: false,
  error: null,

  sendMessage: async (content: string) => {
    const { isStreaming } = get()
    if (isStreaming) return

    // 添加用户消息
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    }

    // 添加占位的 AI 消息
    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    }

    set(state => ({
      messages: [...state.messages, userMessage, assistantMessage],
      isStreaming: true,
      currentStreamContent: '',
      error: null,
    }))

    try {
      // 使用 SSE 流式接收
      const eventSource = new EventSource(
        `${API_BASE}/chat/stream?query=${encodeURIComponent(content)}`
      )

      // 处理 RAG 检索结果
      eventSource.addEventListener('rag', (e) => {
        try {
          const { references } = JSON.parse(e.data)
          set(state => {
            const messages = [...state.messages]
            const lastMsg = messages[messages.length - 1]
            if (lastMsg && lastMsg.role === 'assistant') {
              lastMsg.references = references
            }
            return { messages }
          })
        } catch (err) {
          console.error('Error parsing RAG event:', err)
        }
      })

      eventSource.addEventListener('content', (e) => {
        try {
          const { text } = JSON.parse(e.data)
          set(state => {
            const newContent = state.currentStreamContent + text
            // 更新最后一条消息的内容
            const messages = [...state.messages]
            const lastMsg = messages[messages.length - 1]
            if (lastMsg && lastMsg.role === 'assistant') {
              lastMsg.content = newContent
            }
            return {
              currentStreamContent: newContent,
              messages,
            }
          })
        } catch (err) {
          console.error('Error parsing SSE content:', err)
        }
      })

      eventSource.addEventListener('done', () => {
        set(state => {
          // 标记流式结束
          const messages = [...state.messages]
          const lastMsg = messages[messages.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.isStreaming = false
          }
          return {
            isStreaming: false,
            currentStreamContent: '',
            messages,
          }
        })
        eventSource.close()
      })

      eventSource.addEventListener('error', (e) => {
        console.error('SSE error:', e)
        set(state => {
          const messages = [...state.messages]
          const lastMsg = messages[messages.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content = state.currentStreamContent || '抱歉，发生了错误，请重试。'
            lastMsg.isStreaming = false
          }
          return {
            isStreaming: false,
            error: '连接错误，请检查网络',
            messages,
          }
        })
        eventSource.close()
      })

    } catch (err) {
      console.error('Chat error:', err)
      set(state => {
        const messages = [...state.messages]
        const lastMsg = messages[messages.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.content = '抱歉，发生了错误，请重试。'
          lastMsg.isStreaming = false
        }
        return {
          isStreaming: false,
          error: err instanceof Error ? err.message : '未知错误',
          messages,
        }
      })
    }
  },

  clearHistory: () => {
    set({ messages: [], error: null })
    // 同时清除后端历史
    fetch(`${API_BASE}/chat/history`, { method: 'DELETE' }).catch(console.error)
  },

  toggleChat: () => {
    set(state => ({ isOpen: !state.isOpen }))
  },

  setOpen: (open: boolean) => {
    set({ isOpen: open })
  },
}))
