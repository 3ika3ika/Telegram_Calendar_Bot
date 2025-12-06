import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'
import { User } from '../types/api'

interface TelegramLoginProps {
  onSuccess: (user: User) => void
}

export default function TelegramLogin({ onSuccess }: TelegramLoginProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    authenticate()
  }, [])

  const authenticate = async () => {
    try {
      setLoading(true)
      setError(null)

      if (!window.Telegram?.WebApp?.initData) {
        setError('Telegram WebApp not available')
        return
      }

      const initData = window.Telegram.WebApp.initData
      const user = await apiClient.createSession(initData)
      onSuccess(user)
    } catch (err: any) {
      console.error('Authentication error:', err)
      setError(err.message || 'Failed to authenticate')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return (
      <div>
        <p>{error}</p>
        <button onClick={authenticate}>Retry</button>
      </div>
    )
  }

  return null
}

