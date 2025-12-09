import { useEffect, useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { TelegramWebAppType } from './types/telegram'
import { User } from './types/api'
import { apiClient } from './services/api'
import CalendarPage from './pages/CalendarPage'
import EventDetailPage from './pages/EventDetailPage'
import SettingsPage from './pages/SettingsPage'
import AIAssistantPage from './pages/AIAssistantPage'
import './App.css'

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebAppType
    }
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

      // Wait a bit for Telegram script to load if in production
      const isDevMode = import.meta.env.DEV
      if (!isDevMode && !window.Telegram?.WebApp) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }

      if (!window.Telegram?.WebApp?.initData) {
        // In dev mode, the mock should have been set up, so this shouldn't happen
        if (isDevMode) {
          console.warn('Telegram WebApp mock not set up properly')
        }
        setError('Telegram WebApp not available. Please open this app from Telegram, or use development mode.')
        setLoading(false)
        return
      }

      const initData = window.Telegram.WebApp.initData
      const userData = await apiClient.createSession(initData)
      setUser(userData)
    } catch (err: any) {
      console.error('Authentication error:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to authenticate'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Development mode: Mock Telegram WebApp if not available
    // Check if we're in dev mode and Telegram WebApp initData is missing
    const isDevMode = import.meta.env.DEV
    const hasValidInitData = window.Telegram?.WebApp?.initData
    
    // The mock should already be set up in index.html, but ensure it's there
    
    // Set up mock immediately if needed (before Telegram script tries to access it)
    if (isDevMode && !hasValidInitData) {
      console.log('Development mode: Mocking Telegram WebApp')
      const mockInitData = `user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%2C%22language_code%22%3A%22en%22%7D&auth_date=${Math.floor(Date.now() / 1000)}&hash=dev_mode_hash`
      
      // Override or create the Telegram WebApp object
      if (!window.Telegram) {
        window.Telegram = {} as any
      }
      // At this point, window.Telegram is guaranteed to exist
      const telegram = window.Telegram!
      const existingWebApp = telegram.WebApp || {}
      if (!telegram.WebApp) {
        telegram.WebApp = {} as any
      }
      
      // Set the mock data - merge with existing WebApp if it exists
      telegram.WebApp = {
        ...existingWebApp,
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
        version: (existingWebApp as any)?.version || '6.0',
        platform: (existingWebApp as any)?.platform || 'web',
        colorScheme: (existingWebApp as any)?.colorScheme || 'light',
        themeParams: (existingWebApp as any)?.themeParams || {
          bg_color: '#ffffff',
          text_color: '#000000',
          hint_color: '#999999',
          link_color: '#3390ec',
          button_color: '#3390ec',
          button_text_color: '#ffffff'
        },
        isExpanded: (existingWebApp as any)?.isExpanded ?? true,
        viewportHeight: (existingWebApp as any)?.viewportHeight || window.innerHeight,
        viewportStableHeight: (existingWebApp as any)?.viewportStableHeight || window.innerHeight,
        headerColor: (existingWebApp as any)?.headerColor || '#3390ec',
        backgroundColor: (existingWebApp as any)?.backgroundColor || '#ffffff',
        BackButton: (existingWebApp as any)?.BackButton || {
          isVisible: false,
          onClick: () => {},
          offClick: () => {},
          show: () => {},
          hide: () => {}
        },
        MainButton: (existingWebApp as any)?.MainButton || {
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
        HapticFeedback: (existingWebApp as any)?.HapticFeedback || {
          impactOccurred: () => {},
          notificationOccurred: () => {},
          selectionChanged: () => {}
        },
        ready: (existingWebApp as any)?.ready || (() => {}),
        expand: (existingWebApp as any)?.expand || (() => {}),
        close: (existingWebApp as any)?.close || (() => {}),
        sendData: (existingWebApp as any)?.sendData || (() => {}),
        openLink: (existingWebApp as any)?.openLink || (() => {}),
        openTelegramLink: (existingWebApp as any)?.openTelegramLink || (() => {}),
        openInvoice: (existingWebApp as any)?.openInvoice || (() => {}),
        showPopup: (existingWebApp as any)?.showPopup || (() => {}),
        showAlert: (existingWebApp as any)?.showAlert || (() => {}),
        showConfirm: (existingWebApp as any)?.showConfirm || (() => Promise.resolve(true)),
        showScanQrPopup: (existingWebApp as any)?.showScanQrPopup || (() => {}),
        closeScanQrPopup: (existingWebApp as any)?.closeScanQrPopup || (() => {}),
        readTextFromClipboard: (existingWebApp as any)?.readTextFromClipboard || (() => Promise.resolve('')),
        requestWriteAccess: (existingWebApp as any)?.requestWriteAccess || (() => Promise.resolve(true)),
        requestContact: (existingWebApp as any)?.requestContact || (() => Promise.resolve(true))
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

