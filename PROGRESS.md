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
Status: complete (2026-07-14)

**Scope decision:** push-to-talk (batch), not streaming — faster-whisper has no native low-latency streaming mode, and this matches what `ROADMAP.md` scopes for this phase. VAD (auto-stop-on-silence) skipped deliberately: the push-to-talk button already gives explicit start/stop, so there's no problem yet for VAD to solve.

**Audio transport decision:** REST (`POST /transcribe`), not over the existing WebSocket. Audio-in/transcript-out is a one-shot request/response — the natural fit for REST — and it keeps the WS scoped to exactly what Phase 1 established it for (continuous scene-state sync). Avoids base64 overhead and mixing a large one-shot binary payload into a channel meant for small frequent messages.

**Backend**
- `backend/app/stt.py`: faster-whisper `small` model loaded once as a module-level singleton (model load takes a few seconds — paying that per-request would double it every time), with a `transcribe(audio_bytes) -> str` helper.
- `backend/app/main.py`: `POST /transcribe` accepts a multipart file upload, returns `{"text": ...}`. Added `CORSMiddleware` (required — the Electron renderer's dev-server origin differs from the backend's).
- Verified directly (before touching the frontend) that both WAV and webm/opus — the actual format the browser's `MediaRecorder` produces — decode and transcribe correctly with no manual format conversion needed, using the Phase 0 sample clip converted with `ffmpeg`.

**Frontend**
- `src/useVoiceInput.ts`: hook wrapping `getUserMedia` + `MediaRecorder`, assembling recorded chunks into a `Blob` on stop and POSTing to `/transcribe`.
- `App.tsx`: "Hold to Talk" button (mousedown/mouseup, with mouseleave-while-recording also stopping) showing recording state and the returned transcript.
- Deliberately not wired to anything else yet — the transcript only displays. Connecting it to a tool call and scene mutation is Phase 3's job specifically; keeping Phase 2 scoped to "speech reliably becomes accurate text" independent of whether anything acts on it yet.

**Checkpoint — 10-utterance accuracy test**
- User ran all 10 test utterances (covering shapes, colors, ordinals, and the verbs this app will need: "Add a red circle," "Make the second circle bigger," "Delete the first rectangle," "Move it to the top left," "Undo that," etc.) through the real push-to-talk UI.
- Result: 10/10 transcribed correctly, no failure modes surfaced. `small` model size is sufficient for this app's vocabulary — no need to move to `medium` for accuracy.

**Not done in this pass**
- No LLM or tool-call wiring yet (Phase 3, next) — transcript is display-only.
- No VAD/auto-stop — push-to-talk's explicit button press covers this phase's need.

## Phase 3 — LLM Tool-Use Agent Loop
Status: complete (2026-07-14)

**Model:** `claude-opus-4-8` via the `anthropic` Python SDK. Adaptive thinking deliberately left off (omitted, not disabled) — this is a single-turn structured tool-call mapping with full scene context already provided, not the kind of multi-step reasoning task thinking is for, and latency matters for a voice-interactive app where the user is waiting after they release the mic button.

**Reference resolution scope decision (ties back to the Phase 1 checkpoint discussion):** with no dedicated resolver yet (that's Phase 4), the LLM is given the current scene state — including object ids — directly in its context and picks the target id itself for `update_shape`/`move_shape`/`delete_shape`/`select_shape`. This works reliably for unambiguous references ("the rectangle" when only one exists) but has no principled way to handle "the second circle" when several exist — which is exactly why this phase's checkpoint is scoped to unambiguous commands only, and exactly the gap Phase 4's dedicated resolver will close.

**Credentials:** `backend/.env` (gitignored) holds `ANTHROPIC_API_KEY`, loaded via `python-dotenv`, following the same convention already used in the sibling RAG-agentic project.

**Tool registry (`backend/app/tools.py`)** — 5 schemas matching `ROADMAP.md`: `create_shape`, `update_shape`, `move_shape`, `delete_shape`, `select_shape`. Notable design choices:
- `create_shape`'s position/size are optional, not required — omitting them lets the server apply a default (jittered within canvas bounds, so accidental multi-creates don't perfectly overlap) rather than forcing the LLM to invent precise pixel coordinates for "add a circle."
- `move_shape`'s description includes the canvas dimensions so the LLM can translate relative phrases ("top left," "center") into absolute coordinates itself.
- `select_shape` only returns `{selected_id}` in the tool result — it does **not** touch the backend `SceneGraph`. Selection is treated as ephemeral per-client UI state (matching how manual click-to-select already worked in Phase 1), not canonical scene data, so it doesn't need to be part of the broadcast scene state.

**Agent loop (`backend/app/agent.py`)** — `run_agent_turn(utterance, scene)`: builds a system prompt with canvas dimensions, serializes current scene state as JSON context, calls the Messages API with the 5 tools, and executes every returned `tool_use` block against the live `SceneGraph`. Returns the list of executed calls (name, arguments, result) for transparency/debugging — this is what satisfies the checkpoint's "confirm correct tool calls," not just visual inspection of the canvas.

**Endpoint (`POST /agent` in `main.py`):** REST, consistent with Phase 2's precedent (one-shot request/response) rather than the WS channel — the actual scene mutation still reaches the frontend through the existing WS broadcast mechanism regardless, since `execute_tool` calls the same `SceneGraph` methods the manual buttons use.

