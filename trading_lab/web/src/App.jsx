import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import Dashboard from './pages/Dashboard'
import Strategies from './pages/Strategies'
import Backtests from './pages/Backtests'
import NewBacktest from './pages/NewBacktest'
import BacktestDetail from './pages/BacktestDetail'

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/strategies', label: 'Strategies' },
  { path: '/backtests', label: 'Backtests' },
]

function NavLink({ to, children }) {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link
      to={to}
      className={clsx(
        'px-4 py-2 rounded-md text-sm font-medium transition-colors',
        isActive
          ? 'bg-primary-600 text-white'
          : 'text-gray-600 hover:bg-gray-100'
      )}
    >
      {children}
    </Link>
  )
}

function App() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <h1 className="text-xl font-bold text-gray-900">
                Trading Lab
              </h1>
              <nav className="flex gap-2">
                {navItems.map(item => (
                  <NavLink key={item.path} to={item.path}>
                    {item.label}
                  </NavLink>
                ))}
              </nav>
            </div>
            <Link to="/backtests/new" className="btn btn-primary">
              New Backtest
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/backtests" element={<Backtests />} />
          <Route path="/backtests/new" element={<NewBacktest />} />
          <Route path="/backtests/:id" element={<BacktestDetail />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
