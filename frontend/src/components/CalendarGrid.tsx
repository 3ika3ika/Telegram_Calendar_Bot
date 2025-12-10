import { useMemo } from 'react'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, startOfWeek, endOfWeek } from 'date-fns'
import { Event } from '../types/api'
import './CalendarGrid.css'

interface CalendarGridProps {
  currentDate: Date
  events: Event[]
  onDateClick: (date: Date) => void
  onEventClick: (event: Event) => void
}

export default function CalendarGrid({ currentDate, events, onDateClick, onEventClick }: CalendarGridProps) {
  const monthStart = startOfMonth(currentDate)
  const monthEnd = endOfMonth(currentDate)
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 }) // Monday
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 })

  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  const eventsByDate = useMemo(() => {
    const map = new Map<string, Event[]>()
    events.forEach((event) => {
      const date = new Date(event.start_time)
      const dateKey = format(date, 'yyyy-MM-dd')
      if (!map.has(dateKey)) {
        map.set(dateKey, [])
      }
      map.get(dateKey)!.push(event)
    })
    return map
  }, [events])

  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <div className="calendar-grid">
      <div className="calendar-header">
        {weekDays.map((day) => (
          <div key={day} className="calendar-weekday">
            {day}
          </div>
        ))}
      </div>
      <div className="calendar-body">
        {days.map((day) => {
          const dateKey = format(day, 'yyyy-MM-dd')
          const dayEvents = eventsByDate.get(dateKey) || []
          const isCurrentMonth = isSameMonth(day, currentDate)
          const isToday = isSameDay(day, new Date())

          return (
            <div
              key={day.toISOString()}
              className={`calendar-day ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}
              onClick={() => onDateClick(day)}
            >
              <div className="calendar-day-number">{format(day, 'd')}</div>
              <div className="calendar-day-events">
                {dayEvents.slice(0, 3).map((event) => (
                  <div
                    key={event.id}
                    className="calendar-event-dot"
                    onClick={(e) => {
                      e.stopPropagation()
                      onEventClick(event)
                    }}
                    title={event.title}
                  />
                ))}
                {dayEvents.length > 3 && (
                  <div className="calendar-event-more">+{dayEvents.length - 3}</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

