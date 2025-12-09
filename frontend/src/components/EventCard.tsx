import { format, isToday, isTomorrow, isSameDay } from 'date-fns'
import { Event } from '../types/api'
import './EventCard.css'

interface EventCardProps {
  event: Event
  onClick: () => void
}

export default function EventCard({ event, onClick }: EventCardProps) {
  const startTime = new Date(event.start_time)
  const endTime = new Date(event.end_time)
  const isSameDayEvent = isSameDay(startTime, endTime)

  // Format date display
  let dateDisplay = ''
  if (isToday(startTime)) {
    dateDisplay = 'Today'
  } else if (isTomorrow(startTime)) {
    dateDisplay = 'Tomorrow'
  } else {
    dateDisplay = format(startTime, 'MMM d, yyyy')
  }

  return (
    <div className="event-card" onClick={onClick}>
      <div className="event-card-content">
        <div className="event-card-header">
          <div className="event-card-title">{event.title}</div>
          <div className="event-card-date">{dateDisplay}</div>
        </div>
        <div className="event-card-time-info">
          <div className="event-card-time">
            <span className="event-card-time-label">Start:</span>
            <span className="event-card-time-value">{format(startTime, 'HH:mm')}</span>
          </div>
          <div className="event-card-time">
            <span className="event-card-time-label">End:</span>
            <span className="event-card-time-value">{format(endTime, 'HH:mm')}</span>
            {!isSameDayEvent && (
              <span className="event-card-time-date"> ({format(endTime, 'MMM d')})</span>
            )}
          </div>
        </div>
        {event.description && (
          <div className="event-card-description">{event.description}</div>
        )}
        {event.location && (
          <div className="event-card-location">📍 {event.location}</div>
        )}
      </div>
    </div>
  )
}

