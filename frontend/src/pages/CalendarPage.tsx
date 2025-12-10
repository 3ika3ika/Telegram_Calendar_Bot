import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, startOfMonth, endOfMonth, addMonths, subMonths, startOfDay, isSameDay } from 'date-fns'
import { User, Event } from '../types/api'
import { apiClient } from '../services/api'
import { getCachedEvents, syncCacheWithApiEvents, removeEventFromCache, removeDeletedEventsFromCache, removeAllEventsNotInList } from '../services/cache'
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
  const loadEvents = async () => {
    const start = startOfMonth(currentDate)
    const end = endOfMonth(currentDate)
    
    try {
      setLoading(true)
      
      // Clear events state first to avoid showing stale data
      setEvents([])

      // Load from API first to get the most up-to-date data
      const response = await apiClient.listEvents({
        start_date: start.toISOString(),
        end_date: end.toISOString(),
      })

      // Set events immediately from API response (most up-to-date)
      setEvents(response.events)
      
      // Sync cache: remove deleted events and update with API response
      await syncCacheWithApiEvents(response.events, start, end)
      
      // Also load a wider range to clean up deleted events from cache
      // Load events from 1 year ago to 1 year ahead to catch all deleted events
      const wideStart = new Date(currentDate)
      wideStart.setFullYear(wideStart.getFullYear() - 1)
      const wideEnd = new Date(currentDate)
      wideEnd.setFullYear(wideEnd.getFullYear() + 1)
      
      try {
        const wideResponse = await apiClient.listEvents({
          start_date: wideStart.toISOString(),
          end_date: wideEnd.toISOString(),
        })
        const allEventIds = new Set(wideResponse.events.map(e => e.id))
        // Aggressively remove ALL cached events that are not in the API response
        await removeAllEventsNotInList(allEventIds)
      } catch (wideError) {
        // Ignore errors in wide range cleanup
        console.warn('Error cleaning up cache:', wideError)
      }
    } catch (error) {
      console.error('Error loading events:', error)
      // Fallback to cache if API fails
      try {
        const cached = await getCachedEvents(start, end)
        if (cached.length > 0) {
          setEvents(cached)
        }
      } catch (cacheError) {
        console.error('Error loading from cache:', cacheError)
      }
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

      // Sync cache for upcoming events range
      await syncCacheWithApiEvents(response.events, todayStart, futureDate)
      
      // Also get all events to clean up deleted ones from cache
      const allEventsResponse = await apiClient.listEvents({
        start_date: new Date(now.getFullYear() - 1, 0, 1).toISOString(), // 1 year ago
        end_date: futureDate.toISOString(),
      })
      const allEventIds = new Set(allEventsResponse.events.map(e => e.id))
      await removeDeletedEventsFromCache(allEventIds)

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

  const handleEventClick = async (event: Event) => {
    // Validate event still exists before navigating
    try {
      await apiClient.getEvent(event.id)
      navigate(`/event/${event.id}`)
    } catch (error: any) {
      if (error.response?.status === 404) {
        // Event was deleted, remove from cache and reload
        await removeEventFromCache(event.id)
        await loadEvents()
        await loadUpcomingEvents()
        alert('This event has been deleted.')
      } else {
        // Other error, still try to navigate
        navigate(`/event/${event.id}`)
      }
    }
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
      // Event was created/updated successfully, close the editor first
      setShowEditor(false)
      setSelectedEvent(null)
      setSelectedDate(null)
      // Then reload events in the background (don't fail if this errors)
      try {
        await loadEvents()
        await loadUpcomingEvents()
      } catch (reloadError) {
        console.warn('Event saved but failed to reload:', reloadError)
        // Don't throw - event was saved successfully
      }
    } catch (error) {
      console.error('Error saving event:', error)
      throw error
    }
  }

  const handleDeleteEvent = async (eventId: string) => {
    try {
      await apiClient.deleteEvent(eventId)
      // Remove from cache immediately
      await removeEventFromCache(eventId)
      // Remove from local state immediately to update UI
      setEvents(prevEvents => prevEvents.filter(e => e.id !== eventId))
      setUpcomingEvents(prevEvents => prevEvents.filter(e => e.id !== eventId))
      // Reload to ensure everything is in sync
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
          onAddEvent={(date: Date) => {
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

