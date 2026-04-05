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
        <div className="card mb-6">
          <p>
            <strong>API Status:</strong>{' '}
            <span className="badge badge-success">{health.status}</span>
          </p>
          <p className="mb-2">
            <strong>Version:</strong>{' '}
            <span className="text-mono">{health.version}</span>
          </p>
        </div>
      )}

      <div className="card">
        <h3>最新評価結果（2026-04-04 / hybrid / kuromoji）</h3>
        <table className="admin-table">
          <thead>
            <tr>
              <th>指標</th>
              <th className="text-right">スコア</th>
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
                <td>{name}</td>
                <td className="text-right text-mono">{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-secondary text-sm mt-4" style={{ marginBottom: 0 }}>
          将来的に /eval API を追加し、リアルタイムで評価結果を取得・表示する予定
        </p>
      </div>
    </div>
  )
}
