import { User } from '../types/api'
import NavBar from '../components/NavBar'
import './SettingsPage.css'

interface SettingsPageProps {
  user: User
}

export default function SettingsPage({ user }: SettingsPageProps) {
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'

  return (
    <div className="settings-page">
      <h1>Settings</h1>

      <div className="settings-section">
        <div className="settings-info">
          <p>Timezone: <strong>{userTimezone}</strong> (automatically detected)</p>
          <p>Subscription: <strong>{user.subscription_plan}</strong></p>
          {user.subscription_expires_at && (
            <p>Expires: {new Date(user.subscription_expires_at).toLocaleDateString()}</p>
          )}
        </div>
      </div>

      <NavBar />
    </div>
  )
}

