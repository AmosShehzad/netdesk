<div align="center">

# 🎯 NetDesk

### AI-Powered ISP Support Platform

*A production-grade helpdesk where an autonomous AI agent handles customer support end-to-end — classifying, investigating, and resolving tickets with RAG, tool use, and confidence-based escalation to human agents.*

[![Live Demo](https://img.shields.io/badge/Live_Demo-Visit_Site-6366F1?style=for-the-badge)](https://netdesk-black.vercel.app)
[![Backend](https://img.shields.io/badge/Backend_API-Online-10B981?style=for-the-badge)](https://netdesk-ptcx.onrender.com/api/docs/)
[![AI Service](https://img.shields.io/badge/AI_Service-Online-F59E0B?style=for-the-badge)](https://netdesk-ai.onrender.com/docs)

**[📺 Watch 2-min Demo](https://youtu.be/YOUR_VIDEO_ID)** · **[🚀 Try Live Site](https://netdesk-black.vercel.app)** · **[📖 API Docs](https://netdesk-ptcx.onrender.com/api/docs/)**

</div>

---

## 🔐 Demo Credentials

Try the live site with any of these accounts:

| Role | Registration Number | Password | What you'll see |
|---|---|---|---|
| **Admin** | `ADM-0001` | `Admin@123` | Full dashboard, all tickets, everything |
| **Manager** | `MGR-0001` | `Manager@123` | Analytics + team oversight |
| **Support Agent** | `AGT-0001` | `Agent@123` | SLA-sorted triage queue |
| **Technician** | `TEC-0001` | `Tech@123` | Field-work assignments |
| **Customer** | `CUST-2026-00001` | `Customer@123` | Portal + live chat with AI |

> ⏳ **Note:** Backend spins down after 15 min of inactivity (Render free tier). First request may take ~30s to wake up.

---

## ✨ What makes this project stand out

- **🤖 Real agentic AI** — not just an API wrapper. A LangGraph agent with conditional routing, 5 tools (billing, outages, KB search, diagnostics, escalation), FAISS-based RAG, and confidence-scored decisions.
- **⚡ Real-time everything** — Django Channels + Daphne over authenticated WebSockets. Comments and notifications push instantly, no polling.
- **📊 Staff intelligence layer** — Recharts dashboard, SLA-urgency triage queue, internal notes, auto-assignment for high-priority tickets.
- **🏗️ Production architecture** — 3 containerized services, JWT auth, role-based access, rate limiting, audit trails, OpenAPI docs.

---

## 🎥 Demo Video

[![NetDesk Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg)](https://youtu.be/YOUR_VIDEO_ID)

*Click to watch (2 min) — shows the AI agent, real-time chat, staff dashboard, and agent queue.*

---

## 🧠 AI Architecture

The AI service isn't a prompt wrapper — it's a **stateful agent** built with LangGraph that makes decisions and uses tools:

```
                    Customer message
                          │
                          ▼
                 ┌────────────────┐
                 │ Understand     │  Classify intent + priority
                 │ Intent (LLM)   │
                 └────────┬───────┘
                          │
        ┌─────────┬───────┼───────┬──────────┐
        ▼         ▼       ▼       ▼          ▼
    ┌────────┐┌───────┐┌───────┐┌────────┐┌────────┐
    │Billing ││Outage ││ KB    ││Diagnose││Ticket  │
    │Tool    ││Check  ││Search ││Steps   ││History │
    └────┬───┘└───┬───┘└───┬───┘└────┬───┘└────┬───┘
         └────────┴────────┼─────────┴─────────┘
                           ▼
                 ┌────────────────┐
                 │ Evaluate       │  Confidence score
                 │ Confidence     │
                 └────────┬───────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
      ┌────────────┐          ┌───────────────┐
      │ Generate   │          │ Escalate to   │
      │ Reply      │          │ Human + write │
      │            │          │ summary       │
      └────────────┘          └───────────────┘
```

**Key techniques:**
- **RAG:** FAISS vector store over 6 ISP troubleshooting documents, chunked with overlap, retrieved with `fastembed` (all-MiniLM-L6-v2, ~100MB — fits on free-tier Render)
- **Tool use:** Real Python functions the agent calls — checks the actual DB for outages, bills, ticket history
- **Escalation logic:** When confidence drops or the agent can't find a tool that fits, it writes a summary of what it tried and hands off to a human agent

---

## 🏗️ System Architecture

```
┌──────────────────┐     HTTPS     ┌──────────────────────┐
│                  │◄──────────────►│                     │
│  React + Vite    │                │  Django REST + DRF  │
│   (Vercel)       │◄─── WSS ─────►│  + Channels + Daphne │
│                  │                │  (Render)            │
└──────────────────┘                └──────┬───────────────┘
                                           │
                       ┌───────────────────┼────────────────┐
                       │                   │                │
                       ▼                   ▼                ▼
                 ┌───────────┐      ┌──────────────┐  ┌──────────┐
                 │ Supabase  │      │ FastAPI + AI │  │ Whitenoise│
                 │ Postgres  │      │  LangGraph   │  │  Static   │
                 │           │      │   (Render)   │  │           │
                 └───────────┘      └──────┬───────┘  └──────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ Groq LLM API │
                                    │ FAISS RAG    │
                                    └──────────────┘
```

---

## 🧰 Tech Stack

### Backend (`/backend`)
- **Django 6** + **Django REST Framework** — API layer with 30+ endpoints
- **Django Channels + Daphne** — ASGI WebSocket server for real-time messaging
- **PostgreSQL** (Supabase) — managed database
- **Simple JWT** — authentication with token rotation + blacklist
- **drf-spectacular** — auto-generated OpenAPI 3.0 docs
- **django-jazzmin** — modern admin theme

### AI Service (`/ai-service`)
- **FastAPI** + **Uvicorn** — async ASGI microservice
- **LangGraph** — stateful multi-node agent orchestration
- **LangChain** — LLM abstractions and prompt management
- **Groq API** — LLM inference (Llama 3.1 70B)
- **FAISS** + **fastembed** — vector search and lightweight embeddings

### Frontend (`/frontend`)
- **React 18** + **Vite** — modern build + HMR
- **React Router** — client-side routing with role guards
- **Recharts** — dashboard visualizations
- **Axios** — HTTP client with JWT refresh interceptor
- **lucide-react** — icon library
- **Native WebSocket** with custom auto-reconnecting hook

### Infrastructure
- **Render** (backend + AI service, Docker)
- **Vercel** (frontend)
- **Supabase** (Postgres)
- **GitHub Actions** — ready for CI (Dockerfile committed)

---

## 🎨 Features

### For Customers
- 🎫 Create tickets, chat live with AI agent
- 🔔 Real-time notifications when staff respond
- ⭐ Rate resolved tickets 1–5 with feedback
- 📱 Mobile-responsive with dark/light theme
- 🔒 Force password change on first login

### For Staff (Agents, Managers, Admins)
- 📊 **Staff Dashboard** — 6 KPIs + 5 Recharts (30-day volume, status donut, priority bars, agent workload, AI performance)
- 🚨 **Agent Queue** — active tickets sorted by SLA urgency, breach highlighting, quick actions (assign, escalate, mark in progress)
- 🔐 **Internal Notes** — staff-only tabbed panel on every ticket, invisible to customers
- ⏱️ **Auto-SLA tracking** — priority-based deadlines (Critical 4h, High 8h, Medium 24h, Low 72h)
- 👥 **Role-based access** — Customer / Support Agent / Technician / Manager / Admin
- 📡 **Outage management** — publish network incidents that the AI cross-references

### System
- 🔄 **Real-time WebSockets** — per-ticket and per-user broadcast groups
- 🧾 **Full audit trail** — every action logged (creation, assignment, AI action, escalation, resolution)
- 🚦 **Rate limiting** — 20/min for anonymous, 100/min for authenticated
- 📄 **OpenAPI docs** — Swagger UI at `/api/docs/`

---

## 📸 Screenshots

> _Add screenshots here after recording — I'd suggest 4–6 hero shots:_
> _1. Staff Dashboard  2. Agent Queue  3. Ticket with AI conversation  4. Internal Notes tab  5. Customer Portal  6. API Docs_

---

## 🚀 Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL (or use a Supabase account)
- A Groq API key ([get one here](https://console.groq.com))

### 1. Clone
```bash
git clone https://github.com/AmosShehzad/netdesk.git
cd netdesk
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Copy .env.example and fill in your values
cp .env.example .env

python manage.py migrate
python manage.py seed_demo     # loads realistic demo data
python manage.py runserver
```

### 3. AI Service (new terminal)
```bash
cd ai-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set GROQ_API_KEY in .env
cp .env.example .env

uvicorn app.main:app --reload --port 8001
```

### 4. Frontend (new terminal)
```bash
cd frontend
npm install
cp .env.example .env           # points to localhost by default
npm run dev
```

Open http://localhost:5173 and log in with any demo account above.

---

## 📁 Project Structure

```
netdesk/
├── backend/                 # Django REST + Channels
│   ├── core/                # settings, ASGI, URLs
│   ├── users/               # custom User model, JWT auth
│   ├── tickets/             # tickets, comments, notes, outages, ratings
│   │   ├── consumers.py     # WebSocket consumers
│   │   ├── signals.py       # broadcast on comment/notification create
│   │   ├── ws_auth.py       # JWT auth middleware for WS
│   │   └── management/commands/seed_demo.py
│   ├── notifications/       # notification model + signal
│   └── billing/             # bills
│
├── ai-service/              # FastAPI + LangGraph
│   └── app/
│       ├── graph/           # LangGraph pipeline, nodes, state
│       ├── tools/           # billing, outage, KB, diagnostic tools
│       ├── knowledge_base/  # FAISS index + docs
│       └── routers/         # /ai/analyze endpoint
│
└── frontend/                # React + Vite
    └── src/
        ├── pages/           # Login, Portal, Tickets, StaffDashboard, AgentQueue
        ├── components/      # Layout, NotificationBell
        ├── context/         # Auth, Theme, Toast
        ├── hooks/           # useWebSocket
        └── api/             # axios client with JWT refresh
```

---

## 🗺️ Roadmap

- [ ] Swap FAISS in-memory to Qdrant for production scale
- [ ] Migrate to Redis channel layer for multi-worker deployment
- [ ] Add file attachment support with S3-compatible storage
- [ ] Email notifications via Brevo
- [ ] Comprehensive test coverage (currently manual QA)
- [ ] CI/CD via GitHub Actions

---

## 📝 License

MIT

---

<div align="center">

**Built by [Amos Shehzad](https://github.com/AmosShehzad)** · [LinkedIn](YOUR_LINKEDIN_URL)

*If this helped or impressed you, a ⭐ on the repo means a lot!*

</div>
