// Chat Store - 聊天状态管理
import { create } from 'zustand'
import type { RAGReference } from '@/types/predict'
import type { ChatImageAttachment } from '@/types'

export interface ChatAsset {
  asset_id: string
  doc_id?: string
  source_title?: string
  source_file?: string
  page_num?: number
  asset_type?: string
  public_url?: string
  width?: number
  height?: number
  caption?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
  references?: RAGReference[]  // RAG 引用来源
  assets?: ChatAsset[]
  attachments?: ChatImageAttachment[]
}

interface ChatState {
  // 状态
  messages: Message[]
  isStreaming: boolean
  currentStreamContent: string
  isOpen: boolean
  error: string | null

  // Actions
  sendMessage: (content: string, attachment?: ChatImageAttachment) => Promise<void>
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

  sendMessage: async (content: string, attachment?: ChatImageAttachment) => {
    const { isStreaming } = get()
    if (isStreaming) return

    // 添加用户消息
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
      attachments: attachment ? [attachment] : undefined,
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
      const queryParams = new URLSearchParams({ query: content })
      if (attachment?.attachment_id) {
        queryParams.set('attachment_id', attachment.attachment_id)
      }
      const eventSource = new EventSource(`${API_BASE}/chat/stream?${queryParams.toString()}`)
      let pendingStreamText = ''
      let flushTimer: number | null = null

      const flushStreamText = () => {
        if (!pendingStreamText) return
        const text = pendingStreamText
        pendingStreamText = ''
        if (flushTimer) {
          window.clearTimeout(flushTimer)
          flushTimer = null
        }
        set(state => {
          const newContent = state.currentStreamContent + text
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
      }

      // 处理 RAG 检索结果
      eventSource.addEventListener('rag', (e) => {
        try {
          const { references, assets } = JSON.parse(e.data)
          set(state => {
            const messages = [...state.messages]
            const lastMsg = messages[messages.length - 1]
            if (lastMsg && lastMsg.role === 'assistant') {
              lastMsg.references = references || []
              lastMsg.assets = assets || []
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
          pendingStreamText += text
          if (pendingStreamText.length >= 80 || /[。！？；.!?]\s*$/.test(pendingStreamText)) {
            flushStreamText()
          } else if (!flushTimer) {
            flushTimer = window.setTimeout(flushStreamText, 90)
          }
        } catch (err) {
          console.error('Error parsing SSE content:', err)
        }
      })

      eventSource.addEventListener('done', (e) => {
        flushStreamText()
        set(state => {
          // 标记流式结束
          const messages = [...state.messages]
          const lastMsg = messages[messages.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.isStreaming = false
            try {
              const { assets } = JSON.parse(e.data || '{}')
              if (assets && assets.length > 0) {
                lastMsg.assets = assets
              }
            } catch {
              // done payload is optional metadata only.
            }
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
        flushStreamText()
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
