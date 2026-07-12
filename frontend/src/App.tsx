import { useEffect, useState } from 'react'

function App() {
  const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('connecting')
  const [reply, setReply] = useState<string | null>(null)

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')

    ws.onopen = () => {
      setStatus('open')
      ws.send('hello from VoxSpace frontend')
    }
    ws.onmessage = (event) => setReply(event.data)
    ws.onclose = () => setStatus('closed')

    return () => ws.close()
  }, [])

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
      <h1>VoxSpace</h1>
      <p>Backend WebSocket status: <strong>{status}</strong></p>
      <p>Reply from backend: <strong>{reply ?? '(waiting...)'}</strong></p>
    </main>
  )
}

export default App
