// Toast Hook - 封装 react-hot-toast

import toast from 'react-hot-toast'

export function useToast() {
  return {
    success: (message: string) => toast.success(message, {
      duration: 3000,
      style: {
        background: 'var(--color-surface)',
        color: 'var(--color-success)',
        border: '1px solid var(--color-success)',
      },
    }),

    error: (message: string) => toast.error(message, {
      duration: 4000,
      style: {
        background: 'var(--color-surface)',
        color: 'var(--color-danger)',
        border: '1px solid var(--color-danger)',
      },
    }),

    loading: (message: string) => toast.loading(message, {
      style: {
        background: 'var(--color-surface)',
        color: 'var(--color-text-primary)',
        border: '1px solid var(--color-border)',
      },
    }),

    info: (message: string) => toast(message, {
      duration: 3000,
      icon: 'ℹ️',
      style: {
        background: 'var(--color-surface)',
        color: 'var(--color-primary)',
        border: '1px solid var(--color-primary)',
      },
    }),

    dismiss: toast.dismiss,
  }
}
