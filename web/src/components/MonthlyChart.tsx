import { useEffect, useMemo, useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js'
import 'chartjs-adapter-date-fns'
import { getMonthlyByMode } from '../api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, TimeScale)

type Point = { month: string; source: string; n: number }

export default function MonthlyChart({ sourceFilter }: { sourceFilter?: 'subway'|'streetcar'|'bus' }) {
  const [data, setData] = useState<Point[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getMonthlyByMode()
      .then(setData)
      .catch(e => setError(String(e)))
  }, [])

  const grouped = useMemo(() => {
    const bySource: Record<string, Point[]> = {}
    data.filter(p => !sourceFilter || p.source === sourceFilter).forEach(p => {
      bySource[p.source] = bySource[p.source] || []
      bySource[p.source].push(p)
    })
    // Ensure chronological order
    Object.values(bySource).forEach(arr => arr.sort((a,b) => a.month.localeCompare(b.month)))
    const labels = Array.from(new Set(
      (sourceFilter ? data.filter(d => d.source === sourceFilter) : data).map(d => d.month)
    )).sort()
    const colors: Record<string, string> = {
      subway: '#4C78A8',
      streetcar: '#F58518',
      bus: '#54A24B',
    }
    const datasets = Object.entries(bySource).map(([source, points]) => ({
      label: source,
      data: labels.map(m => points.find(p => p.month === m)?.n ?? 0),
      borderColor: colors[source] || '#999',
      backgroundColor: colors[source] || '#999',
      tension: 0.2,
    }))
    return { labels, datasets }
  }, [data, sourceFilter])

  if (error) return <div style={{ color: 'crimson' }}>{error}</div>
  if (!data.length) return <div>Loading…</div>

  return (
    <Line
      data={{
        labels: grouped.labels.map(d => new Date(d)),
        datasets: grouped.datasets,
      }}
      options={{
        responsive: true,
        scales: {
          x: { type: 'time', time: { unit: 'month' } },
          y: { beginAtZero: true },
        },
        plugins: {
          legend: { position: 'bottom' as const },
        },
      }}
    />
  )
}
