import { useEffect, useRef, useState } from 'react'
import type { SceneObject } from './types'

export function useScene() {
  const [objects, setObjects] = useState<SceneObject[]>([])
  const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('connecting')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')
    wsRef.current = ws

    ws.onopen = () => setStatus('open')
    ws.onclose = () => setStatus('closed')
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'scene_state') {
        setObjects(message.objects)
      }
    }

    return () => ws.close()
  }, [])

  function createObject(payload: Omit<SceneObject, 'id' | 'z_index' | 'created_at' | 'rotation'>) {
    wsRef.current?.send(JSON.stringify({ type: 'create_object', payload }))
  }

  function updateObject(id: number, payload: Partial<SceneObject>) {
    wsRef.current?.send(JSON.stringify({ type: 'update_object', id, payload }))
  }

  function deleteObject(id: number) {
    wsRef.current?.send(JSON.stringify({ type: 'delete_object', id }))
  }

  return { objects, status, createObject, updateObject, deleteObject }
}
