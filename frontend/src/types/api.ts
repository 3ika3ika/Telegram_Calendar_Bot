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
