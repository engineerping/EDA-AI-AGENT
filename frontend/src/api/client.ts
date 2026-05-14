export interface AgentConfig {
  model: string
  api_key: string
  base_url: string | null
  kicad_cli_path: string | null
  db_last_scanned: string | null
}

export async function fetchConfig(): Promise<AgentConfig> {
  const res = await fetch('/api/config')
  return res.json()
}

export async function saveConfig(patch: Partial<AgentConfig>): Promise<void> {
  await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
}

export async function rescanLibraries(): Promise<{ added: number }> {
  const res = await fetch('/api/rescan', { method: 'POST' })
  return res.json()
}

export function downloadSchematic(sessionId: string): void {
  window.location.href = `/api/download/${sessionId}`
}
