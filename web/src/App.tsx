import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import ModePage from './pages/ModePage'

const tabLinkStyle: React.CSSProperties = {
  padding: '8px 12px',
  borderRadius: 8,
  textDecoration: 'none',
  color: '#333',
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: 16, fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif' }}>
        <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
          <div style={{ fontWeight: 700 }}>TTC Delay Insights</div>
          <nav aria-label="Delay mode" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <NavLink to="/" style={({isActive}) => ({ ...tabLinkStyle, background: isActive ? '#eef3fb' : 'transparent' })}>Home</NavLink>
            <NavLink to="/all" style={({isActive}) => ({ ...tabLinkStyle, background: isActive ? '#eef3fb' : 'transparent' })}>All</NavLink>
            <NavLink to="/subway" style={({isActive}) => ({ ...tabLinkStyle, background: isActive ? '#eef3fb' : 'transparent' })}>Subway</NavLink>
            <NavLink to="/streetcar" style={({isActive}) => ({ ...tabLinkStyle, background: isActive ? '#eef3fb' : 'transparent' })}>Streetcar</NavLink>
            <NavLink to="/bus" style={({isActive}) => ({ ...tabLinkStyle, background: isActive ? '#eef3fb' : 'transparent' })}>Bus</NavLink>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/all" element={<ModePage mode="all" />} />
            <Route path="/subway" element={<ModePage mode="subway" />} />
            <Route path="/streetcar" element={<ModePage mode="streetcar" />} />
            <Route path="/bus" element={<ModePage mode="bus" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
