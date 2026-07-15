import { useEffect, useState } from 'react'
import { Canvas } from './Canvas'
import { useScene } from './useScene'
import { useVoiceInput } from './useVoiceInput'
import { useAgent } from './useAgent'
import { useProviderSetting } from './useProviderSetting'

let colorIndex = 0
const COLORS = ['#e64980', '#4287f5', '#40c057', '#f59f00']

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: 'Claude (cloud)',
  ollama: 'Qwen2.5 (local)',
}

function App() {
  const { objects, status, createObject, updateObject, deleteObject } = useScene()
  const { isRecording, transcript, error, startRecording, stopRecording } = useVoiceInput()
  const { executed, isRunning, sendToAgent } = useAgent()
  const { provider, options, setProvider } = useProviderSetting()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  useEffect(() => {
    if (!transcript) return
    sendToAgent(transcript).then((results) => {
      const selectCall = results.find((r) => r.name === 'select_shape')
      if (selectCall && typeof selectCall.result.selected_id === 'number') {
        setSelectedId(selectCall.result.selected_id)
      }
    })
  }, [transcript, sendToAgent])

  function addShape(type: 'circle' | 'rectangle') {
    const fill = COLORS[colorIndex % COLORS.length]
    colorIndex += 1
    createObject({ type, x: 100, y: 100, w: 80, h: 80, fill })
  }

  function deleteSelected() {
    if (selectedId === null) return
    deleteObject(selectedId)
    setSelectedId(null)
  }

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '1.5rem' }}>
      <h1>VoxSpace</h1>
      <p>Backend WebSocket status: <strong>{status}</strong></p>

      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
        <button onClick={() => addShape('circle')}>Add Circle</button>
        <button onClick={() => addShape('rectangle')}>Add Rectangle</button>
        <button onClick={deleteSelected} disabled={selectedId === null}>
          Delete Selected
        </button>
      </div>

      <Canvas
        objects={objects}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onDragEnd={(id, x, y) => updateObject(id, { x, y })}
      />

      <div style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <label htmlFor="provider-select">Model:</label>
        <select
          id="provider-select"
          value={provider ?? ''}
          onChange={(e) => setProvider(e.target.value)}
          disabled={provider === null}
        >
          {options.map((option) => (
            <option key={option} value={option}>
              {PROVIDER_LABELS[option] ?? option}
            </option>
          ))}
        </select>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <button
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onMouseLeave={() => isRecording && stopRecording()}
          style={{ background: isRecording ? '#e03131' : undefined }}
        >
          {isRecording ? 'Recording... (release to stop)' : 'Hold to Talk'}
        </button>
        {error && <p style={{ color: '#e03131' }}>Error: {error}</p>}
        {transcript && <p>Transcript: <strong>{transcript}</strong></p>}
        {isRunning && <p>Thinking...</p>}
        {executed.length > 0 && (
          <p>
            Agent executed:{' '}
            {executed.map((call) => `${call.name}(${JSON.stringify(call.arguments)})`).join(', ')}
          </p>
        )}
      </div>
    </main>
  )
}

export default App
