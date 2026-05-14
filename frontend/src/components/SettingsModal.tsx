import { useEffect, useState } from 'react'
import { fetchConfig, saveConfig, rescanLibraries, type AgentConfig } from '../api/client'

interface Props {
  onClose: () => void
}

export function SettingsModal({ onClose }: Props) {
  const [cfg, setCfg] = useState<AgentConfig>({ model: '', api_key: '', base_url: null, kicad_cli_path: null, db_last_scanned: null })
  const [saving, setSaving] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [scanResult, setScanResult] = useState<string | null>(null)

  useEffect(() => {
    fetchConfig().then(setCfg)
  }, [])

  const handleSave = async () => {
    setSaving(true)
    const patch = { ...cfg, api_key: cfg.api_key === '***' ? undefined : cfg.api_key }
    await saveConfig(patch)
    setSaving(false)
    onClose()
  }

  const handleRescan = async () => {
    setScanning(true)
    const result = await rescanLibraries()
    setScanResult(`Added ${result.added} symbols`)
    setScanning(false)
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: 'white', borderRadius: 12, padding: 24, width: 480, maxWidth: '95vw', boxShadow: '0 20px 60px rgba(0,0,0,.15)' }}>
        <h2 style={{ margin: '0 0 20px', fontSize: 18, fontWeight: 700 }}>Settings</h2>

        <section style={{ marginBottom: 20 }}>
          <h3 style={sectionHeader}>AI Provider</h3>
          <label style={labelStyle}>Model (LiteLLM format)</label>
          <input style={inputStyle} value={cfg.model} onChange={e => setCfg({ ...cfg, model: e.target.value })} placeholder="anthropic/claude-opus-4-7" />
          <p style={hintStyle}>e.g. openai/gpt-4o · anthropic/claude-opus-4-7 · ollama/llama3 · deepseek/deepseek-chat</p>

          <label style={labelStyle}>API Key</label>
          <input style={inputStyle} type="password" value={cfg.api_key ?? ''} onChange={e => setCfg({ ...cfg, api_key: e.target.value })} placeholder="sk-..." />
          <p style={hintStyle}>Stored in ~/.eda-agent/config.json — never sent to any server except your provider.</p>

          <label style={labelStyle}>Base URL <span style={{ color: '#9ca3af' }}>(optional — for Ollama / custom endpoints)</span></label>
          <input style={inputStyle} value={cfg.base_url ?? ''} onChange={e => setCfg({ ...cfg, base_url: e.target.value || null })} placeholder="http://localhost:11434" />
        </section>

        <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '0 0 20px' }} />

        <section style={{ marginBottom: 20 }}>
          <h3 style={sectionHeader}>KiCad Integration</h3>
          <label style={labelStyle}>KiCad CLI Path</label>
          <input style={inputStyle} value={cfg.kicad_cli_path ?? ''} onChange={e => setCfg({ ...cfg, kicad_cli_path: e.target.value || null })} placeholder="Auto-detect on save" />

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
            <span style={{ fontSize: 12, color: '#6b7280', flex: 1 }}>
              {cfg.db_last_scanned ? `Library last scanned: ${new Date(cfg.db_last_scanned).toLocaleDateString()}` : 'Library not yet scanned'}
              {scanResult && <span style={{ marginLeft: 8, color: '#15803d' }}>{scanResult}</span>}
            </span>
            <button onClick={handleRescan} disabled={scanning} style={{ ...btnStyle, opacity: scanning ? 0.6 : 1 }}>
              {scanning ? 'Scanning...' : 'Re-scan Libraries'}
            </button>
          </div>
        </section>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button onClick={onClose} style={btnStyle}>Cancel</button>
          <button onClick={handleSave} disabled={saving} style={{ ...btnStyle, background: '#7c3aed', color: 'white', border: 'none' }}>
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}

const sectionHeader: React.CSSProperties = { fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.06em', color: '#6b7280', margin: '0 0 10px' }
const labelStyle: React.CSSProperties = { display: 'block', fontSize: 12, color: '#374151', marginBottom: 4, marginTop: 10 }
const inputStyle: React.CSSProperties = { width: '100%', padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 8, fontSize: 13, boxSizing: 'border-box', outline: 'none' }
const hintStyle: React.CSSProperties = { fontSize: 11, color: '#9ca3af', margin: '3px 0 0' }
const btnStyle: React.CSSProperties = { padding: '8px 16px', borderRadius: 8, border: '1px solid #d1d5db', background: 'white', fontSize: 13, cursor: 'pointer' }
