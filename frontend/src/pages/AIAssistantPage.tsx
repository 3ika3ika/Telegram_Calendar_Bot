import { User } from '../types/api'
import NavBar from '../components/NavBar'
import './AIAssistantPage.css'

interface AIAssistantPageProps {
  user: User
}

export default function AIAssistantPage({}: AIAssistantPageProps) {

  return (
    <div className="ai-assistant-page">
      <h1>AI Assistant</h1>
      <p className="ai-description">
        Tell me what you'd like to do with your calendar in natural language.
      </p>

      {/* NLPBox component removed - using Telegram bot instead */}
      <p>AI Assistant is available through the Telegram bot. Send messages directly to the bot to create, update, or delete events.</p>


      <NavBar />
    </div>
  )
}

