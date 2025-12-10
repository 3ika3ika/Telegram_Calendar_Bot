import { format } from 'date-fns'
import { Event } from '../types/api'
import EventCard from './EventCard'
import './DayEventsModal.css'

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
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content day-events-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{format(date, 'EEEE, MMMM d, yyyy')}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          {events.length === 0 ? (
            <p style={{ color: '#666', padding: '1rem' }}>No events on this day</p>
          ) : (
            <div className="events-list">
              {events.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  onClick={() => {
                    onEventClick(event)
                    onClose()
                  }}
                />
              ))}
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          <button
            className="add-event-button"
            onClick={() => {
              onAddEvent(date)
            }}
          >
            Add Event
          </button>
        </div>
      </div>
    </div>
  )
}

