# VoxSpace (working title)

A local, voice-and-text-driven spatial design tool — Figma-style, starting in 2D — built to demonstrate agentic tool-use, contextual reference resolution, and a modular, swappable architecture (local vs. cloud LLM, 2D vs. 3D renderer).

**Purpose:** Portfolio piece for AI/ML Engineer roles, with real product potential.

## Core capability

Say or type "update the second circle" and have it work — which means the system needs to:
1. Turn voice into text (local STT)
2. Resolve "the second circle" to an actual object in the scene (reference resolution)
3. Decide what tool call that maps to (LLM agent loop)
4. Execute it against a shared scene model and re-render

## Tech stack

| Layer | Choice |
|---|---|
| Desktop shell | Electron |
| Frontend | React + TypeScript |
| Canvas engine | Konva.js (retained-mode scene graph) |
| Backend | Python + FastAPI |
| Speech-to-text | faster-whisper (local) |
| LLM | Provider adapter — Anthropic API (default) + Ollama local model (swap-in) |
| Frontend ↔ backend | WebSocket (localhost) |

Full rationale for each choice is in `ROADMAP.md`.

## Repo docs

- **`ROADMAP.md`** — the phased build plan (Phase 0 through Phase 6, July 11 – early August), with learn-first resources, build steps, and checkpoints per phase
- **`CLAUDE.md`** — working style for Claude Code sessions (plumbing-mode vs. core-learning-mode, checkpoint discipline)
- **`PROGRESS.md`** — running log of what's actually been built, updated at each milestone

## Getting started

**Backend** (FastAPI + WebSocket + STT):
```
conda activate voxspace   # conda create -n voxspace python=3.11 (one-time)
cd backend
python -m pip install -r requirements.txt   # one-time
python -m uvicorn app.main:app --port 8000
```

**Frontend** (Electron + React + TS):
```
cd frontend
npm install   # one-time
npm run dev
```

**LLM (local path)** — requires Ollama running with a model pulled:
```
brew services start ollama   # one-time background service
ollama pull qwen2.5:7b       # one-time, ~4.7GB, function-calling capable
```

## Status

Phase 0 (environment setup + concept grounding) complete — see `PROGRESS.md`. Phase 1 (static scene graph + manual 2D canvas) is next.

## Related project

This replaced the Agentic RAG System as the active build for July–early August. That project resumes afterward and reuses the same agent-loop pattern this one is built around (tool-use loop: context → LLM → tool call → execute).
