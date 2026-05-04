# AGENTS.md

## Project Rule

This repository is for ShipGuard Agent, a multi-agent delivery review system for vibe-coded projects.

## Coding Principles

1. Keep MVP small and shippable.
2. Do not add OCR, payment, login, or external SaaS dependencies in V1.
3. Do not automatically modify uploaded projects in V1.
4. Every review finding must be evidence-based.
5. Never print real secrets. Always redact secret-like values.
6. Prefer FastAPI + React + SQLite + LangGraph.
7. Keep the code easy for a teacher or reviewer to run locally.

## MVP Acceptance

A successful MVP can:

1. Accept a sample project zip
2. Analyze its structure
3. Detect missing delivery files
4. Detect obvious secret/local artifact risks
5. Generate P0/P1/P2 findings
6. Export a Markdown report

