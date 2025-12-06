# Telegram Calendar Bot - AI-Powered Calendar Assistant

A complete, production-capable Telegram Mini App with AI scheduling features. Built with Python (FastAPI) backend and React frontend.

## 🎯 Features

- **Telegram Mini App Integration**: Native Telegram authentication via WebApp API
- **AI-Powered Scheduling**: Natural language event creation, updates, and management
- **Full Calendar Views**: Month, week, and day views with event management
- **Smart Reminders**: Configurable reminders (15min, 1h, 24h) via Telegram bot
- **Recurring Events**: Support for daily, weekly, monthly, and custom recurrence
- **Conflict Detection**: Automatic conflict detection and resolution suggestions
- **Multi-tenant Architecture**: Single database with user-scoped data
- **Server-side Validation**: Enforced global rules and AI output validation

## 🏗️ Architecture

```
┌─────────────────┐
│  Telegram Mini  │
│  App (React)     │
│  (Frontend)      │
└────────┬─────────┘
         │
         │ HTTPS
         │
┌────────▼─────────┐
│   FastAPI Backend │
│   (Python)        │
└────────┬─────────┘
         │
    ┌────┴────┐
    │        │
┌───▼───┐ ┌─▼────┐
│Postgres│ │Redis │
│   DB   │ │(Opt) │
└────────┘ └──────┘
```

### Components

- **Frontend**: React + Vite, Telegram WebApp JS API
- **Backend**: FastAPI (async), SQLModel, Alembic migrations
- **Database**: PostgreSQL (Supabase/Postgres compatible)
- **AI**: OpenAI GPT-4o-mini with structured parsing
- **Background Jobs**: APScheduler for reminders
- **Telegram Bot**: For sending reminders and notifications

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (optional, for local development)
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key

## 🚀 Quick Start

### Local Development with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Telegram_Calendar_Bot
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your keys
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000 (if running separately)

### Manual Setup

#### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb telegram_calendar
   
   # Run migrations
   alembic upgrade head
   ```

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API URL
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

## 🔧 Configuration

### Environment Variables

#### Backend (`backend/.env`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/telegram_calendar

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_WEBAPP_SECRET=your_webapp_secret_from_botfather
TELEGRAM_BOT_WEBHOOK_SECRET=optional_webhook_secret

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# App
SECRET_KEY=your-secret-key-here
DEBUG=false
CORS_ORIGINS=["https://web.telegram.org","https://telegram.org"]

# Optional: Redis for rate limiting
REDIS_URL=redis://localhost:6379/0

# Optional: Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@example.com
```

#### Frontend (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Telegram Bot Setup

1. **Create a bot**
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command and follow instructions
   - Save the bot token

2. **Create a Mini App**
   - Use `/newapp` command in BotFather
   - Set the web app URL (your frontend URL)
   - Save the WebApp secret key

3. **Configure Webhook (optional)**
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://your-backend-url.com/api/v1/telegram/webhook"
   ```

## 📚 API Documentation

### Authentication

All API requests (except `/api/v1/users/session`) require the `X-Telegram-User-Id` header.

### Endpoints

#### Users

- `POST /api/v1/users/session` - Create/authenticate user via Telegram WebApp
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update user settings

#### Events

- `GET /api/v1/events` - List events (query params: `start_date`, `end_date`, `search`, `page`, `page_size`)
- `GET /api/v1/events/{id}` - Get event by ID
- `POST /api/v1/events` - Create event
- `PUT /api/v1/events/{id}` - Update event
- `DELETE /api/v1/events/{id}` - Delete event
- `POST /api/v1/events/apply_action` - Apply AI-generated action

#### AI

- `POST /api/v1/ai/parse` - Parse natural language into structured action

### Example Requests

#### Create Event

```bash
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-User-Id: 123456789" \
  -d '{
    "title": "Team Meeting",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T11:00:00Z",
    "reminder_offsets": [15, 60]
  }'
