import axios, { AxiosInstance } from 'axios'
import { User, Event, EventCreate, EventUpdate, EventListResponse, AIActionResponse, AIParseRequest, AIApplyActionRequest } from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class APIClient {
  private client: AxiosInstance
  private telegramUserId: number | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth header
    this.client.interceptors.request.use((config) => {
      if (this.telegramUserId) {
        config.headers['X-Telegram-User-Id'] = this.telegramUserId.toString()
      }
      return config
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          console.error('Unauthorized - please re-authenticate')
        }
        return Promise.reject(error)
      }
    )
  }

  setTelegramUserId(userId: number) {
    this.telegramUserId = userId
  }

  async createSession(initData: string): Promise<User> {
    const response = await this.client.post<User>('/api/v1/users/session', {
      init_data: initData,
    })
    if (response.data) {
      this.setTelegramUserId(response.data.telegram_user_id)
    }
    return response.data
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/api/v1/users/me')
    return response.data
  }

  async updateUser(timezone?: string, metadata?: Record<string, any>): Promise<User> {
    const response = await this.client.put<User>('/api/v1/users/me', {
      timezone,
      metadata,
    })
    return response.data
  }

  async listEvents(params?: {
    start_date?: string
    end_date?: string
    search?: string
    page?: number
    page_size?: number
  }): Promise<EventListResponse> {
    const response = await this.client.get<EventListResponse>('/api/v1/events', { params })
    return response.data
  }

  async getEvent(eventId: string): Promise<Event> {
    const response = await this.client.get<Event>(`/api/v1/events/${eventId}`)
    return response.data
  }

  async createEvent(event: EventCreate): Promise<Event> {
    const response = await this.client.post<Event>('/api/v1/events', event)
    return response.data
  }

  async updateEvent(eventId: string, event: EventUpdate): Promise<Event> {
    const response = await this.client.put<Event>(`/api/v1/events/${eventId}`, event)
    return response.data
  }

  async deleteEvent(eventId: string): Promise<void> {
    await this.client.delete(`/api/v1/events/${eventId}`)
  }

  async parseAI(request: AIParseRequest): Promise<AIActionResponse> {
    const response = await this.client.post<AIActionResponse>('/api/v1/ai/parse', request)
    return response.data
  }

  async applyAIAction(action: AIApplyActionRequest): Promise<Event> {
    const response = await this.client.post<Event>('/api/v1/events/apply_action', action)
    return response.data
  }
}

export const apiClient = new APIClient()

