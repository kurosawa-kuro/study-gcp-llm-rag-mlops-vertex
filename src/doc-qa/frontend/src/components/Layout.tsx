import { NavLink, Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: '0 16px' }}>
      <header style={{ borderBottom: '1px solid #e0e0e0', padding: '12px 0', marginBottom: 24 }}>
        <h1 style={{ fontSize: 20, margin: 0, display: 'inline' }}>Doc QA</h1>
        <nav style={{ display: 'inline', marginLeft: 32 }}>
          {[
            { to: '/', label: 'QA' },
            { to: '/upload', label: 'Upload' },
            { to: '/eval', label: 'Eval' },
          ].map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({
                marginRight: 16,
                textDecoration: 'none',
                fontWeight: isActive ? 'bold' : 'normal',
                color: isActive ? '#1a73e8' : '#666',
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