```

#### Parse Natural Language

```bash
curl -X POST "http://localhost:8000/api/v1/ai/parse" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-User-Id: 123456789" \
  -d '{
    "text": "Move dentist appointment to tomorrow at 5pm"
  }'
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest app/tests/ -v --cov=app
```

### Frontend Tests

```bash
cd frontend
npm run lint
npm run build
```

## 🚢 Deployment

### Backend Deployment (Render/Cloudflare Workers)

#### Render

1. **Create a new Web Service**
   - Connect your GitHub repository
   - Set build command: `cd backend && pip install -r requirements.txt && alembic upgrade head`
   - Set start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables from `.env.example`

2. **Set up PostgreSQL**
   - Create a PostgreSQL database in Render
   - Update `DATABASE_URL` in environment variables

3. **Deploy**
   - Push to main branch triggers automatic deployment

#### Cloudflare Workers (Alternative)

For Cloudflare Workers, you'll need to adapt the FastAPI app to use Cloudflare's runtime. Consider using [Cloudflare Workers for Python](https://developers.cloudflare.com/workers/languages/python/) or deploy as a regular service.

### Frontend Deployment (Vercel)

1. **Connect Repository**
   - Import your GitHub repository to Vercel
   - Set root directory to `frontend`

2. **Configure Build**
   - Build command: `npm run build`
   - Output directory: `dist`
   - Install command: `npm install`

3. **Environment Variables**
   - Add `VITE_API_BASE_URL` pointing to your backend URL

4. **Deploy**
   - Push to main branch triggers automatic deployment

5. **Update Telegram Bot**
   - Update Mini App URL in BotFather to your Vercel URL

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend alembic upgrade head
```

## 🔒 Security

### Best Practices

1. **Environment Variables**: Never commit `.env` files
2. **Secret Keys**: Use strong, random `SECRET_KEY` in production
3. **Telegram Verification**: Always verify `initData` signature server-side
4. **Rate Limiting**: Implement rate limiting (Redis recommended)
5. **HTTPS Only**: Use HTTPS in production
6. **CORS**: Restrict CORS origins to Telegram domains only
7. **Input Validation**: All user inputs are validated via Pydantic schemas
8. **AI Validation**: AI outputs are validated against global rules before application

### Master System Prompt

The system prompt is embedded in `app/ai/engine.py` and enforced server-side. Users cannot override global rules:

- Movement = Create new + Delete old (no duplicates)
- Conflict resolution with warnings
- Data integrity checks
- Privacy: only use stored context

## 📊 Database Schema

See `backend/alembic/versions/001_initial_schema.py` for the complete schema.

### Key Tables

- `users`: Telegram users
- `events`: Calendar events
- `reminders`: Event reminders
- `recurrencerules`: Recurrence patterns
- `audit_logs`: Action audit trail
- `subscription_plans`: Subscription tiers

## 🔄 Background Jobs

APScheduler runs background tasks:

- **Reminder Sender**: Checks every minute for due reminders
- **Cleanup Jobs**: (Optional) Archive old events, clean expired sessions

## 💳 Billing & Subscriptions

Subscription system is stubbed for future integration:

- `free`: Basic features, limited AI requests
- `pro`: Unlimited events, advanced AI features

To integrate Stripe:

1. Add Stripe SDK to `requirements.txt`
2. Create subscription endpoints in `app/api/v1/subscriptions.py`
3. Add webhook handler for Stripe events
4. Update user subscription status on payment

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check `DATABASE_URL` format
   - Ensure PostgreSQL is running
   - Verify database exists

2. **Telegram WebApp Not Working**
   - Ensure app is opened from Telegram
   - Check `TELEGRAM_WEBAPP_SECRET` matches BotFather
   - Verify CORS settings

3. **AI Parsing Fails**
   - Check `OPENAI_API_KEY` is valid
   - Verify API quota/limits
   - Check logs for OpenAI errors

4. **Reminders Not Sending**
   - Verify `TELEGRAM_BOT_TOKEN` is correct
   - Check scheduler is running (should see logs)
   - Ensure bot can send messages to users

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API examples in this README

## 🗺️ Roadmap

- [ ] Team/group calendar sharing
- [ ] Calendar export (iCal, Google Calendar)
- [ ] Email reminders
- [ ] Advanced recurrence patterns
- [ ] Time zone detection from Telegram
- [ ] Multi-language support
- [ ] Voice input for AI assistant
- [ ] Calendar analytics

---

**Built with ❤️ for Telegram users**

