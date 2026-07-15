import { useCallback, useEffect, useState } from 'react'

export function useProviderSetting() {
  const [provider, setProviderState] = useState<string | null>(null)
  const [options, setOptions] = useState<string[]>([])

  useEffect(() => {
    fetch('http://localhost:8000/provider')
      .then((res) => res.json())
      .then((data) => {
        setProviderState(data.provider)
        setOptions(data.options)
      })
  }, [])

  const setProvider = useCallback(async (next: string) => {
    const response = await fetch('http://localhost:8000/provider', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: next }),
    })
    const data = await response.json()
    setProviderState(data.provider)
  }, [])

  return { provider, options, setProvider }
}
