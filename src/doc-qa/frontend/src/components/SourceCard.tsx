import type { SourceDoc } from '../types/api'

export default function SourceCard({ doc }: { doc: SourceDoc }) {
  return (
    <div
      style={{
        border: '1px solid #e0e0e0',
        borderRadius: 8,
        padding: 12,
        marginBottom: 8,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <strong>{doc.doc_name}</strong>
        <span style={{ color: '#888', fontSize: 13 }}>
          {doc.page_number != null && `p.${doc.page_number} / `}
          score: {doc.score.toFixed(4)}
        </span>
      </div>
      <p style={{ margin: 0, fontSize: 14, color: '#444', whiteSpace: 'pre-wrap' }}>
        {doc.content}
      </p>
    </div>
  )
}
