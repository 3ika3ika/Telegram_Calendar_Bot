import { useEffect, useState, useCallback } from 'react'
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

  const authenticate = useCallback(async () => {
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
  }, [])

  useEffect(() => {
    // Development mode: Mock Telegram WebApp if not available
    // Check if we're in dev mode and Telegram WebApp initData is missing
    const isDevMode = import.meta.env.DEV
    const hasValidInitData = window.Telegram?.WebApp?.initData
    
    if (isDevMode && !hasValidInitData) {
      console.log('Development mode: Mocking Telegram WebApp')
      const mockInitData = `user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%2C%22language_code%22%3A%22en%22%7D&auth_date=${Math.floor(Date.now() / 1000)}&hash=dev_mode_hash`
      
      // Override or create the Telegram WebApp object
      if (!window.Telegram) {
        window.Telegram = {} as any
      }
      if (!window.Telegram.WebApp) {
        window.Telegram.WebApp = {} as any
      }
      
      // Set the mock data - merge with existing WebApp if it exists
      window.Telegram.WebApp = {
        ...(window.Telegram.WebApp || {}),
        initData: mockInitData,
        initDataUnsafe: {
          user: {
            id: 123456789,
            first_name: 'Test',
            last_name: 'User',
            username: 'testuser',
            language_code: 'en'
          },
          auth_date: Math.floor(Date.now() / 1000),
          hash: 'dev_mode_hash'
        },
        version: window.Telegram.WebApp?.version || '6.0',
        platform: window.Telegram.WebApp?.platform || 'web',
        colorScheme: window.Telegram.WebApp?.colorScheme || 'light',
        themeParams: window.Telegram.WebApp?.themeParams || {
          bg_color: '#ffffff',
          text_color: '#000000',
          hint_color: '#999999',
          link_color: '#3390ec',
          button_color: '#3390ec',
          button_text_color: '#ffffff'
        },
        isExpanded: window.Telegram.WebApp?.isExpanded ?? true,
        viewportHeight: window.Telegram.WebApp?.viewportHeight || window.innerHeight,
        viewportStableHeight: window.Telegram.WebApp?.viewportStableHeight || window.innerHeight,
        headerColor: window.Telegram.WebApp?.headerColor || '#3390ec',
        backgroundColor: window.Telegram.WebApp?.backgroundColor || '#ffffff',
        BackButton: window.Telegram.WebApp?.BackButton || {
          isVisible: false,
          onClick: () => {},
          offClick: () => {},
          show: () => {},
          hide: () => {}
        },
        MainButton: window.Telegram.WebApp?.MainButton || {
          text: '',
          color: '#3390ec',
          textColor: '#ffffff',
          isVisible: false,
          isActive: true,
          isProgressVisible: false,
          setText: () => {},
          onClick: () => {},
          offClick: () => {},
          show: () => {},
          hide: () => {},
          enable: () => {},
          disable: () => {},
          showProgress: () => {},
          hideProgress: () => {},
          setParams: () => {}
        },
        HapticFeedback: window.Telegram.WebApp?.HapticFeedback || {
          impactOccurred: () => {},
          notificationOccurred: () => {},
          selectionChanged: () => {}
        },
        ready: window.Telegram.WebApp?.ready || (() => {}),
        expand: window.Telegram.WebApp?.expand || (() => {}),
        close: window.Telegram.WebApp?.close || (() => {}),
        sendData: window.Telegram.WebApp?.sendData || (() => {}),
        openLink: window.Telegram.WebApp?.openLink || (() => {}),
        openTelegramLink: window.Telegram.WebApp?.openTelegramLink || (() => {}),
        openInvoice: window.Telegram.WebApp?.openInvoice || (() => {}),
        showPopup: window.Telegram.WebApp?.showPopup || (() => {}),
        showAlert: window.Telegram.WebApp?.showAlert || (() => {}),
        showConfirm: window.Telegram.WebApp?.showConfirm || (() => Promise.resolve(true)),
        showScanQrPopup: window.Telegram.WebApp?.showScanQrPopup || (() => {}),
        closeScanQrPopup: window.Telegram.WebApp?.closeScanQrPopup || (() => {}),
        readTextFromClipboard: window.Telegram.WebApp?.readTextFromClipboard || (() => Promise.resolve('')),
        requestWriteAccess: window.Telegram.WebApp?.requestWriteAccess || (() => Promise.resolve(true)),
        requestContact: window.Telegram.WebApp?.requestContact || (() => Promise.resolve(true))
      } as any
    }

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
  }, [authenticate])

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

