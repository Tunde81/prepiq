# PrepIQ — UK National Cyber Preparedness Learning Platform

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Made in UK](https://img.shields.io/badge/Made%20in-UK-red.svg)](https://www.fa3tech.io)
[![Live Platform](https://img.shields.io/badge/Live-prepiq.fa3tech.io-00d4ff.svg)](https://prepiq.fa3tech.io)

> Free and open source cybersecurity preparedness platform for UK SMEs, educational institutions, and public sector organisations.

## What is PrepIQ?

PrepIQ is a full-stack cyber preparedness learning platform built specifically for the UK regulatory environment. It helps organisations assess their cyber posture, train their teams, simulate real incidents, and generate compliance evidence — all in one place.

**Live platform:** [prepiq.fa3tech.io](https://prepiq.fa3tech.io)

## Features

| Feature | Description |
|---|---|
| 🇬🇧 UK SME Cyber Health Index | 35-question assessment across 10 domains, benchmarked against UK SME peers |
| ⚡ Cyber Incident Simulator | 6 realistic UK scenarios with tabletop, timed challenges, and AI debrief |
| 🎣 Phishing Simulator | Send simulated campaigns with 8 UK-relevant templates, track click rates |
| 📋 Learning Modules | Structured courses with quizzes, certificates, and badges |
| 🤖 CyberCoach AI | AI-powered cybersecurity mentor powered by Claude |
| 📊 Board Reports | One-click PDF reports for board-level and compliance submissions |
| 🔔 Notifications | Automated email notifications for completions, badges, and reminders |
| 👥 Organisation Management | Multi-org support with user management and analytics |

## Regulatory Alignment

- **NCSC Cyber Essentials** — technical controls mapping
- **UK GDPR & Data Protection Act 2018** — data protection obligations
- **FCA SYSC 13** — operational resilience for regulated firms
- **NIST Cybersecurity Framework** — risk management structure
- **ISO 27001** — information security management
- **DORA** — digital operational resilience for financial entities

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Database | PostgreSQL + Redis + MongoDB |
| AI | Anthropic Claude API |
| Email | Resend API |
| Infrastructure | Docker Compose on Ubuntu VPS |
| PDF Generation | ReportLab |

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.12+
- Node.js 20+

### Installation
```bash
git clone https://github.com/Tunde81/prepiq.git
cd prepiq
cp .env.example .env
# Edit .env with your API keys
docker compose up -d
```

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://prepiq:password@db:5432/prepiq
REDIS_URL=redis://redis:6379
MONGODB_URL=mongodb://mongo:27017

# AI
ANTHROPIC_API_KEY=sk-ant-...

# Email
RESEND_API_KEY=re_...
MAIL_FROM=noreply@yourdomain.com

# Security
SECRET_KEY=your-secret-key
FRONTEND_URL=https://yourdomain.com
```

### Database Setup
```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Seed initial data
docker compose exec backend python3 seed_questions.py
docker compose exec backend python3 seed_scenarios.py
```

## Project Structure
```
prepiq/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Config, database, security
│   │   ├── features/     # Feature modules (health index, simulator, phishing)
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Email, notifications, events
│   └── migrations/       # Alembic migrations
├── frontend/
│   ├── src/
│   │   ├── pages/        # React page components
│   │   ├── components/   # Shared components
│   │   ├── store/        # Zustand state management
│   │   └── utils/        # API client, helpers
│   └── public/
└── docker-compose.yml
```

## API Documentation

When running locally, API docs are available at:
- Swagger UI: `http://localhost:5010/api/docs`
- ReDoc: `http://localhost:5010/api/redoc`

## Contributing

PrepIQ is open source and welcomes contributions. Areas where help is most valuable:

- Additional incident simulator scenarios
- New phishing email templates
- Learning module content
- Translations (Welsh, Scottish Gaelic)
- Accessibility improvements
- Additional regulatory framework mappings

Please open an issue before submitting a pull request for significant changes.

## Licence

Copyright 2025 [Fa3Tech Limited](https://www.fa3tech.io)

Licensed under the [Apache License 2.0](LICENSE).

You are free to use, modify, and distribute this software for any purpose, including commercially, provided you include the original licence and copyright notice.

## About

PrepIQ is built and maintained by [Fa3Tech Limited](https://www.fa3tech.io), a UK cybersecurity and IT consulting firm based in London.

- **Website:** [fa3tech.io](https://www.fa3tech.io)
- **Platform:** [prepiq.fa3tech.io](https://prepiq.fa3tech.io)
- **Contact:** info@fa3tech.io

---

*PrepIQ is free for all UK organisations. If you find it valuable, consider [contributing](#contributing) or sharing it with your network.*
