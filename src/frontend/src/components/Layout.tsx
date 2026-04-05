import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { Search, Upload, BarChart3 } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Query', icon: Search },
  { to: '/upload', label: 'Upload', icon: Upload },
  { to: '/eval', label: 'Evaluation', icon: BarChart3 },
]

const pageNames: Record<string, string> = {
  '/': 'Query',
  '/upload': 'Upload',
  '/eval': 'Evaluation',
}

export default function Layout() {
  const location = useLocation()
  const currentPage = pageNames[location.pathname] ?? 'Page'

  return (
    <div className="admin-wrapper">
      <aside className="admin-sidebar">
        <div className="sidebar-logo">
          <Search size={20} className="sidebar-logo-icon" />
          <span className="sidebar-logo-text">Doc QA</span>
        </div>
        <div className="nav-group-title">Menu</div>
        <nav>
          <ul className="nav-list">
            {navItems.map(({ to, label, icon: Icon }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                >
                  <Icon size={20} className="nav-icon" />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <div className="admin-content">
        <header className="admin-header">
          <div className="breadcrumb">
            <span>Doc QA</span>
            <span>/</span>
            <span className="breadcrumb-current">{currentPage}</span>
          </div>
        </header>
        <main className="admin-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
