import { useEffect, useState } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { SchematicViewer } from './components/SchematicViewer'
import { SettingsModal } from './components/SettingsModal'
import { useAgentSocket } from './hooks/useAgentSocket'
import { downloadSchematic, fetchConfig } from './api/client'

export default function App() {
  const [showSettings, setShowSettings] = useState(false)
  const [needsConfig, setNeedsConfig] = useState(false)
  const { messages, stage, schematicContent, bom, ercReport, sessionId, connected, sendMessage, newSession } = useAgentSocket()

  useEffect(() => {
    fetchConfig().then(cfg => {
      if (!cfg.api_key || cfg.api_key === '***') setNeedsConfig(true)
    })
  }, [])

  useEffect(() => {
    if (needsConfig) setShowSettings(true)
  }, [needsConfig])

  const handleDownloadBOM = () => {
    if (!bom.length) return
    const csv = ['lib_id,reference,value,quantity,notes', ...bom.map(b => `${b.lib_id},${b.reference},${b.value},${b.quantity},${b.notes ?? ''}`)].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'bom.csv'
    a.click()
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      {/* Header */}
      <div style={{ padding: '10px 16px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'white' }}>
        <div style={{ fontWeight: 700, fontSize: 16 }}>⚡ EDA-AI-Agent</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button onClick={newSession} style={{ fontSize: 12, padding: '4px 10px', borderRadius: 6, border: '1px solid #d1d5db', background: 'white', cursor: 'pointer' }}>
            New Session
          </button>
          <button onClick={() => setShowSettings(true)} style={{ fontSize: 20, background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280' }} title="Settings">
            ⚙
          </button>
        </div>
      </div>

      {/* Two-panel body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Chat — 40% */}
        <div style={{ width: '40%', borderRight: '1px solid #e5e7eb', overflow: 'hidden' }}>
          <ChatPanel messages={messages} stage={stage} connected={connected} onSend={sendMessage} />
        </div>

        {/* Schematic — 60% */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <SchematicViewer
            schematicContent={schematicContent}
            bom={bom}
            ercReport={ercReport}
            sessionId={sessionId}
            onDownloadSchematic={() => sessionId && downloadSchematic(sessionId)}
            onDownloadBOM={handleDownloadBOM}
          />
        </div>
      </div>

      {showSettings && <SettingsModal onClose={() => { setShowSettings(false); setNeedsConfig(false) }} />}
    </div>
  )
}
