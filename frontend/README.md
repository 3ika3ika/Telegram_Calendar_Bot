# Frontend - Telegram Calendar Mini App

React + Vite frontend for Telegram Mini App Calendar.

## Quick Start

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your API URL

# Run development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── CalendarGrid.tsx
│   │   ├── EventCard.tsx
│   │   ├── EventEditorModal.tsx
│   │   ├── NLPBox.tsx
│   │   ├── NavBar.tsx
│   │   └── TelegramLogin.tsx
│   ├── pages/               # Page components
│   │   ├── CalendarPage.tsx
│   │   ├── EventDetailPage.tsx
│   │   ├── SettingsPage.tsx
│   │   └── AIAssistantPage.tsx
│   ├── services/           # API client & cache
│   │   ├── api.ts
│   │   └── cache.ts
│   ├── types/              # TypeScript types
│   │   ├── api.ts
│   │   └── telegram.d.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Telegram WebApp Integration

The app uses Telegram WebApp JS API for:
- Authentication via `initData`
- Theme colors and styling
- Native Telegram UI elements
- User information

## Features

- **Calendar Views**: Month grid with event indicators
- **Event Management**: Create, edit, delete events
- **AI Assistant**: Natural language event creation
- **Local Caching**: IndexedDB for offline support
- **Responsive Design**: Optimized for mobile Telegram

## Building for Production

```bash
npm run build
```

Output: `dist/` directory

## Deployment to Vercel

1. Connect GitHub repository
2. Set root directory to `frontend`
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add environment variable: `VITE_API_BASE_URL`

## Environment Variables

- `VITE_API_BASE_URL`: Backend API URL (default: `http://localhost:8000`)

## Development

```bash
# Run dev server
npm run dev

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

