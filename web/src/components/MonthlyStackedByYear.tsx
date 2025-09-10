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
import { getMonthlyByMode } from '../api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

type Point = { month: string; source: string; n: number }

const MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

export default function MonthlyStackedByYear({ sourceFilter }: { sourceFilter?: 'subway'|'streetcar'|'bus' }) {
  const [rows, setRows] = useState<Point[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getMonthlyByMode()
      .then(setRows)
      .catch(e => setError(String(e)))
  }, [])

  const { labels, datasets } = useMemo(() => {
    // Aggregate counts into year-month buckets, optionally filtering by source
    const bucket = new Map<string, number>() // key: `${year}-${m}`
    const yearsSet = new Set<number>()
    for (const r of rows) {
      if (sourceFilter && r.source !== sourceFilter) continue
      const d = new Date(r.month)
      if (Number.isNaN(d.getTime())) continue
      const y = d.getFullYear()
      const m = d.getMonth() // 0..11
      yearsSet.add(y)
      const key = `${y}-${m}`
      bucket.set(key, (bucket.get(key) || 0) + r.n)
    }
    const years = Array.from(yearsSet).sort((a,b) => a - b)
    const labels = MONTH_LABELS
    // color palette per year
    const makeColor = (idx: number, total: number) => {
      const hue = Math.round((idx / Math.max(1, total)) * 300) // 0..300
      return `hsl(${hue} 60% 50%)`
    }
    const datasets = years.map((y, idx) => ({
      label: String(y),
      data: labels.map((_, mIdx) => bucket.get(`${y}-${mIdx}`) || 0),
      backgroundColor: makeColor(idx, years.length),
      stack: 'years',
    }))
    return { labels, datasets }
  }, [rows, sourceFilter])

  if (error) return <div style={{ color: 'crimson' }}>{error}</div>
  if (!rows.length) return <div>Loading…</div>

  return (
    <Bar
      data={{ labels, datasets }}
      options={{
        responsive: true,
        plugins: { legend: { position: 'bottom' as const } },
        scales: {
          x: { stacked: true },
          y: { stacked: true, beginAtZero: true },
        },
      }}
    />
  )
}

