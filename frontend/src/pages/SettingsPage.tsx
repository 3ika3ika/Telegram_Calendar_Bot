import { useState, useEffect } from 'react'
import { User } from '../types/api'
import { apiClient } from '../services/api'
import NavBar from '../components/NavBar'
import './SettingsPage.css'

interface SettingsPageProps {
  user: User
}

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
            <option value="UTC">UTC</option>
            <option value="America/New_York">Eastern Time</option>
            <option value="America/Chicago">Central Time</option>
            <option value="America/Denver">Mountain Time</option>
            <option value="America/Los_Angeles">Pacific Time</option>
            <option value="Europe/London">London</option>
            <option value="Europe/Paris">Paris</option>
            <option value="Asia/Tokyo">Tokyo</option>
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

