import { format } from 'date-fns'
import { Event } from '../types/api'
import './EventCard.css'

interface EventCardProps {
  event: Event
  onClick: () => void
}

export default function EventCard({ event, onClick }: EventCardProps) {
  const startTime = new Date(event.start_time)
  const endTime = new Date(event.end_time)

  return (
    <div className="event-card" onClick={onClick}>
      <div className="event-card-time">
        <div className="event-card-time-start">{format(startTime, 'HH:mm')}</div>
        {format(startTime, 'yyyy-MM-dd') !== format(endTime, 'yyyy-MM-dd') && (
          <div className="event-card-time-end">{format(endTime, 'HH:mm')}</div>
        )}
      </div>
      <div className="event-card-content">
        <div className="event-card-title">{event.title}</div>
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

