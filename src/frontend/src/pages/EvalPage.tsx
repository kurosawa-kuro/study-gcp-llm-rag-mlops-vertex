import { useEffect, useState } from 'react'
import type { HealthResponse } from '../types/api'

export default function EvalPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)

  useEffect(() => {
    fetch('/health')
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => {})
  }, [])

  return (
    <div>
      <h2>Eval Dashboard</h2>

      {health && (
        <div style={{ background: '#f8f9fa', borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <p><strong>API Status:</strong> {health.status}</p>
          <p><strong>Version:</strong> {health.version}</p>
        </div>
      )}

      <div style={{ background: '#fff8e1', borderRadius: 8, padding: 16 }}>
        <h3 style={{ marginTop: 0 }}>最新評価結果（2026-04-04 / hybrid / kuromoji）</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: 8, borderBottom: '2px solid #ddd' }}>指標</th>
              <th style={{ textAlign: 'right', padding: 8, borderBottom: '2px solid #ddd' }}>スコア</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['Recall@1', '0.7500'],
              ['Recall@3', '0.9500'],
              ['Recall@5', '1.0000'],
              ['Recall@10', '1.0000'],
              ['MRR', '0.8625'],
              ['Exact Match', '0.9500'],
              ['ROUGE-L', '0.2117'],
            ].map(([name, value]) => (
              <tr key={name}>
                <td style={{ padding: 8, borderBottom: '1px solid #eee' }}>{name}</td>
                <td style={{ padding: 8, borderBottom: '1px solid #eee', textAlign: 'right', fontFamily: 'monospace' }}>
                  {value}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ color: '#888', fontSize: 13, marginTop: 12 }}>
          将来的に /eval API を追加し、リアルタイムで評価結果を取得・表示する予定
        </p>
      </div>
    </div>
  )
}
