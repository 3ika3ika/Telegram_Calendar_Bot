import { openDB, DBSchema, IDBPDatabase } from 'idb'
import { Event } from '../types/api'

interface CalendarDBSchema extends DBSchema {
  events: {
    key: string
    value: Event
    indexes: { 'by-start-time': string }
  }
  cache: {
    key: string
    value: {
      key: string
      data: any
      timestamp: number
    }
  }
}

let db: IDBPDatabase<CalendarDBSchema> | null = null

export async function initCache() {
  if (db) return db

  db = await openDB<CalendarDBSchema>('telegram-calendar', 1, {
    upgrade(db) {
      // Events store
      if (!db.objectStoreNames.contains('events')) {
        const eventStore = db.createObjectStore('events', { keyPath: 'id' })
        eventStore.createIndex('by-start-time', 'start_time')
      }

      // Cache store for other data
      if (!db.objectStoreNames.contains('cache')) {
        db.createObjectStore('cache', { keyPath: 'key' })
      }
    },
  })

  return db
}

export async function cacheEvents(events: Event[]) {
  const database = await initCache()
  const tx = database.transaction('events', 'readwrite')
  
  for (const event of events) {
    await tx.store.put(event)
  }
  
  await tx.done
}

export async function removeEventFromCache(eventId: string) {
  const database = await initCache()
  const tx = database.transaction('events', 'readwrite')
  await tx.store.delete(eventId)
  await tx.done
}

export async function syncCacheWithApiEvents(apiEvents: Event[], startDate: Date, endDate: Date) {
  const database = await initCache()
  const tx = database.transaction('events', 'readwrite')
  const index = tx.store.index('by-start-time')
  
  // Get all cached events in the date range
  const startKey = startDate.toISOString()
  const endKey = endDate.toISOString()
  const cachedEventIds = new Set<string>()
  
  let cursor = await index.openCursor(IDBKeyRange.bound(startKey, endKey))
  while (cursor) {
    cachedEventIds.add(cursor.value.id)
    cursor = await cursor.continue()
  }
  
  // Create set of API event IDs
  const apiEventIds = new Set(apiEvents.map(e => e.id))
  
  // Remove cached events in the date range that are not in the API response (deleted events)
  for (const cachedId of cachedEventIds) {
    if (!apiEventIds.has(cachedId)) {
      await tx.store.delete(cachedId)
    }
  }
  
  // Add/update events from API
  for (const event of apiEvents) {
    await tx.store.put(event)
  }
  
  await tx.done
}

export async function removeDeletedEventsFromCache(apiEventIds: Set<string>) {
  const database = await initCache()
  const tx = database.transaction('events', 'readwrite')
  
  // Get all cached event IDs
  const allCachedIds: string[] = []
  let cursor = await tx.store.openCursor()
  while (cursor) {
    allCachedIds.push(cursor.value.id)
    cursor = await cursor.continue()
  }
  
  // Remove any cached events that are not in the API response
  for (const cachedId of allCachedIds) {
    if (!apiEventIds.has(cachedId)) {
      await tx.store.delete(cachedId)
    }
  }
  
  await tx.done
}

export async function getCachedEvents(startDate: Date, endDate: Date): Promise<Event[]> {
  const database = await initCache()
  const tx = database.transaction('events', 'readonly')
  const index = tx.store.index('by-start-time')
  
  const startKey = startDate.toISOString()
  const endKey = endDate.toISOString()
  
  const events: Event[] = []
  let cursor = await index.openCursor(IDBKeyRange.bound(startKey, endKey))
  
  while (cursor) {
    events.push(cursor.value)
    cursor = await cursor.continue()
  }
  
  await tx.done
  return events
}

export async function clearCache() {
  const database = await initCache()
  await database.clear('events')
  await database.clear('cache')
}

export async function clearEventsCache() {
  const database = await initCache()
  await database.clear('events')
}

export async function removeAllEventsNotInList(validEventIds: Set<string>) {
  /**
   * Aggressively remove all cached events that are not in the provided list.
   * This is more thorough than removeDeletedEventsFromCache as it ensures
   * complete synchronization.
   */
  const database = await initCache()
  const tx = database.transaction('events', 'readwrite')
  
  // Get all cached event IDs
  const allCachedIds: string[] = []
  let cursor = await tx.store.openCursor()
  while (cursor) {
    allCachedIds.push(cursor.value.id)
    cursor = await cursor.continue()
  }
  
  // Remove any cached events that are not in the valid list
  for (const cachedId of allCachedIds) {
    if (!validEventIds.has(cachedId)) {
      await tx.store.delete(cachedId)
    }
  }
  
  await tx.done
}

