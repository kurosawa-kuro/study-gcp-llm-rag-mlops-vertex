import { useState } from 'react'
import type { QueryResponse } from '../types/api'
import SourceCard from '../components/SourceCard'

export default function QueryPage() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK }),
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
      <h2>QA</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="質問を入力..."
            style={{ flex: 1, padding: 8, fontSize: 16, borderRadius: 4, border: '1px solid #ccc' }}
          />
          <select value={topK} onChange={(e) => setTopK(Number(e.target.value))} style={{ padding: 8 }}>
            {[3, 5, 10].map((k) => (
              <option key={k} value={k}>Top {k}</option>
            ))}
          </select>
          <button type="submit" disabled={loading} style={{ padding: '8px 20px', fontSize: 16 }}>
            {loading ? '...' : '検索'}
          </button>
        </div>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {result && (
        <>
          <div style={{ background: '#f8f9fa', borderRadius: 8, padding: 16, marginBottom: 16 }}>
            <h3 style={{ marginTop: 0 }}>回答</h3>
            <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{result.answer}</p>
          </div>
          <h3>根拠ドキュメント ({result.sources.length})</h3>
          {result.sources.map((doc, i) => (
            <SourceCard key={i} doc={doc} />
          ))}
        </>
      )}
    </div>
  )
}
