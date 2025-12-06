import { useState } from 'react'
import { User, AIActionResponse, Event } from '../types/api'
import { apiClient } from '../services/api'
import NLPBox from '../components/NLPBox'
import NavBar from '../components/NavBar'
import './AIAssistantPage.css'

interface AIAssistantPageProps {
  user: User
}

export default function AIAssistantPage({ user }: AIAssistantPageProps) {
  const [parsedAction, setParsedAction] = useState<AIActionResponse | null>(null)
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleActionParsed = (action: AIActionResponse) => {
    setParsedAction(action)
    setError(null)
  }

  const handleApplyAction = async () => {
    if (!parsedAction) return

    setApplying(true)
    setError(null)

    try {
      await apiClient.applyAIAction({
        action: parsedAction.action,
        payload: parsedAction.payload,
        original_text: '',
      })
      setParsedAction(null)
      alert('Action applied successfully!')
    } catch (err: any) {
      console.error('Error applying action:', err)
      setError(err.message || 'Failed to apply action')
    } finally {
      setApplying(false)
    }
  }

  const handleCancel = () => {
    setParsedAction(null)
    setError(null)
  }

  return (
    <div className="ai-assistant-page">
      <h1>AI Assistant</h1>
      <p className="ai-description">
        Tell me what you'd like to do with your calendar in natural language.
      </p>

      <NLPBox onActionParsed={handleActionParsed} onError={setError} />

      {error && (
        <div className="ai-error">
          <p>{error}</p>
        </div>
      )}

      {parsedAction && (
        <div className="ai-preview">
          <h2>Preview</h2>
          <div className="ai-preview-action">
            <div className="ai-preview-label">Action:</div>
            <div className="ai-preview-value">{parsedAction.action}</div>
          </div>
          <div className="ai-preview-summary">
            <div className="ai-preview-label">Summary:</div>
            <div className="ai-preview-value">{parsedAction.summary}</div>
          </div>
          {parsedAction.payload.message && (
            <div className="ai-preview-message">
              <div className="ai-preview-label">Message:</div>
              <div className="ai-preview-value">{parsedAction.payload.message}</div>
            </div>
          )}
          <div className="ai-preview-actions">
            <button className="btn btn-secondary" onClick={handleCancel}>
              Cancel
            </button>
            {parsedAction.action !== 'ASK' && parsedAction.action !== 'NOOP' && (
              <button
                className="btn btn-primary"
                onClick={handleApplyAction}
                disabled={applying}
              >
                {applying ? 'Applying...' : 'Apply'}
              </button>
            )}
          </div>
        </div>
      )}

      <NavBar />
    </div>
  )
}

