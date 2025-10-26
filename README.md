# FinBuddy

FinBuddy is a multi-part application for wallet analysis and AI-driven transaction scoring. The repository contains:
- back: Python FastAPI service (AI service, scoring, routes, schemas)
- front: Next.js frontend (React + WebSocket AI analysis)
- compose.yml : Docker Compose setups to run the system

## Big picture
- Backend (FastAPI) exposes REST + WebSocket endpoints (AI analysis at `/aiservice/analyse`). Container listens on port 8080 internally.
- Frontend (Next.js) is a React app that opens a WebSocket to the backend for streaming AI analysis results. The frontend is built with NEXT_PUBLIC_* env vars injected at build time.

## Prerequisites
- Docker and Docker Compose (v2) installed
- If using local AI (Ollama), have Ollama running and reachable

## Quick start (recommended)
1. Copy or create a `.env` at repository root (example below).
2. Start services:
   - Simple (no Traefik):
     sudo docker compose -f compose.yml up --build
   - With Traefik (reverse proxy / host routing):
     sudo docker compose -f compose_traefik.yml up --build

## .env (example)
Place at repository root as `.env`. Adjust values for your environment.

```
# backend
OLLAMA_BASE_URL=http://localhost:11434
CORS_ORIGIN=http://localhost:8000

# frontend (this is the value the frontend will use to call the backend from the browser)
NEXT_PUBLIC_API_BASE=http://localhost:8001
```

Notes:
- compose.yml maps container ports to host ports:
  - backend container port 8080 -> host 8001 (so browser/host uses http://localhost:8001)
  - frontend container port 3000 -> host 8000 (so browser/host uses http://localhost:8000)
- NEXT_PUBLIC_API_BASE is injected at frontend build time. Make sure `.env` has the correct value before building the frontend image.

