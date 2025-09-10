export default function Home() {
  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>TTC Delay Insights</h1>
      <p style={{ color: '#555', marginTop: 0 }}>
        This project collects and analyzes TTC Subway, Streetcar, and Bus delay data to
        understand patterns and causes of service interruptions. Data is loaded into
        PostgreSQL and exposed via a lightweight API, then visualized with interactive charts.
      </p>
      <ul>
        <li>Explore monthly trends by mode</li>
        <li>See top impacted stations for a time range</li>
        <li>Review frequent causes per mode</li>
        <li>Identify peak disruption hours</li>
      </ul>
      <p style={{ color: '#555' }}>
        Use the tabs above to view All modes together or focus on Subway, Streetcar, or Bus.
      </p>
    </div>
  )
}

