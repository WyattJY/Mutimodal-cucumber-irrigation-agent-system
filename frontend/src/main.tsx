import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

import { router } from './routes'
import './index.css'
import './styles/cankao.css'

// Create QueryClient with default options
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      gcTime: 1000 * 60 * 5, // 5 minutes (formerly cacheTime)
      refetchOnWindowFocus: false,
      retry: 3,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1E1F20',
            color: '#E3E3E3',
            border: '1px solid #3C4043',
            borderRadius: '0.75rem',
          },
          success: {
            iconTheme: {
              primary: '#6DD58C',
              secondary: '#131314',
            },
          },
          error: {
            iconTheme: {
              primary: '#F28B82',
              secondary: '#131314',
            },
          },
        }}
      />
    </QueryClientProvider>
  </StrictMode>
)
