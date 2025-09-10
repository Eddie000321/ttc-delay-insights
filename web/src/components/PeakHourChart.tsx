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
import { getPeakHour } from '../api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default function PeakHourChart(props: { source: 'subway'|'streetcar'|'bus'; year: number }) {
  const { source, year } = props
  const [rows, setRows] = useState<Array<{ hour: number; n: number }>>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    getPeakHour({ source, year })
      .then(setRows)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [source, year])

  const labels = useMemo(() => rows.map(r => String(r.hour)), [rows])
  const counts = useMemo(() => rows.map(r => r.n), [rows])

  if (error) return <div style={{ color: 'crimson' }}>{error}</div>
  if (loading) return <div>Loading…</div>
  if (!rows.length) return <div>No data.</div>

  return (
    <Bar
      data={{
        labels,
        datasets: [{
          label: `Events by Hour (${source})`,
          data: counts,
          backgroundColor: '#54A24B',
        }],
      }}
      options={{
        responsive: true,
        scales: { x: { title: { display: true, text: 'Hour' } }, y: { beginAtZero: true } },
        plugins: { legend: { display: false } },
      }}
    />
  )
}

