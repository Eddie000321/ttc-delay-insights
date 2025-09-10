const BASE = import.meta.env.VITE_API_URL || ''

export async function getMonthlyByMode() {
  const res = await fetch(`${BASE}/api/monthly-by-mode`)
  if (!res.ok) throw new Error('Failed to fetch monthly-by-mode')
  return res.json() as Promise<Array<{ month: string; source: string; n: number }>>
}

export async function getTopStations(params: { source: string; fromDate: string; toDate: string; limit?: number }) {
  const q = new URLSearchParams({
    source: params.source,
    from_date: params.fromDate,
    to_date: params.toDate,
    ...(params.limit ? { limit: String(params.limit) } : {}),
  })
  const res = await fetch(`${BASE}/api/top-stations?${q.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch top-stations')
  return res.json() as Promise<Array<{ station: string; n: number }>>
}

export async function getCauses(params: { source: string; year: number; limit?: number }) {
  const q = new URLSearchParams({
    source: params.source,
    year: String(params.year),
    ...(params.limit ? { limit: String(params.limit) } : {}),
  })
  const res = await fetch(`${BASE}/api/causes?${q.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch causes')
  return res.json() as Promise<Array<{ label: string; code?: string; n: number }>>
}

export async function getPeakHour(params: { source: string; year: number }) {
  const q = new URLSearchParams({
    source: params.source,
    year: String(params.year),
  })
  const res = await fetch(`${BASE}/api/peak-hour?${q.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch peak-hour')
  return res.json() as Promise<Array<{ hour: number; n: number }>>
}
