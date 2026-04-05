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
      <p className="text-secondary mb-4">GCS パスを指定して Ingestion Job を実行します。</p>
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="form-row">
          <input
            type="text"
            value={gcsPath}
            onChange={(e) => setGcsPath(e.target.value)}
            placeholder="gs://mlops-dev-a-doc-qa/sample/"
            style={{ flex: 1 }}
          />
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? '...' : '実行'}
          </button>
        </div>
      </form>

      {error && <p className="text-error">{error}</p>}

      {result && (
        <div className="card">
          <p><strong>Status:</strong> <span className="badge badge-success">{result.status}</span></p>
          <p className="mb-2"><strong>Job ID:</strong> <span className="text-mono">{result.doc_id}</span></p>
        </div>
      )}
    </div>
  )
}
