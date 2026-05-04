# ShipGuard Agent

ShipGuard Agent is a multi-agent delivery review system for vibe-coded projects.

## Positioning

ShipGuard Agent helps developers, students, and AI builders check whether their project is actually ready to ship.

It focuses on delivery readiness, not code generation.

## Core Problems

- Missing README
- Missing .env.example
- Missing Docker deployment
- Missing test command
- Hardcoded ports and local paths
- Secrets accidentally committed
- No teacher/client testing guide
- No clear project scope or known limitations

## MVP Goal

Upload or analyze a project repository, then generate a delivery review report.

The report should include:

- Project overview
- Tech stack detection
- Runbook check
- Environment variable check
- Docker readiness check
- Security risk scan
- Test readiness check
- P0/P1/P2 issue list
- Fix prompts for Trae/Cursor/Codex
- Markdown report export

## Multi-Agent Workflow

User -> Planner Agent -> Repo Reader Agent -> Runbook Agent -> Delivery Checklist Agent -> Security Agent -> Teacher/User Test Agent -> Fix Prompt Agent -> Validator Agent -> Report Agent

## MVP Boundary

Version 1 only reviews and reports.

It does not automatically modify the target project.

## Tech Stack Plan

- Backend: FastAPI
- Agent workflow: LangGraph
- Frontend: React + Vite
- Storage: SQLite
- Report export: Markdown
- Deployment: Docker + docker-compose
- Config: .env.example

## License

MIT