**Frontend:** new `useAgent.ts` hook (`sendToAgent`, memoized with `useCallback` so it can safely sit in a `useEffect` dependency array). `App.tsx` chains Phase 2's transcript directly into the agent call the moment it arrives — no manual "send" step, matching the "say it and watch it happen" core capability. `select_shape` results update local `selectedId` state (reusing the Phase 1 selection/highlight UI) without any backend involvement. An "Agent executed: ..." line surfaces exactly which tool(s) ran with which arguments, for transparency during testing.

**Verification**
- Scripted all 5 tools directly against the live API via `curl` before touching the frontend: create (blue circle), create + update (rectangle → red), move ("top left" → x=0,y=0), select (unambiguous "the circle" → correct id), delete (unambiguous "the rectangle" → correct id). All correct on the first pass.
- User ran the actual Phase 3 checkpoint — 5 unambiguous voice commands through the real push-to-talk UI: "Add a blue circle," "Add a red rectangle," "Make the rectangle bigger," "Move the circle to the center," "Delete the rectangle." All five produced the correct tool call and the correct visible canvas update, confirmed with screenshots at each step.

**Not done in this pass**
- No reference resolution for ambiguous cases ("the second circle," "it") — Phase 4.
- No Ollama/local-provider swap-in yet — Phase 3b. The LLM call is currently hardcoded to the Anthropic API.
- No typed-text input path yet (voice only) — Phase 5 formalizes typed input as a first-class alternate entry point into the same agent loop.

## Phase 3b — LLM Provider Abstraction: Local Swap-In
Status: complete (2026-07-15)

**Interface design decision:** `LLMProvider.generate(system, user_message, tools) -> ProviderResponse`, where `ProviderResponse` carries both `text: str | None` and `tool_calls: list[ToolCall]` — not just tool calls. Chosen over a tool-calls-only shape specifically to anticipate Phase 4: disambiguation will need the model to sometimes respond with a clarifying question instead of a tool call, and building that into the interface now avoids a breaking change later. `ToolCall(name, arguments)` is the normalized shape both providers map their structurally different native responses into (Anthropic's `content: [{type: "tool_use", ...}]` content blocks vs. Ollama's `message.tool_calls: [{function: {...}}]`) — this normalization is the actual substance of the "provider abstraction," not the HTTP plumbing.

**Implementation (`backend/app/`)**
- `llm_provider.py` — the `LLMProvider` Protocol, `ToolCall`, `ProviderResponse`.
- `providers.py` — `AnthropicProvider` (wraps the existing `client.messages.create` call, extracts `text`/`tool_use` blocks into the normalized shape) and `OllamaProvider` (translates the canonical `TOOLS` schema — Anthropic's `{name, description, input_schema}` shape — into Ollama's wire format `{type: "function", function: {name, description, parameters}}`, POSTs to `/api/chat` with `qwen2.5:7b`, normalizes the response back).
- `agent.py` — `get_provider()` reads `LLM_PROVIDER` env var (`anthropic` default, `ollama` to swap) and returns the matching instance; `run_agent_turn` now goes through the abstraction instead of calling the Anthropic SDK directly, and returns `(executed, message)` — the `message` field (surfaced but not yet used by the UI) is where Phase 4's clarifying questions will eventually flow.

**Benchmark (`backend/tests/benchmark_providers.py`)** — 6 test cases covering all 5 tools, each with a fresh seeded `SceneGraph` (independent, repeatable) and a correctness check (right tool name + right target id + sane argument values), run against both providers:

| Provider | Accuracy | Avg latency |
|---|---|---|
| Anthropic (`claude-opus-4-8`) | 100% (6/6) | 2.02s |
| Ollama (`qwen2.5:7b`, local) | 83% (5/6) | 0.87s |

Ollama's one failure was a specific, addressable failure mode, not blended noise: for "move the circle to the top left" it returned `y=600` — the *bottom* of the 600px canvas (origin top-left, y grows downward) — inverting the y-axis for "top." Worth remembering for Phase 6's eval work as a named failure category, not just "local is worse."

**Checkpoint — tradeoff discussion.** Latency gap comes from two compounding factors: no network round-trip to Anthropic's servers, and `qwen2.5:7b` being a far smaller model than Opus (smaller forward pass per token) — not "readiness," both providers receive an identical prompt structure. Accuracy gap traces to raw model capability, concretely demonstrated by the coordinate-convention failure. Landed on three legitimate reasons to prefer local beyond "cloud unavailable" (matching this project's own local-first pitch in `README.md`): privacy/data sovereignty (design content and transcripts never leaving the machine), cost at scale (fixed local compute vs. per-request cloud billing), and latency-critical interactive UX — the 0.87s vs 2.02s gap is perceptible in a voice tool, and an 83%-correct-but-fast response is a reasonable tradeoff once Phase 5 makes wrong answers cheap to undo.

**Not done in this pass**
- No UI toggle between providers yet — switching is currently a backend env var, not a user-facing control. Not required by this phase's checkpoint (config-driven swap, not a polished UI), and a UI toggle would be natural Phase 5 integration-polish scope.
- The `message` field (clarifying-question text) is plumbed through the interface and the `/agent` response but not yet rendered distinctly in the frontend — no real use for it until Phase 4 actually produces disambiguation questions.

## Phase 4 — Reference Resolution & Multi-Turn Context
Status: not started
