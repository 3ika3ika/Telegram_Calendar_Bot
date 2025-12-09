import { useState } from 'react'
import { User } from '../types/api'
import { apiClient } from '../services/api'
import NavBar from '../components/NavBar'
import './SettingsPage.css'

interface SettingsPageProps {
  user: User
}

// Helper function to get GMT offset for a timezone
function getGMTOffset(timezone: string): string {
  try {
    const now = new Date()
    
    // Method 1: Try to get offset using Intl API
    const formatter = new Intl.DateTimeFormat('en', {
      timeZone: timezone,
      timeZoneName: 'shortOffset'
    })
    
    const parts = formatter.formatToParts(now)
    const offsetPart = parts.find(part => part.type === 'timeZoneName')
    
    if (offsetPart) {
      const offset = offsetPart.value
      // If already in GMT format, return as is
      if (offset.startsWith('GMT') || offset.startsWith('UTC')) {
        return offset
      }
      // If it's in +HH:MM or -HH:MM format, convert to GMT format
      const match = offset.match(/([+-])(\d{1,2}):(\d{2})/)
      if (match) {
        const sign = match[1]
        const hours = parseInt(match[2])
        const minutes = parseInt(match[3])
        if (minutes === 0) {
          return `GMT${sign}${hours}`
        }
        return `GMT${sign}${hours}:${minutes.toString().padStart(2, '0')}`
      }
    }
    
    // Method 2: Calculate offset by comparing UTC and timezone
    const utcFormatter = new Intl.DateTimeFormat('en', {
      timeZone: 'UTC',
      hour: 'numeric',
      minute: 'numeric',
      hour12: false
    })
    
    const tzFormatter = new Intl.DateTimeFormat('en', {
      timeZone: timezone,
      hour: 'numeric',
      minute: 'numeric',
      hour12: false
    })
    
    const utcParts = utcFormatter.formatToParts(now)
    const tzParts = tzFormatter.formatToParts(now)
    
    const utcHour = parseInt(utcParts.find(p => p.type === 'hour')?.value || '0')
    const utcMin = parseInt(utcParts.find(p => p.type === 'minute')?.value || '0')
    const tzHour = parseInt(tzParts.find(p => p.type === 'hour')?.value || '0')
    const tzMin = parseInt(tzParts.find(p => p.type === 'minute')?.value || '0')
    
    const utcTotalMins = utcHour * 60 + utcMin
    const tzTotalMins = tzHour * 60 + tzMin
    let diffMins = tzTotalMins - utcTotalMins
    
    // Handle day boundary (could be +/- 24 hours)
    if (diffMins > 12 * 60) diffMins -= 24 * 60
    if (diffMins < -12 * 60) diffMins += 24 * 60
    
    const offsetHours = Math.floor(diffMins / 60)
    const offsetMins = Math.abs(diffMins % 60)
    const sign = offsetHours >= 0 ? '+' : '-'
    const absHours = Math.abs(offsetHours)
    
    if (offsetMins === 0) {
      return `GMT${sign}${absHours}`
    }
    return `GMT${sign}${absHours}:${offsetMins.toString().padStart(2, '0')}`
  } catch {
    return ''
  }
}

// Comprehensive timezone list with cities
const timezones = [
  { value: 'UTC', label: 'UTC', city: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time', city: 'New York' },
  { value: 'America/Chicago', label: 'Central Time', city: 'Chicago' },
  { value: 'America/Denver', label: 'Mountain Time', city: 'Denver' },
  { value: 'America/Los_Angeles', label: 'Pacific Time', city: 'Los Angeles' },
  { value: 'America/Phoenix', label: 'Mountain Time (Arizona)', city: 'Phoenix' },
  { value: 'America/Anchorage', label: 'Alaska Time', city: 'Anchorage' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time', city: 'Honolulu' },
  { value: 'America/Toronto', label: 'Eastern Time', city: 'Toronto' },
  { value: 'America/Vancouver', label: 'Pacific Time', city: 'Vancouver' },
  { value: 'Europe/London', label: 'Greenwich Mean Time', city: 'London' },
  { value: 'Europe/Paris', label: 'Central European Time', city: 'Paris' },
  { value: 'Europe/Berlin', label: 'Central European Time', city: 'Berlin' },
  { value: 'Europe/Rome', label: 'Central European Time', city: 'Rome' },
  { value: 'Europe/Madrid', label: 'Central European Time', city: 'Madrid' },
  { value: 'Europe/Amsterdam', label: 'Central European Time', city: 'Amsterdam' },
  { value: 'Europe/Athens', label: 'Eastern European Time', city: 'Athens' },
  { value: 'Europe/Moscow', label: 'Moscow Time', city: 'Moscow' },
  { value: 'Asia/Dubai', label: 'Gulf Standard Time', city: 'Dubai' },
  { value: 'Asia/Kolkata', label: 'India Standard Time', city: 'Mumbai' },
  { value: 'Asia/Shanghai', label: 'China Standard Time', city: 'Shanghai' },
  { value: 'Asia/Hong_Kong', label: 'Hong Kong Time', city: 'Hong Kong' },
  { value: 'Asia/Tokyo', label: 'Japan Standard Time', city: 'Tokyo' },
  { value: 'Asia/Seoul', label: 'Korea Standard Time', city: 'Seoul' },
  { value: 'Asia/Singapore', label: 'Singapore Time', city: 'Singapore' },
  { value: 'Australia/Sydney', label: 'Australian Eastern Time', city: 'Sydney' },
  { value: 'Australia/Melbourne', label: 'Australian Eastern Time', city: 'Melbourne' },
  { value: 'Australia/Brisbane', label: 'Australian Eastern Time', city: 'Brisbane' },
  { value: 'Pacific/Auckland', label: 'New Zealand Time', city: 'Auckland' },
  { value: 'America/Sao_Paulo', label: 'Brasilia Time', city: 'São Paulo' },
  { value: 'America/Mexico_City', label: 'Central Time', city: 'Mexico City' },
  { value: 'America/Buenos_Aires', label: 'Argentina Time', city: 'Buenos Aires' },
  { value: 'Africa/Cairo', label: 'Eastern European Time', city: 'Cairo' },
  { value: 'Africa/Johannesburg', label: 'South Africa Standard Time', city: 'Johannesburg' },
]

export default function SettingsPage({ user }: SettingsPageProps) {
  const [timezone, setTimezone] = useState(user.timezone)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await apiClient.updateUser(timezone)
      alert('Settings saved!')
    } catch (error) {
      console.error('Error saving settings:', error)
      alert('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="settings-page">
      <h1>Settings</h1>

      <div className="settings-section">
        <div className="form-group">
          <label className="form-label">Timezone</label>
          <select
            className="form-input"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
          >
            {timezones.map((tz) => {
              const gmtOffset = getGMTOffset(tz.value)
              const displayText = gmtOffset ? `${tz.city} (${gmtOffset})` : tz.city
              return (
                <option key={tz.value} value={tz.value}>
                  {displayText}
                </option>
              )
            })}
          </select>
        </div>

        <div className="settings-info">
          <p>Subscription: <strong>{user.subscription_plan}</strong></p>
          {user.subscription_expires_at && (
            <p>Expires: {new Date(user.subscription_expires_at).toLocaleDateString()}</p>
          )}
        </div>

        <div className="form-actions">
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>

      <NavBar />
    </div>
  )
}

