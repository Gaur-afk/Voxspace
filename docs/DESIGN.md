# Design Notes

The key design decisions in VoxSpace, with the reasoning behind each and the alternatives considered.

---

## Scene graph as the single source of truth

The backend `SceneGraph` owns every object (`id, type, x, y, w, h, rotation, fill, z_index, created_at`). Every input path mutates the model and never touches the renderer directly: toolbar buttons, drag-to-move, and LLM tool calls all go through it. The canvas is a pure function of the scene state.

- **Why retained mode (Konva) rather than immediate-mode canvas drawing:** commands like "update the second circle" need objects that persist as addressable entities. Immediate-mode drawing leaves only pixels behind.
- **Renderer independence:** because the canvas only *reads* the model, a 3D renderer can be added as a second consumer without changing the agent or tool layers.
- **Ids are incrementing integers, not UUIDs.** There is a single local process, so there's no distribution concern, and integers keep logs and LLM context readable.

### One coordinate convention across shape types
Konva positions a `Circle` by its **center** but a `Rect` by its **top-left corner**. If the model stored whatever each shape natively uses, the LLM would have to reason about position differently per shape type. The scene graph uses a single convention instead: `x, y` is always the top-left of the bounding box. The center ↔ corner conversion happens only at the render/drag boundary in `Canvas.tsx`.

## Sync protocol: WebSocket with full-state broadcast

All manual create/update/delete actions travel as typed JSON messages over one WebSocket. After every mutation, and whenever a client connects, the backend broadcasts the **full** scene state to all clients.

- **Chosen over a REST + WebSocket hybrid** so there is one channel to reason about.
- **Full-state broadcast rather than diffs:** scenes are small, and this makes reconnects and late joiners correct by construction. A client that reloads gets exactly the current state, with nothing lost or duplicated. This was verified with multiple concurrent clients.

## Audio and agent calls use REST

`POST /transcribe` (audio → text) and `POST /agent` (utterance → tool calls) are one-shot request/response operations, which is a natural fit for REST. Keeping them off the WebSocket avoids base64-encoding audio and keeps the socket scoped to continuous state sync. Scene changes from the agent still reach clients through the normal WebSocket broadcast, because tools call the same `SceneGraph` methods as manual edits.

## Speech-to-text

- **Push-to-talk batch transcription, not streaming.** faster-whisper has no native low-latency streaming mode, and an explicit press/release already marks utterance boundaries, so voice activity detection isn't needed yet.
- **The `small` model is loaded once** as a module-level singleton, so the multi-second load isn't paid per request. It scored 10/10 on a test set built around the app's vocabulary (shapes, colors, ordinals, edit verbs), so a larger model wasn't justified.
- The browser's `MediaRecorder` produces webm/opus, which faster-whisper decodes directly with no conversion step.

## Tool schema design

Five tools: `create_shape`, `update_shape`, `move_shape`, `delete_shape`, `select_shape`. Adding an operation means registering a tool, not changing the agent loop.

- **`create_shape` makes position and size optional.** The server supplies a default placement, jittered so repeated creates don't overlap exactly, instead of forcing the model to invent pixel coordinates for "add a circle."
- **`move_shape`'s description states the canvas size and origin,** so the model can translate "top left" or "center" into absolute coordinates.
- **Selection is per-client UI state, not scene data.** `select_shape` returns `{selected_id}` to the caller and does not modify the scene graph or get broadcast. This matches how click-to-select already behaved.

## LLM provider abstraction

```python
class LLMProvider(Protocol):
    def generate(self, system: str, user_message: str, tools: list[dict]) -> ProviderResponse: ...

@dataclass
class ProviderResponse:
    text: str | None          # free-text reply (e.g. a clarifying question)
    tool_calls: list[ToolCall]
```

- **The real work is normalization, not HTTP.** Anthropic returns `content: [{type: "tool_use", ...}]` blocks, while Ollama returns `message.tool_calls: [{function: {...}}]`. Both are mapped into `ToolCall(name, arguments)`. Tool schemas are written once, in Anthropic's `input_schema` format, and translated to Ollama's `{type: "function", function: {..., parameters}}` format inside the Ollama provider.
- **`ProviderResponse` carries `text` as well as tool calls.** A tool-calls-only interface was the simpler option. `text` is included now because reference resolution will sometimes need the agent to reply with a clarifying question instead of acting, and adding it later would have been a breaking change.
- **Provider choice is runtime state** (env var default + `POST /provider` + a UI selector), so switching requires no code change or restart.

## Reference resolution (in progress)

Currently the LLM sees object ids in the scene context and picks the target itself. That's reliable for unambiguous references, but it leaves ordinal counting ("the second circle") to the model, which is exactly the kind of task models are inconsistent at, and inconsistent *differently* across providers.

The planned approach is a hybrid split:
1. **The LLM parses language into structure.** "the second red circle" becomes `{type: "circle", color: "red", ordinal: 2}`; "it" becomes a pronoun reference.
2. **A deterministic resolver runs that structure against the scene graph:** filter → order → index, plus a last-referenced-object pointer for pronouns.
3. **Each resolution has three outcomes:** exactly one match executes, zero matches returns an error, and two or more matches return a clarifying question (with the pending action held until the user answers).

This keeps resolution unit-testable and provider-independent, and lets the evaluation harness score resolution accuracy separately from tool-selection accuracy.
