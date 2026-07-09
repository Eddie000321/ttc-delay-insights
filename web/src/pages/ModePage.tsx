import { useMemo, useState } from 'react'
import MonthlyChart from '../components/MonthlyChart'
import MonthlyStackedByYear from '../components/MonthlyStackedByYear'
import TopStations from '../components/TopStations'
import CauseChart from '../components/CauseChart'
import PeakHourChart from '../components/PeakHourChart'

type Mode = 'all' | 'subway' | 'streetcar' | 'bus'

export default function ModePage({ mode }: { mode: Mode }) {
  const [fromDate, setFromDate] = useState<string>(() => {
    const d = new Date(); d.setDate(d.getDate() - 90); return d.toISOString().slice(0,10)
  })
  const [toDate, setToDate] = useState<string>(() => new Date().toISOString().slice(0,10))
  const [year, setYear] = useState<number>(new Date().getFullYear())

  const header = useMemo(() => {
    if (mode === 'all') return 'All Modes'
    return mode[0].toUpperCase() + mode.slice(1)
  }, [mode])

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>{header}</h1>
      <section>
        <h2 style={{ fontSize: 18 }}>Monthly Events (stacked by year)</h2>
        <MonthlyStackedByYear sourceFilter={mode === 'all' ? undefined : (mode as any)} />
      </section>

      {mode !== 'all' && (
        <>
          <section style={{ marginTop: 24 }}>
            <h2 style={{ fontSize: 18 }}>Top Stations</h2>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
              <label>
                From:
                <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} style={{ marginLeft: 8 }} />
              </label>
              <label>
                To:
                <input type="date" value={toDate} onChange={e => setToDate(e.target.value)} style={{ marginLeft: 8 }} />
              </label>
            </div>
            <TopStations source={mode as any} fromDate={fromDate} toDate={toDate} />
          </section>

          <section style={{ marginTop: 24 }}>
            <h2 style={{ fontSize: 18 }}>Top Causes</h2>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
              <label>
                Year:
                <input type="number" min={2014} max={2100} value={year} onChange={e => setYear(parseInt(e.target.value || String(new Date().getFullYear()), 10))} style={{ marginLeft: 8, width: 100 }} />
              </label>
            </div>
            <CauseChart source={mode as any} year={year} />
          </section>

          <section style={{ marginTop: 24, marginBottom: 32 }}>
            <h2 style={{ fontSize: 18 }}>Events by Hour</h2>
            <PeakHourChart source={mode as any} year={year} />
          </section>
        </>
      )}
    </div>
  )
}
