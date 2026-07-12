# Voice-Controlled Spatial Design App — Work Plan

**Working title:** VoxSpace (placeholder — rename freely)

**Goal:** Build a local, voice-and-text-driven spatial design tool — Figma-style, starting in 2D — as a resume-ready portfolio piece with real product potential. The core technical differentiator is contextual reference resolution ("update the second circle," "make it bigger") on top of an agentic, tool-using LLM loop, with a local/cloud-swappable LLM provider and a renderer-agnostic scene model that can grow from 2D into 3D.

**Purpose:** Portfolio piece for AI/ML Engineer roles + potential product. This replaces the Agentic RAG System as the active main-focus project for July–early August; RAG resumes afterward (tracked in its own project space).

**Timeline:** July 11 – early August (~4–5 weeks), scoped for an intensive pace since this is the sole active build during this window. Phases are the real checkpoints, not the calendar dates — if a phase runs long, let it, and compress a later one rather than rushing reference resolution (Phase 4), which is the differentiator.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Desktop shell | Electron | Fastest path to a polished, demoable UI in a compressed timeline. Tauri (Rust) is a stronger long-term product choice (smaller binary, less resource overhead) but not worth the learning curve this sprint — flagged as a v2 migration candidate. |
| Frontend | React + TypeScript | Standard pairing with Electron; large ecosystem. |
| Canvas engine | Konva.js | Retained-mode scene graph library — objects persist as addressable entities, which is exactly what "update the second circle" requires. (Immediate-mode canvas drawing would give you pixels, not objects.) |
| Backend/orchestration | Python + FastAPI | Reuses your existing FastAPI experience from the Model Monitoring Dashboard. Hosts STT and the agent loop. |
| Speech-to-text | faster-whisper (local) | Local, no per-request cost, good accuracy/latency tradeoff at small model sizes. |
| LLM | Provider adapter: Anthropic API (default) + Ollama-served local model (swap-in) | Satisfies the "local LLM with ability to connect to proprietary" requirement directly. Reuses your Anthropic API setup from the RAG project. |
| Frontend ↔ backend | WebSocket (localhost) | Streaming transcript + tool-call events; keeps everything on-device. |

---

## Modularity principles (cross-cutting, referenced throughout the phases)

These are the seams that make "as modular as possible" concrete rather than aspirational:

1. **Renderer-agnostic scene graph** — a single source-of-truth object model (id, type, position, size, color, z-index, created_at). Commands mutate the model, never the renderer directly. The 2D renderer and the eventual 3D renderer both just *read* this model.
2. **LLM provider abstraction** — one `LLMProvider` interface (`generate(messages, tools) -> response`), implemented separately for the Anthropic/OpenAI cloud path and the Ollama local path. Swapping providers is a config change, not a code change.
3. **Input modality abstraction** — voice transcript and typed prompt both normalize to the same "utterance" string feeding the same agent loop. Voice is just one way of producing that string; there's no separate voice-only code path.
4. **Tool registry pattern** — shape operations are discrete tools with JSON schemas (`create_shape`, `update_shape`, `delete_shape`, `move_shape`, `select_shape`). Adding a new shape type or operation means registering a new tool, not touching the agent loop.
5. **Reference resolver as a separate module** — decoupled from the LLM call itself (hybrid symbolic + LLM resolution), so resolution logic is independently testable and works the same regardless of which LLM provider is active.

---

## Phase 0 — Environment, Concept Grounding & Scaffolding (Week 1, first half)

**Learn first:**
- LLM tool/function-calling mechanics — this is a direct extension of what you already learned for the RAG agent loop, so this is mostly a bridge, not new ground
- Retained-mode vs. immediate-mode canvas rendering, and why retained-mode (scene graph) fits this project
- STT basics: streaming vs. batch transcription, voice activity detection (VAD)
- How an Electron app's main/renderer process split interacts with an external local backend process

**Resources:**
- Konva.js docs, "Core Concepts"
- faster-whisper README
- Ollama function-calling / tool-use docs
- Your own notes from the Anthropic tool-use docs + ReAct paper (RAG Phase 0) — this is the same underlying pattern

**Build:**
- Repo scaffold: Electron + React + TS frontend skeleton, Python + FastAPI backend skeleton
- Conda/venv environment for the backend
- Ollama installed locally with one function-calling-capable model pulled (e.g. Llama 3.1 8B Instruct or Qwen2.5 7B)
- faster-whisper installed and smoke-tested on a sample audio clip
- Basic WebSocket round trip proven end-to-end between frontend and backend ("hello world" message both directions)
- `CLAUDE.md` (teaching-mode instructions, same plumbing-mode vs. core-learning-mode distinction as the other projects), `ROADMAP.md` (this plan), `PROGRESS.md` added to repo root

**Checkpoint:** Explain the difference between retained-mode and immediate-mode rendering and why retained-mode is the right fit here. Explain what a tool schema needs to contain for an LLM to call it correctly.

---

## Phase 1 — Static Scene Graph + Manual 2D Canvas (Week 1, second half)

**Learn first:**
- Scene graph data modeling: object identity, z-order, transform properties
- Konva's shape/layer model

**Build:**
- Scene graph data model in the Python backend as the single source of truth: `id, type, x, y, w, h, rotation, fill, z_index, created_at`
- REST/WebSocket endpoints to create/update/delete/list objects
- Konva-based React canvas that renders the scene graph and stays in sync via WebSocket push
- A minimal manual UI (buttons: add circle / add rectangle) to validate the full round trip *before* any voice or LLM involvement — this is your naive baseline, same role as Phase 2's naive RAG in the other project

