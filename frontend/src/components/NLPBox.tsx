import { useState } from 'react'
import { apiClient } from '../services/api'
import { AIActionResponse } from '../types/api'
import './NLPBox.css'

interface NLPBoxProps {
  onActionParsed: (action: AIActionResponse) => void
  onError: (error: string) => void
}

export default function NLPBox({ onActionParsed, onError }: NLPBoxProps) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim() || loading) return

    setLoading(true)
    try {
      const response = await apiClient.parseAI({ text: text.trim() })
      onActionParsed(response)
      setText('')
    } catch (error: any) {
      console.error('AI parsing error:', error)
      onError(error.message || 'Failed to parse input')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="nlp-box" onSubmit={handleSubmit}>
      <input
        type="text"
        className="nlp-input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type natural language request (e.g., 'Move dentist to tomorrow at 5pm')"
        disabled={loading}
      />
      <button type="submit" className="nlp-submit" disabled={loading || !text.trim()}>
        {loading ? '...' : '→'}
      </button>
    </form>
  )
}

