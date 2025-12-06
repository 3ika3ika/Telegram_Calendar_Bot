export interface User {
  id: number
  telegram_user_id: number
  username?: string
  first_name?: string
  last_name?: string
  language_code?: string
  timezone: string
  subscription_plan: string
  subscription_expires_at?: string
  created_at: string
}

export interface Event {
  id: string
  user_id: number
  team_id?: number
  title: string
  description?: string
  start_time: string
  end_time: string
  timezone: string
  location?: string
  recurrence_rule_id?: number
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface EventCreate {
  title: string
  description?: string
  start_time: string
  end_time: string
  timezone?: string
  location?: string
  recurrence_rule_id?: number
  reminder_offsets?: number[]
  metadata?: Record<string, any>
}

export interface EventUpdate {
  title?: string
  description?: string
  start_time?: string
  end_time?: string
  timezone?: string
  location?: string
  recurrence_rule_id?: number
  reminder_offsets?: number[]
  metadata?: Record<string, any>
}

export interface EventListResponse {
  events: Event[]
  total: number
  page: number
  page_size: number
}

export interface AIActionPayload {
  event_id?: string
  title?: string
  start_time?: string
  end_time?: string
  recurrence?: Record<string, any>
  reminders?: number[]
  message?: string
}

export interface AIActionResponse {
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'MOVE' | 'SUGGEST' | 'ASK' | 'NOOP' | 'CONFLICT'
  payload: AIActionPayload
  confidence: number
  summary: string
}

export interface AIApplyActionRequest {
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'MOVE' | 'SUGGEST' | 'ASK' | 'NOOP' | 'CONFLICT'
  payload: AIActionPayload
  original_text?: string
}

export interface AIParseRequest {
  text: string
  context_events?: Event[]
  user_memory?: Record<string, any>
}

