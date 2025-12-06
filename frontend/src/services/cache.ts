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

