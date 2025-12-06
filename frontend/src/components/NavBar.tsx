import { useLocation, useNavigate } from 'react-router-dom'
import './NavBar.css'

export default function NavBar() {
  const location = useLocation()
  const navigate = useNavigate()

  const navItems = [
    { path: '/', label: 'Calendar', icon: '📅' },
    { path: '/ai', label: 'AI', icon: '🤖' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ]

  return (
    <nav className="nav-bar">
      {navItems.map((item) => (
        <button
          key={item.path}
          className={`nav-button ${location.pathname === item.path ? 'active' : ''}`}
          onClick={() => navigate(item.path)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-label">{item.label}</span>
        </button>
      ))}
    </nav>
  )
}

