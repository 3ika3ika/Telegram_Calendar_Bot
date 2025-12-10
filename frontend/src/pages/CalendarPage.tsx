import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns'
import { User, Event } from '../types/api'
import { apiClient } from '../services/api'
import { getCachedEvents, cacheEvents } from '../services/cache'
import CalendarGrid from '../components/CalendarGrid'
import EventCard from '../components/EventCard'
import EventEditorModal from '../components/EventEditorModal'
import NavBar from '../components/NavBar'
import './CalendarPage.css'

interface CalendarPageProps {
  user: User
}

export default function CalendarPage({ user }: CalendarPageProps) {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)
  const [showEditor, setShowEditor] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadEvents()
  }, [currentDate])

<<<<<<< Updated upstream
=======
  useEffect(() => {
    // Load upcoming events on mount and refresh periodically
    loadUpcomingEvents()
    const interval = setInterval(() => {
      loadUpcomingEvents()
    }, 60000) // Refresh every minute
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Refresh events when page becomes visible (user returns to tab)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadEvents()
        loadUpcomingEvents()
      }
    }

    // Refresh on focus (user clicks on window/tab)
    const handleFocus = () => {
      loadEvents()
      loadUpcomingEvents()
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('focus', handleFocus)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('focus', handleFocus)
    }
  }, [currentDate])

>>>>>>> Stashed changes
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

  const handleDateClick = (date: Date) => {
    setSelectedDate(date)
    setShowEditor(true)
  }

  const handleEventClick = (event: Event) => {
    navigate(`/event/${event.id}`)
  }

  const handleSaveEvent = async (eventData: any) => {
    try {
      if (selectedEvent) {
        await apiClient.updateEvent(selectedEvent.id, eventData)
      } else {
        await apiClient.createEvent(eventData)
      }
      await loadEvents()
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
            {events
              .filter((e) => new Date(e.start_time) >= new Date())
              .slice(0, 5)
              .map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  onClick={() => handleEventClick(event)}
                />
              ))}
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

      <NavBar />
    </div>
  )
}

