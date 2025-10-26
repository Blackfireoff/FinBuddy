# FinBuddy

FinBuddy is a multi-part application for wallet analysis and AI-driven transaction scoring. The repository contains:
- back/: Python FastAPI service (AI service, scoring, routes, schemas)
- front/: Next.js frontend (React + WebSocket AI analysis)
- compose.yml / compose_traefik.yml: Docker Compose setups to run the system

Quick start (recommended)
1. Copy or create a .env at repository root with any required secrets (example below).
2. Start all services with Docker Compose:
     sudo docker compose -f compose.yml up --build


Sample minimal .env
- Place at repository root as `.env`:
````bash
NEXT_PUBLIC_API_BASE=http://localhost:8000 #frontend url
OLLAMA_BASE_URL=http://localhost:11434 # For locally hosted OLLAMA AI
NEXT_PUBLIC_API_BASE=http://localhost:8001 # Backend url
```

