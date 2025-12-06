import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { TelegramWebApp } from './types/telegram'
import { User } from './types/api'
import { apiClient } from './services/api'
import CalendarPage from './pages/CalendarPage'
import EventDetailPage from './pages/EventDetailPage'
import SettingsPage from './pages/SettingsPage'
import AIAssistantPage from './pages/AIAssistantPage'
import TelegramLogin from './components/TelegramLogin'
import './App.css'

declare global {
  interface Window {
    Telegram?: TelegramWebApp
  }
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Initialize Telegram WebApp
    if (window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp
      tg.ready()
      tg.expand()
      
      // Set theme colors
      if (tg.colorScheme === 'dark') {
        document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#212121')
        document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#ffffff')
        document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999')
        document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#3390ec')
        document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#3390ec')
        document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff')
      }
    }

    // Try to authenticate
    authenticate()
  }, [])

  const authenticate = async () => {
    try {
      setLoading(true)
      setError(null)

      if (!window.Telegram?.WebApp?.initData) {
        setError('Telegram WebApp not available')
        setLoading(false)
        return
      }

      const initData = window.Telegram.WebApp.initData
      const userData = await apiClient.createSession(initData)
      setUser(userData)
    } catch (err: any) {
      console.error('Authentication error:', err)
      setError(err.message || 'Failed to authenticate')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="app-loading">
        <p>Loading...</p>
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="app-error">
        <p>{error || 'Please open this app from Telegram'}</p>
        {window.Telegram?.WebApp && (
          <button onClick={authenticate}>Retry</button>
        )}
      </div>
    )
  }

  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<CalendarPage user={user} />} />
          <Route path="/event/:id" element={<EventDetailPage user={user} />} />
          <Route path="/settings" element={<SettingsPage user={user} />} />
          <Route path="/ai" element={<AIAssistantPage user={user} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App

