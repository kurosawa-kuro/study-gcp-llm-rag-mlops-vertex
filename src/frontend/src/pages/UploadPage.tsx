import { useState } from 'react'
import type { IngestResponse } from '../types/api'

export default function UploadPage() {
  const [gcsPath, setGcsPath] = useState('')
  const [result, setResult] = useState<IngestResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!gcsPath.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch('/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gcs_path: gcsPath }),
      })
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      setResult(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Upload</h2>
      <p style={{ color: '#666' }}>GCS パスを指定して Ingestion Job を実行します。</p>
      <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            value={gcsPath}
            onChange={(e) => setGcsPath(e.target.value)}
            placeholder="gs://mlops-dev-a-doc-qa/sample/"
            style={{ flex: 1, padding: 8, fontSize: 16, borderRadius: 4, border: '1px solid #ccc' }}
          />
          <button type="submit" disabled={loading} style={{ padding: '8px 20px', fontSize: 16 }}>
            {loading ? '...' : '実行'}
          </button>
        </div>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {result && (
        <div style={{ background: '#f0f7f0', borderRadius: 8, padding: 16 }}>
          <p><strong>Status:</strong> {result.status}</p>
          <p><strong>Job ID:</strong> {result.doc_id}</p>
        </div>
      )}
    </div>
  )
}
