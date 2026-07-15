import { useCallback, useState } from 'react'

interface ExecutedTool {
  name: string
  arguments: Record<string, unknown>
  result: Record<string, unknown>
}

export function useAgent() {
  const [executed, setExecuted] = useState<ExecutedTool[]>([])
  const [isRunning, setIsRunning] = useState(false)

  const sendToAgent = useCallback(async (utterance: string) => {
    setIsRunning(true)
    try {
      const response = await fetch('http://localhost:8000/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ utterance }),
      })
      const data = await response.json()
      setExecuted(data.executed)
      return data.executed as ExecutedTool[]
    } finally {
      setIsRunning(false)
    }
  }, [])

  return { executed, isRunning, sendToAgent }
}
