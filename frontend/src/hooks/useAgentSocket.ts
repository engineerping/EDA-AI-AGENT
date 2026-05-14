import { useCallback, useEffect, useRef, useState } from 'react'

export type PipelineStage = 'requirements' | 'design' | 'generation' | 'validation' | 'done'

export interface ChatMessage {
  role: 'user' | 'agent'
  content: string
  timestamp: number
}

export interface BOMItem {
  lib_id: string
  reference: string
  value: string
  quantity: number
  notes?: string
}

export interface ERCReport {
  error_count: number
  violations_translated: string[]
  note?: string
}

interface AgentSocketState {
  messages: ChatMessage[]
  stage: PipelineStage
  schematicContent: string | null
  bom: BOMItem[]
  ercReport: ERCReport | null
  sessionId: string | null
  connected: boolean
}

interface AgentSocketActions {
  sendMessage: (content: string) => void
  newSession: () => void
}

export function useAgentSocket(): AgentSocketState & AgentSocketActions {
  const wsRef = useRef<WebSocket | null>(null)
  const [state, setState] = useState<AgentSocketState>({
    messages: [],
    stage: 'requirements',
    schematicContent: null,
    bom: [],
    ercReport: null,
    sessionId: null,
    connected: false,
  })
  const pendingTokenRef = useRef('')

  const flushToken = useCallback(() => {
    if (!pendingTokenRef.current) return
    const token = pendingTokenRef.current
    pendingTokenRef.current = ''
    setState(s => {
      const msgs = [...s.messages]
      if (msgs.length > 0 && msgs[msgs.length - 1].role === 'agent') {
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: msgs[msgs.length - 1].content + token }
      } else {
        msgs.push({ role: 'agent', content: token, timestamp: Date.now() })
      }
      return { ...s, messages: msgs }
    })
  }, [])

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:5173/ws')
    wsRef.current = ws

    ws.onopen = () => setState(s => ({ ...s, connected: true }))
    ws.onclose = () => setState(s => ({ ...s, connected: false }))

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      switch (msg.type) {
        case 'session_id':
          setState(s => ({ ...s, sessionId: msg.session_id }))
          break
        case 'token':
          pendingTokenRef.current += msg.content
          requestAnimationFrame(flushToken)
          break
        case 'stage':
          flushToken()
          setState(s => ({ ...s, stage: msg.stage }))
          break
        case 'schematic':
          setState(s => ({ ...s, schematicContent: msg.content }))
          break
        case 'bom':
          setState(s => ({ ...s, bom: msg.items }))
          break
        case 'erc':
          setState(s => ({ ...s, ercReport: msg.report }))
          break
      }
    }

    return () => ws.close()
  }, [flushToken])

  const sendMessage = useCallback((content: string) => {
    setState(s => ({
      ...s,
      messages: [...s.messages, { role: 'user', content, timestamp: Date.now() }],
    }))
    wsRef.current?.send(JSON.stringify({ type: 'user_message', content }))
  }, [])

  const newSession = useCallback(() => {
    setState(s => ({
      ...s,
      messages: [],
      stage: 'requirements',
      schematicContent: null,
      bom: [],
      ercReport: null,
    }))
    wsRef.current?.send(JSON.stringify({ type: 'new_session' }))
  }, [])

  return { ...state, sendMessage, newSession }
}
