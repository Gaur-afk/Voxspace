# Progress Log

## Phase 0 — Environment, Concept Grounding & Scaffolding
Status: complete (2026-07-12)

**Repo scaffold**
- Git repo initialized (`main` branch).
- `frontend/`: Electron + React + TypeScript, scaffolded via Vite (`react-ts` template), Electron main/preload wired through `vite-plugin-electron`. Konva + react-konva installed for Phase 1's canvas.
- `backend/`: Python + FastAPI, in a dedicated `voxspace` conda env (Python 3.11). `app/main.py` has a `/health` REST endpoint and a `/ws` WebSocket echo endpoint.

**Environment**
- Conda env `voxspace` (Python 3.11) created; `backend/requirements.txt` pins direct deps (fastapi, uvicorn[standard], websockets, python-multipart, pydantic, faster-whisper).
- Note: this machine's default `pip`/`uvicorn` on PATH resolve to a system Python 3.8 install ahead of conda in PATH order — use `python -m pip` / `python -m uvicorn` after `conda activate voxspace`, not the bare commands.

**LLM (local path)**
- Ollama installed via Homebrew, running as a background service (`brew services start ollama`).
- Pulled `qwen2.5:7b` (4.7GB) as the local function-calling model.
- Smoke-tested tool-calling via `/api/chat` with a `create_shape` tool schema (matching the roadmap's Phase 3 tool shape) — model correctly returned a structured `create_shape` call with the right arguments from a natural-language prompt.

**Speech-to-text**
- faster-whisper installed in the `voxspace` env.
- Smoke-tested end-to-end: generated a sample utterance with macOS `say` ("Create a blue circle and make the second rectangle bigger"), converted to WAV, transcribed with the `small` model (CPU, int8) — transcript matched exactly.
- Sample fixture at `backend/tests/fixtures/sample.wav` for reuse in Phase 2.

**WebSocket round trip**
- Backend `/ws` endpoint verified with a raw Python `websockets` client: sent a message, got `echo: <message>` back.
- Frontend `App.tsx` replaced with a minimal client that connects to `ws://localhost:8000/ws` on mount, sends a hello message, and displays connection status + echoed reply.
- Electron dev boot verified (main/renderer/GPU process tree came up correctly after fixing an ESM `__dirname` bug in `electron/main.ts` — the plugin bundles the main process as ESM since the frontend's `package.json` has `"type": "module"`).
- Not yet visually confirmed in an actual Electron window from this session (sandboxed, non-interactive) — next session should confirm `npm run dev` shows "Backend WebSocket status: open" and the echoed reply in the UI.

**Not done in this pass**
- No Ollama-vs-cloud provider abstraction yet (that's Phase 3b).
- No scene graph or manual canvas yet (that's Phase 1, next).

## Phase 1 — Static Scene Graph + Manual 2D Canvas
Status: not started
