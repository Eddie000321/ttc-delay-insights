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
import { getTopStations } from '../api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default function TopStations(props: { source: 'subway'|'streetcar'|'bus'; fromDate: string; toDate: string; }) {
  const { source, fromDate, toDate } = props
  const [rows, setRows] = useState<Array<{ station: string; n: number }>>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    getTopStations({ source, fromDate, toDate, limit: 20 })
      .then(setRows)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [source, fromDate, toDate])

  const labels = useMemo(() => rows.map(r => r.station || '(Unknown)'), [rows])
  const counts = useMemo(() => rows.map(r => r.n), [rows])

  if (error) return <div style={{ color: 'crimson' }}>{error}</div>
  if (loading) return <div>Loading…</div>
  if (!rows.length) return <div>No data for selected range.</div>

  return (
    <Bar
      data={{
        labels,
        datasets: [{
          label: `Count (${source})`,
          data: counts,
          backgroundColor: '#4C78A8',
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

