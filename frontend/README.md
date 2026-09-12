# TaskMate — React Frontend

This directory contains the client-side single page application (SPA) for **TaskMate**, built with **React 19**, **TypeScript**, **Vite**, and **Tailwind CSS**.

## Structure

```text
frontend/
├── src/
│   ├── components/        # UI components (Header, KanbanBoard, WorkspaceView, etc.)
│   ├── context/           # AppContext state management
│   ├── data/              # Mock dataset seeds for local development
│   ├── services/          # Client API services (to connect to backend in Phase 10)
│   ├── utils/             # Formatters and date helpers
│   ├── App.tsx            # Main shell component
│   ├── main.tsx           # Application DOM mount
│   ├── index.css          # Tailwind CSS definitions
│   └── types.ts           # Central TypeScript types
├── index.html             # HTML entry point
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite bundler configuration
├── tsconfig.json          # TypeScript compiler options
└── .env.example           # Client environment template
```

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```
