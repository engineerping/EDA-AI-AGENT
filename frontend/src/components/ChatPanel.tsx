import { useEffect, useRef, useState } from 'react'
import type { ChatMessage, PipelineStage } from '../hooks/useAgentSocket'

const STAGES: PipelineStage[] = ['requirements', 'design', 'generation', 'validation']
const STAGE_LABELS: Record<string, string> = {
  requirements: 'Requirements',
  design: 'Design',
  generation: 'Generation',
  validation: 'Validation',
}

interface Props {
  messages: ChatMessage[]
  stage: PipelineStage
  connected: boolean
  onSend: (text: string) => void
}

export function ChatPanel({ messages, stage, connected, onSend }: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || !connected) return
    onSend(text)
    setInput('')
  }

  const stageIndex = STAGES.indexOf(stage as PipelineStage)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Stage progress bar */}
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 4, alignItems: 'center' }}>
        {STAGES.map((s, i) => (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{
              height: 4, width: 40, borderRadius: 2,
              background: i <= stageIndex ? '#7c3aed' : '#e5e7eb',
            }} />
            <span style={{ fontSize: 10, color: i <= stageIndex ? '#7c3aed' : '#9ca3af' }}>
              {STAGE_LABELS[s]}
            </span>
          </div>
        ))}
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#9ca3af', marginTop: 40, fontSize: 14 }}>
            Describe the circuit you want to build.
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '80%',
              padding: '8px 12px',
              borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              background: msg.role === 'user' ? '#7c3aed' : '#f3f4f6',
              color: msg.role === 'user' ? 'white' : '#111827',
              fontSize: 13,
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
            }}>
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: 10, borderTop: '1px solid #e5e7eb', display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder={connected ? 'Type your message...' : 'Connecting...'}
          disabled={!connected}
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db',
            fontSize: 13, outline: 'none',
          }}
        />
        <button
          onClick={handleSend}
          disabled={!connected || !input.trim()}
          style={{
            padding: '8px 16px', borderRadius: 8, border: 'none',
            background: '#7c3aed', color: 'white', fontSize: 13,
            cursor: 'pointer', opacity: (!connected || !input.trim()) ? 0.5 : 1,
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
