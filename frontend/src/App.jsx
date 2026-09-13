import { useState } from 'react'
import Dashboard from './pages/Dashboard.jsx'
import Loans from './pages/Loans.jsx'
import Salary from './pages/Salary.jsx'
import PF from './pages/PF.jsx'
import Insurance from './pages/Insurance.jsx'
import CreditCards from './pages/CreditCards.jsx'
import Icon from './icons.jsx'

const TABS = [
  { key: 'dashboard', label: 'Dashboard', icon: 'dashboard', component: Dashboard },
  { key: 'loans', label: 'Loans', icon: 'loan', component: Loans },
  { key: 'salary', label: 'Salary', icon: 'wallet', component: Salary },
  { key: 'pf', label: 'Provident Fund', icon: 'piggy', component: PF },
  { key: 'insurance', label: 'Insurance', icon: 'shield', component: Insurance },
  { key: 'creditcards', label: 'Credit Cards', icon: 'card', component: CreditCards },
]

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const Active = TABS.find((t) => t.key === tab)?.component ?? Dashboard

  return (
    <>
      <nav className="sidebar">
        <h1>
          <span className="brand-mark">F</span>
          Fin<span>Core</span>
        </h1>
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`nav-item${tab === t.key ? ' active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            <Icon name={t.icon} size={17} />
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
