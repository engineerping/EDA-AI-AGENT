import { useEffect, useRef } from 'react'
import type { BOMItem, ERCReport } from '../hooks/useAgentSocket'

interface Props {
  schematicContent: string | null
  bom: BOMItem[]
  ercReport: ERCReport | null
  sessionId: string | null
  onDownloadSchematic: () => void
  onDownloadBOM: () => void
}

export function SchematicViewer({ schematicContent, bom, ercReport, onDownloadSchematic, onDownloadBOM }: Props) {
  const viewerRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!schematicContent || !viewerRef.current) return
    const blob = new Blob([schematicContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const el = viewerRef.current as any
    if (el.load) el.load(url)
    return () => URL.revokeObjectURL(url)
  }, [schematicContent])

  const ercColor = !ercReport ? '#9ca3af' : ercReport.error_count === 0 ? '#15803d' : '#dc2626'
  const ercLabel = !ercReport ? '—' : ercReport.error_count === 0 ? '✓ Clean' : `${ercReport.error_count} errors`

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div style={{ padding: '8px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '.05em' }}>
          Schematic Preview
        </span>
        <div style={{ display: 'flex', gap: 6 }}>
          <button onClick={onDownloadSchematic} disabled={!schematicContent} style={btnStyle}>
            ↓ .kicad_sch
          </button>
          <button onClick={onDownloadBOM} disabled={bom.length === 0} style={btnStyle}>
            ↓ BOM.csv
          </button>
        </div>
      </div>

      {/* KiCanvas viewer */}
      <div style={{ flex: 1, background: '#f9fafb', position: 'relative', overflow: 'hidden' }}>
        {schematicContent ? (
          <kicanvas-embed
            ref={viewerRef as any}
            style={{ width: '100%', height: '100%', display: 'block' }}
            controls="basic"
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', gap: 8, color: '#9ca3af' }}>
            <div style={{ fontSize: 40 }}>📐</div>
            <div style={{ fontSize: 13 }}>Schematic will appear here after generation</div>
            <div style={{ fontSize: 11 }}>Powered by KiCanvas</div>
          </div>
        )}
      </div>

      {/* Status bar */}
      <div style={{ padding: '5px 12px', borderTop: '1px solid #e5e7eb', background: '#f9fafb', display: 'flex', gap: 16, fontSize: 11, color: '#6b7280' }}>
        <span>ERC: <span style={{ color: ercColor, fontWeight: 600 }}>{ercLabel}</span></span>
        <span>Components: <span style={{ fontWeight: 600 }}>{bom.length || '—'}</span></span>
        {ercReport?.note && <span style={{ color: '#9ca3af' }}>{ercReport.note}</span>}
      </div>
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  fontSize: 11, padding: '4px 10px', borderRadius: 6,
  border: '1px solid #d1d5db', background: 'white',
  cursor: 'pointer', color: '#374151',
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'kicanvas-embed': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement> & { controls?: string }, HTMLElement>
    }
  }
}
