import { useState } from 'react'
import { Canvas } from './Canvas'
import { useScene } from './useScene'

let colorIndex = 0
const COLORS = ['#e64980', '#4287f5', '#40c057', '#f59f00']

function App() {
  const { objects, status, createObject, updateObject, deleteObject } = useScene()
  const [selectedId, setSelectedId] = useState<number | null>(null)

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
    </main>
  )
}

export default App
