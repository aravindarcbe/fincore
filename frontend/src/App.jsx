import { useState } from 'react'
import Dashboard from './pages/Dashboard.jsx'
import Loans from './pages/Loans.jsx'
import Salary from './pages/Salary.jsx'
import PF from './pages/PF.jsx'
import Insurance from './pages/Insurance.jsx'
import CreditCards from './pages/CreditCards.jsx'

const TABS = [
  { key: 'dashboard', label: 'Dashboard', component: Dashboard },
  { key: 'loans', label: 'Loans', component: Loans },
  { key: 'salary', label: 'Salary', component: Salary },
  { key: 'pf', label: 'Provident Fund', component: PF },
  { key: 'insurance', label: 'Insurance', component: Insurance },
  { key: 'creditcards', label: 'Credit Cards', component: CreditCards },
]

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const Active = TABS.find((t) => t.key === tab)?.component ?? Dashboard

  return (
    <>
      <nav className="sidebar">
        <h1>
          Fin<span>Core</span>
        </h1>
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`nav-item${tab === t.key ? ' active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <main className="main">
        <Active />
      </main>
    </>
  )
}
