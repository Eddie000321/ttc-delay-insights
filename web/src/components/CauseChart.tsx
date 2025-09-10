import { useEffect, useMemo, useState } from 'react'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { getCauses } from '../api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default function CauseChart(props: { source: 'subway'|'streetcar'|'bus'; year: number; limit?: number }) {
  const { source, year, limit = 20 } = props
  const [rows, setRows] = useState<Array<{ label: string; code?: string; n: number }>>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    getCauses({ source, year, limit })
      .then(setRows)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [source, year, limit])

  const labels = useMemo(() => rows.map(r => r.label || '(Unknown)'), [rows])
  const counts = useMemo(() => rows.map(r => r.n), [rows])

  if (error) return <div style={{ color: 'crimson' }}>{error}</div>
  if (loading) return <div>Loading…</div>
  if (!rows.length) return <div>No data.</div>

  return (
    <Bar
      data={{
        labels,
        datasets: [{
          label: `Causes (${source})`,
          data: counts,
          backgroundColor: '#F58518',
        }],
      }}
      options={{
        indexAxis: 'y' as const,
        responsive: true,
        scales: { x: { beginAtZero: true } },
        plugins: { legend: { display: false } },
      }}
    />
  )
}

