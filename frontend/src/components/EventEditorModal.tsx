import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { Event, EventCreate, EventUpdate } from '../types/api'
import './EventEditorModal.css'

interface EventEditorModalProps {
  event?: Event
  defaultDate?: Date
  onSave: (event: EventCreate | EventUpdate) => Promise<void>
  onDelete?: (eventId: string) => Promise<void>
  onClose: () => void
}

export default function EventEditorModal({
  event,
  defaultDate,
  onSave,
  onDelete,
  onClose,
}: EventEditorModalProps) {
  const [title, setTitle] = useState(event?.title || '')
  const [description, setDescription] = useState(event?.description || '')
  const [location, setLocation] = useState(event?.location || '')
  const [startDate, setStartDate] = useState(
    event ? format(new Date(event.start_time), "yyyy-MM-dd") : (defaultDate ? format(defaultDate, "yyyy-MM-dd") : format(new Date(), "yyyy-MM-dd"))
  )
  const [startTime, setStartTime] = useState(
    event ? format(new Date(event.start_time), "HH:mm") : "09:00"
  )
  const [endDate, setEndDate] = useState(
    event ? format(new Date(event.end_time), "yyyy-MM-dd") : (defaultDate ? format(defaultDate, "yyyy-MM-dd") : format(new Date(), "yyyy-MM-dd"))
  )
  const [endTime, setEndTime] = useState(
    event ? format(new Date(event.end_time), "HH:mm") : "10:00"
  )
  const [reminders, setReminders] = useState<number[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    // Load reminders if event exists
    // TODO: Load from event.reminders when available
  }, [event])

  const handleSave = async () => {
    if (!title.trim()) {
      alert('Please enter a title')
      return
    }

    const start = new Date(`${startDate}T${startTime}`)
    const end = new Date(`${endDate}T${endTime}`)

    if (end <= start) {
      alert('End time must be after start time')
      return
    }

    setSaving(true)
    try {
      if (event) {
        await onSave({
          title,
          description: description || undefined,
          location: location || undefined,
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          reminder_offsets: reminders,
        } as EventUpdate)
      } else {
        await onSave({
          title,
          description: description || undefined,
          location: location || undefined,
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          reminder_offsets: reminders,
        } as EventCreate)
      }
      onClose()
    } catch (error) {
      console.error('Error saving event:', error)
      alert('Failed to save event')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!event || !onDelete) return
    if (!confirm('Are you sure you want to delete this event?')) return

    try {
      await onDelete(event.id)
      onClose()
    } catch (error) {
      console.error('Error deleting event:', error)
      alert('Failed to delete event')
    }
  }

  const toggleReminder = (offset: number) => {
    setReminders((prev) =>
      prev.includes(offset) ? prev.filter((o) => o !== offset) : [...prev, offset]
    )
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{event ? 'Edit Event' : 'New Event'}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="form-group">
          <label className="form-label">Title *</label>
          <input
            type="text"
            className="form-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Event title"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Event description"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Location</label>
          <input
            type="text"
            className="form-input"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Event location"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Start</label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="date"
              className="form-input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <input
              type="time"
              className="form-input"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">End</label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="date"
              className="form-input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
            <input
              type="time"
              className="form-input"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Reminders</label>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {[15, 60, 1440].map((offset) => (
              <button
                key={offset}
                className={`btn ${reminders.includes(offset) ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => toggleReminder(offset)}
                style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
              >
                {offset < 60 ? `${offset}m` : offset < 1440 ? `${offset / 60}h` : `${offset / 1440}d`}
              </button>
            ))}
          </div>
        </div>

        <div className="form-actions">
          {event && onDelete && (
            <button className="btn btn-danger" onClick={handleDelete}>
              Delete
            </button>
          )}
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

