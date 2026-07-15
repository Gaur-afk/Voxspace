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
- Electron dev boot verified (main/renderer/GPU process tree came up correctly after fixing an ESM `__dirname` bug in `electron/main.ts` — the plugin initially bundled the main process as ESM since the frontend's `package.json` had `"type": "module"`).
- User ran it for real and caught a second bug from the same root cause: preload script failed to load (`ENOENT ... dist-electron/preload.js`) because the ESM build emitted `preload.mjs` while `main.ts` hardcoded `preload.js`. Fix: removed `"type": "module"` from `frontend/package.json` entirely (it only affected the Electron main/preload build, not the renderer, which Vite controls independently) and reverted the `__dirname` shim back to plain `__dirname` — main/preload now build as CommonJS matching Electron's expectations. Verified `dist-electron/preload.js` exists at the correct path afterward.
- User opened a real Electron window and caught the preload bug above via devtools console; after the fix, confirmed the window shows "Backend WebSocket status: open" and "Reply from backend: echo: hello from VoxSpace frontend" — round trip proven end-to-end in a real GUI window, not just via a raw test client.
- Two benign items remain in the devtools console: (1) a CSP security warning — expected in dev (no policy set yet), disappears once packaged; (2) a one-time "WebSocket is closed before the connection is established" warning — a side effect of React StrictMode's intentional double-mount-in-dev behavior (mount → cleanup closes the first socket before it finishes connecting → real mount succeeds). Neither needs fixing.

**Not done in this pass**
- No Ollama-vs-cloud provider abstraction yet (that's Phase 3b).
- No scene graph or manual canvas yet (that's Phase 1, next).

## Phase 1 — Static Scene Graph + Manual 2D Canvas
Status: complete (2026-07-12)

**Sync protocol decision**
- Chose pure WebSocket over a REST+WebSocket hybrid: all CRUD (`create_object`, `update_object`, `delete_object`) travels as typed JSON messages over the single WS connection; the backend responds to every mutation (and to every new connection) by broadcasting the *full* current scene state to all connected clients. One channel to reason about, and it's the same channel Phase 3's tool-call execution will push updates through later — no second protocol to keep in sync.
- Object ids are a simple incrementing integer counter (not UUIDs) — single local process, no concurrency/distribution concerns, and integers are far more readable in logs/demos.
- `z_index` is set equal to the object's id at creation (both monotonically increasing) — sufficient for correct stacking order; explicit reordering ("send to back") isn't a feature yet.

**Backend (`backend/app/scene.py`, `backend/app/main.py`)**
- `SceneObject` (pydantic model): `id, type (circle|rectangle), x, y, w, h, rotation, fill, z_index, created_at`.
- `SceneGraph`: in-memory dict-backed store with `create`/`update`/`delete`/`list`, the single source of truth.
- `/ws` endpoint: accepts typed messages, applies them to the `SceneGraph`, and broadcasts `{"type": "scene_state", "objects": [...]}` to every connection in a `connections` set — including immediately on a new connection, so a fresh client always sees current state.

**A real modeling bug caught before it shipped:** Konva's `Circle` positions by *center*, while `Rect` positions by *top-left corner*. The scene graph's `x, y` needs one consistent meaning across shape types (top-left of the bounding box) since Phase 3's tool calls will reason about position uniformly regardless of shape — so `frontend/src/Canvas.tsx` converts top-left ↔ center at the render/drag boundary for circles specifically, keeping the conversion out of the data model.

**Frontend**
- `src/types.ts` — `SceneObject` type shared conceptually with the backend model.
- `src/useScene.ts` — hook owning the WebSocket connection, scene state, and `createObject`/`updateObject`/`deleteObject` senders.
- `src/Canvas.tsx` — Konva `Stage`/`Layer` rendering circles/rectangles from scene state, draggable, click-to-select (white outline).
- `src/App.tsx` — toolbar (Add Circle / Add Rectangle / Delete Selected) wired to the hook; this is the manual baseline proving the round trip before any voice/LLM involvement.

**Verification**
- Scripted a Python WS client simulating the exact frontend protocol: create → move → delete, each step confirmed via the broadcast response.
- Tested the specific checkpoint requirement directly: a second client connecting *after* an object already exists receives exactly that object (not empty, not duplicated) as its initial state; a third mutation from the first client live-broadcasts to the second. Confirms "pure reflection of backend state" holds across reconnects and multiple clients.
- User confirmed manually in the real Electron window: add circle/rectangle, drag to move, click to select, delete selected, and reload (Cmd+R) without losing or duplicating remaining objects — all work as intended.

**Not done in this pass**
- No voice or LLM involvement yet (Phase 2 and Phase 3).
- No undo, no multi-select, no resize handles — not required by this phase's checkpoint.

## Phase 2 — Voice Pipeline: Speech-to-Text
Status: not started