**Checkpoint:** Create, move, and delete objects manually end-to-end. Confirm the canvas is a pure reflection of backend state — refreshing the frontend shouldn't lose or duplicate anything.

---

## Phase 2 — Voice Pipeline: Speech-to-Text (Week 2, first half)

**Learn first:**
- Push-to-talk batch capture vs. streaming STT
- Basic VAD
- Latency/accuracy tradeoffs across Whisper model sizes

**Resources:**
- faster-whisper streaming examples
- WebRTC VAD docs (if you use it for auto-stop on silence)

**Build:**
- Push-to-talk capture in the Electron renderer → audio blob → Python backend → faster-whisper transcription → transcript returned and displayed live

**Checkpoint:** Transcribe 10 varied test utterances (including the shape/color/number vocabulary this app actually needs) and record accuracy. Note failure modes — you'll need them for Phase 4.

---

## Phase 3 — LLM Tool-Use Agent Loop (Week 2, second half)

**Learn first:**
- Mapping natural language to structured tool calls with current scene state as context — direct extension of the ReAct pattern from the RAG project
- Designing tool schemas for spatial operations

**Build:**
- Tool registry + JSON schemas for the 5 core ops: `create_shape`, `update_shape`, `delete_shape`, `move_shape`, `select_shape`
- Hand-rolled agent loop: transcript (or typed prompt) + current scene JSON → LLM (Anthropic API first) → tool call(s) → executed against the scene graph → canvas updates live

**Checkpoint:** Issue 5 unambiguous voice commands ("add a blue circle," "make the rectangle red") and confirm correct tool calls and scene updates end-to-end.

---

## Phase 3b — LLM Provider Abstraction: Local Swap-In (Week 3, first half)

**Learn first:**
- The local function-calling model landscape — which Ollama-servable models support tool calls reliably
- Latency/quality tradeoffs of local vs. cloud for this specific task

**Build:**
- `LLMProvider` interface
- Ollama-backed implementation
- Config-driven switch between local and cloud
- Side-by-side benchmark on the same 5+ test commands (accuracy, latency) across both providers

**Checkpoint:** Explain, with your own benchmark numbers, the concrete tradeoff between the local and cloud provider for this task, and when you'd choose each. This is a strong interview answer if you have real numbers behind it.

---

## Phase 4 — Reference Resolution & Multi-Turn Context (Week 3, second half – Week 4 start)

**This is the core differentiator of the project — give it the room it needs.**

**Learn first:**
- Deictic and anaphoric reference in dialogue systems: what "it," "the second one," "that circle" actually require to resolve
- Symbolic vs. LLM-based resolution strategies, and why a hybrid usually beats either alone
- Disambiguation and clarification-question design

**Resources:**
- A short primer on coreference resolution (search "reference resolution task-oriented dialogue")
- Task-oriented dialogue "slot filling" concepts

**Build:**
- Object registry queries for ordinal reference — "second circle" resolves deterministically to the 2nd circle by creation order, exposed as a resolver function, not left for the LLM to guess
- A "last-referenced object" pointer for pronoun resolution ("make it bigger")
- A disambiguation path: if a reference has 2+ candidates, the agent asks a clarifying question instead of guessing
- Resolved target IDs passed into tool calls — the LLM works with resolved references, not raw natural-language descriptions

**Checkpoint:** Walk through your resolver logic for three cases — an unambiguous ordinal reference, a pronoun reference, and an ambiguous case that should trigger a clarifying question — and explain why each resolves the way it does.

---

## Phase 5 — Unified Input & UX Polish (Week 4, second half)

**Learn first:** Nothing new — this phase is integration and polish.

**Build:**
- Typed-prompt input as a first-class alternate path into the same agent loop, no special-casing
- Command history panel with undo (command-pattern style: every tool call is invertible)
- Voice/typed toggle in the UI
- Ambiguity and error surfacing in the UI itself, not just the console

**Checkpoint:** Complete a 10-command mixed voice-and-text session, including at least one correction and undo, without touching code.

---

## Phase 6 — Evaluation Harness + Demo Packaging (Week 5 / early August)

**Learn first:**
- Task-success evaluation for command-driven systems: tool-selection accuracy, parameter accuracy, reference-resolution accuracy — the analogue of RAGAS for this project

**Build:**
- A labeled test set of 20–30 utterances with expected tool call + expected resolved target
- A small eval script scoring tool accuracy / parameter accuracy / resolution accuracy, run against both LLM providers from Phase 3b
- A polished demo recording (screen + voice) — this is a highly visual project, and a good demo video will do more for your portfolio than the code alone

**Checkpoint:** Report baseline eval numbers for the local vs. cloud provider and be able to explain the single biggest remaining failure category.

---

## Beyond August (explicit stretch — not in scope for this sprint)

- 3D renderer (Three.js) as a second implementation behind the same scene-graph interface — this is where the modularity claim gets proven, not just asserted
- Multi-object / batch commands ("align these three circles")
- Wake-word / hands-free activation
- Full undo/redo history, multi-user collaboration (product angle)
- Packaging as an installable app — this is where a Tauri migration would be revisited

---

## Working style

Same pattern as your other projects: teaching mode via `CLAUDE.md` (concepts explained before building, checkpoints before advancing phases), phased `ROADMAP.md`, running `PROGRESS.md`. Plumbing-mode vs. core-learning-mode distinction applies here too — Phase 4 (reference resolution) is core-learning-mode by default given it's the differentiator; scaffolding-heavy phases like 0 and 5 lean more plumbing-mode.
