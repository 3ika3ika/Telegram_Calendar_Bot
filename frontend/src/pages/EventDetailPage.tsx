import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { User, Event } from '../types/api'
import { apiClient } from '../services/api'
import { removeEventFromCache } from '../services/cache'
import EventEditorModal from '../components/EventEditorModal'
import NavBar from '../components/NavBar'
import './EventDetailPage.css'

interface EventDetailPageProps {
  user: User
}

export default function EventDetailPage({}: EventDetailPageProps) {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [event, setEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [showEditor, setShowEditor] = useState(false)

  useEffect(() => {
    if (id) {
      loadEvent()
    }
  }, [id])

  const loadEvent = async () => {
    if (!id) return
    try {
      setLoading(true)
      const eventData = await apiClient.getEvent(id)
      setEvent(eventData)
    } catch (error) {
      console.error('Error loading event:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (eventData: any) => {
    if (!event) return
    try {
      const updated = await apiClient.updateEvent(event.id, eventData)
      setEvent(updated)
      setShowEditor(false)
    } catch (error) {
      console.error('Error updating event:', error)
      throw error
    }
  }

  const handleDelete = async () => {
    if (!event) return
    try {
      await apiClient.deleteEvent(event.id)
      // Remove from cache immediately
      await removeEventFromCache(event.id)
      navigate('/')
    } catch (error) {
      console.error('Error deleting event:', error)
      throw error
    }
  }

  if (loading) {
    return (
      <div className="event-detail-page">
        <div className="loading">Loading event...</div>
        <NavBar />
      </div>
    )
  }

  if (!event) {
    return (
      <div className="event-detail-page">
        <div className="error">Event not found</div>
        <NavBar />
      </div>
    )
  }

  const startTime = new Date(event.start_time)
  const endTime = new Date(event.end_time)

  return (
    <div className="event-detail-page">
      <div className="event-detail-header">
        <button onClick={() => navigate('/')}>← Back</button>
        <button onClick={() => setShowEditor(true)}>Edit</button>
      </div>

      <div className="event-detail-content">
        <h1>{event.title}</h1>

        <div className="event-detail-section">
          <div className="event-detail-label">Time</div>
          <div className="event-detail-value">
            {format(startTime, 'EEEE, MMMM d, yyyy')}
            <br />
            {format(startTime, 'HH:mm')} - {format(endTime, 'HH:mm')}
          </div>
        </div>

        {event.description && (
          <div className="event-detail-section">
            <div className="event-detail-label">Description</div>
            <div className="event-detail-value">{event.description}</div>
          </div>
        )}

        {event.location && (
          <div className="event-detail-section">
            <div className="event-detail-label">Location</div>
            <div className="event-detail-value">📍 {event.location}</div>
          </div>
        )}

        <div className="event-detail-actions">
          <button className="btn btn-primary" onClick={() => setShowEditor(true)}>
            Edit Event
          </button>
          <button className="btn btn-danger" onClick={handleDelete}>
            Delete Event
          </button>
        </div>
      </div>

      {showEditor && (
        <EventEditorModal
          event={event}
          onSave={handleSave}
          onDelete={handleDelete}
          onClose={() => setShowEditor(false)}
        />
      )}

      <NavBar />
    </div>
  )
}

