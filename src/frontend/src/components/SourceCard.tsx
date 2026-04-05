import type { SourceDoc } from '../types/api'

export default function SourceCard({ doc }: { doc: SourceDoc }) {
  return (
    <div className="card source-card">
      <div className="source-header">
        <strong>{doc.doc_name}</strong>
        <span className="source-meta">
          {doc.page_number != null && `p.${doc.page_number} / `}
          score: {doc.score.toFixed(4)}
        </span>
      </div>
      <p className="source-content">{doc.content}</p>
    </div>
  )
}
