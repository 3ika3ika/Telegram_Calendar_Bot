import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, startOfMonth, endOfMonth, addMonths, subMonths, startOfDay, isSameDay } from 'date-fns'
import { User, Event } from '../types/api'
import { apiClient } from '../services/api'
import { getCachedEvents, cacheEvents } from '../services/cache'
import CalendarGrid from '../components/CalendarGrid'
import EventCard from '../components/EventCard'
import EventEditorModal from '../components/EventEditorModal'
import DayEventsModal from '../components/DayEventsModal'
import NavBar from '../components/NavBar'
import './CalendarPage.css'

interface CalendarPageProps {
  user: User
}

export default function CalendarPage({}: CalendarPageProps) {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [events, setEvents] = useState<Event[]>([])
  const [upcomingEvents, setUpcomingEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)
  const [showEditor, setShowEditor] = useState(false)
  const [showDayModal, setShowDayModal] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadEvents()
  }, [currentDate])

  useEffect(() => {
    // Load upcoming events on mount and refresh periodically
    loadUpcomingEvents()
    const interval = setInterval(() => {
      loadUpcomingEvents()
    }, 60000) // Refresh every minute
    
    return () => clearInterval(interval)
  }, [])

  const loadEvents = async () => {
    try {
      setLoading(true)
      const start = startOfMonth(currentDate)
      const end = endOfMonth(currentDate)

      // Try cache first
      const cached = await getCachedEvents(start, end)
      if (cached.length > 0) {
        setEvents(cached)
      }

      // Load from API
      const response = await apiClient.listEvents({
        start_date: start.toISOString(),
        end_date: end.toISOString(),
      })

      setEvents(response.events)
      await cacheEvents(response.events)
    } catch (error) {
      console.error('Error loading events:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadUpcomingEvents = async () => {
    try {
      const now = new Date()
      const todayStart = startOfDay(now) // Start of today (00:00:00)
      const futureDate = new Date(now)
      futureDate.setMonth(futureDate.getMonth() + 3) // Load next 3 months

      // Load upcoming events from start of today onwards (includes all of today's events)
      // We use start_date to get events that start from today, but we'll filter by end_time
      const response = await apiClient.listEvents({
        start_date: todayStart.toISOString(),
        end_date: futureDate.toISOString(),
      })

      // Filter to only show events that haven't ended yet
      // API returns UTC times (may or may not have 'Z' suffix)
      const filtered = response.events
        .filter((e) => {
          // Parse end time - if no timezone, assume UTC
          let eventEndStr = e.end_time
          if (!eventEndStr.includes('Z') && !eventEndStr.includes('+') && !eventEndStr.includes('-', 10)) {
            eventEndStr = eventEndStr + 'Z'
          }
          const eventEnd = new Date(eventEndStr)
          // Show events that haven't ended yet
          return eventEnd.getTime() >= now.getTime()
        })
        .sort((a, b) => {
          let aStartStr = a.start_time
          let bStartStr = b.start_time
          if (!aStartStr.includes('Z') && !aStartStr.includes('+') && !aStartStr.includes('-', 10)) {
            aStartStr = aStartStr + 'Z'
          }
          if (!bStartStr.includes('Z') && !bStartStr.includes('+') && !bStartStr.includes('-', 10)) {
            bStartStr = bStartStr + 'Z'
          }
          return new Date(aStartStr).getTime() - new Date(bStartStr).getTime()
        })

      setUpcomingEvents(filtered)
    } catch (error) {
      console.error('Error loading upcoming events:', error)
    }
  }

  const handleDateClick = (date: Date) => {
    setSelectedDate(date)
    setShowDayModal(true)
  }

  const handleEventClick = (event: Event) => {
    navigate(`/event/${event.id}`)
  }

  const dayEvents = useMemo(() => {
    if (!selectedDate) return []
    return events
      .filter((e) => isSameDay(new Date(e.start_time), selectedDate))
      .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  }, [events, selectedDate])

  const handleSaveEvent = async (eventData: any) => {
    try {
      if (selectedEvent) {
        await apiClient.updateEvent(selectedEvent.id, eventData)
      } else {
        await apiClient.createEvent(eventData)
      }
      await loadEvents()
      await loadUpcomingEvents()
      setShowEditor(false)
      setSelectedEvent(null)
      setSelectedDate(null)
    } catch (error) {
      console.error('Error saving event:', error)
      throw error
    }
  }

  const handleDeleteEvent = async (eventId: string) => {
    try {
      await apiClient.deleteEvent(eventId)
      await loadEvents()
      await loadUpcomingEvents()
      setShowEditor(false)
      setSelectedEvent(null)
    } catch (error) {
      console.error('Error deleting event:', error)
      throw error
    }
  }

  return (
    <div className="calendar-page">
      <div className="calendar-header">
        <button onClick={() => setCurrentDate(subMonths(currentDate, 1))}>‹</button>
        <h1>{format(currentDate, 'MMMM yyyy')}</h1>
        <button onClick={() => setCurrentDate(addMonths(currentDate, 1))}>›</button>
      </div>

      {loading ? (
        <div className="loading">Loading events...</div>
      ) : (
        <>
          <CalendarGrid
            currentDate={currentDate}
            events={events}
            onDateClick={handleDateClick}
            onEventClick={handleEventClick}
          />

          <div className="events-list">
            <h2>Upcoming Events</h2>
            {upcomingEvents.slice(0, 5).map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onClick={() => handleEventClick(event)}
              />
            ))}
            {upcomingEvents.length === 0 && (
              <p style={{ color: '#666', padding: '1rem' }}>No upcoming events</p>
            )}
          </div>
        </>
      )}

      {showEditor && (
        <EventEditorModal
          event={selectedEvent || undefined}
          defaultDate={selectedDate || undefined}
          onSave={handleSaveEvent}
          onDelete={selectedEvent ? handleDeleteEvent : undefined}
          onClose={() => {
            setShowEditor(false)
            setSelectedEvent(null)
            setSelectedDate(null)
          }}
        />
      )}

      {showDayModal && selectedDate && (
        <DayEventsModal
          date={selectedDate}
          events={dayEvents}
          onClose={() => setShowDayModal(false)}
          onEventClick={handleEventClick}
          onAddEvent={(date) => {
            setSelectedDate(date)
            setShowDayModal(false)
            setShowEditor(true)
          }}
        />
      )}

      <NavBar />
    </div>
  )
}

