# Working style for this repo

This project is being built as a learning exercise as much as a deliverable. Read this before writing any code.

## Two modes

**Plumbing-mode** — just build it. No explanation needed. Use this for:
- Boilerplate and scaffolding (repo structure, config files, dependency installs)
- Well-understood glue code (wiring a WebSocket handshake, a REST endpoint that just calls a function)
- Anything that's setup rather than a new concept

**Core-learning-mode** — explain first, let me attempt it, then review. Use this for:
- Anything introducing a new concept I haven't built before (scene graph design, the agent tool-use loop, reference resolution logic, LLM provider abstraction)
- Any non-trivial design decision, even inside a phase that's otherwise plumbing-mode

Default to core-learning-mode when unsure which one applies. Phase 4 (reference resolution) is core-learning-mode by default for its entire duration — it's the core differentiator of this project and deserves the full explain-attempt-review cycle, not shortcuts.

Per `ROADMAP.md`: Phase 0 and Phase 5 lean plumbing-mode (scaffolding and integration polish). Phases 2, 3, 3b, and 6 are mixed — plumbing for the wiring, core-learning-mode for the new concept each phase introduces.

## Workflow

1. **Read the linked resource(s) for the current phase before building it.** `ROADMAP.md` lists a "Learn first" section per phase — don't skip straight to "Build."
2. **Narrate design decisions before writing code**, especially anything that touches the modularity seams (scene graph shape, tool schema design, provider interface, resolver logic). A one- or two-sentence rationale is enough — the point is surfacing the decision, not writing an essay.
3. **Ask before non-trivial design decisions.** Don't silently pick between reasonable alternatives (e.g. how to structure the object registry, what the tool schema looks like) — flag the tradeoff and ask.
4. **Trace a concrete example after code is written.** Once a piece of functionality exists, walk through one real input (a sample utterance, a sample tool call) end-to-end so the behavior is verified, not just assumed.
5. **Pause at phase checkpoints.** Each phase in `ROADMAP.md` ends with a checkpoint — don't start the next phase until that checkpoint has actually been done, not just nominally possible.
6. **Update `PROGRESS.md` at milestones.** Whenever a phase (or meaningful sub-step) completes, provide the full updated `PROGRESS.md` content — not a diff — so it stays a clean, complete log.

## Session start

At the start of a new Claude Code session, read `CLAUDE.md`, `ROADMAP.md`, and `PROGRESS.md` to pick up where things left off before doing anything else.
