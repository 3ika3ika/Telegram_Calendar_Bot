import { format } from 'date-fns'
import { Event } from '../types/api'
import './EventEditorModal.css'

interface DayEventsModalProps {
  date: Date
  events: Event[]
  onClose: () => void
  onEventClick: (event: Event) => void
  onAddEvent: (date: Date) => void
}

export default function DayEventsModal({
  date,
  events,
  onClose,
  onEventClick,
  onAddEvent,
}: DayEventsModalProps) {
  const title = format(date, 'EEEE, MMMM d, yyyy')

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{title}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {events.length === 0 ? (
            <p style={{ color: '#666' }}>No events for this day.</p>
          ) : (
            <div className="day-events-list">
              {events.map((event) => {
                const start = new Date(event.start_time)
                const end = new Date(event.end_time)
                return (
                  <div
                    key={event.id}
                    className="day-event-item"
                    onClick={() => onEventClick(event)}
                    style={{
                      border: '1px solid var(--tg-theme-hint-color, #ccc)',
                      borderRadius: '8px',
                      padding: '0.75rem',
                      marginBottom: '0.5rem',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <div style={{ fontWeight: 600 }}>{event.title}</div>
                      <div style={{ color: 'var(--tg-theme-hint-color, #999)' }}>
                        {format(start, 'HH:mm')} - {format(end, 'HH:mm')}
                      </div>
                    </div>
                    {event.description && (
                      <div style={{ color: 'var(--tg-theme-hint-color, #999)', fontSize: '0.9rem' }}>
                        {event.description}
                      </div>
                    )}
                    {event.location && (
                      <div style={{ color: 'var(--tg-theme-hint-color, #999)', fontSize: '0.9rem' }}>
                        📍 {event.location}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="form-actions" style={{ justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <button className="btn btn-primary" onClick={() => onAddEvent(date)}>
            Add Event
          </button>
        </div>
      </div>
    </div>
  )
}

