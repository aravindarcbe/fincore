import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { money, dateStr } from '../format.js'
import StatCard from '../components/StatCard.jsx'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="error-text">{error}</div>
  if (!data) return <div className="loading-text">Loading dashboard…</div>

  const netWorthGap = data.total_credit_limit - data.total_credit_card_outstanding

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
      </div>

      <div className="stats-grid">
        <StatCard
          label="Total loan principal pending"
          value={money(data.total_loan_principal_outstanding)}
          sub={`${data.active_loans_count} active loan(s)`}
          tone={data.total_loan_principal_outstanding > 0 ? 'danger' : 'good'}
        />
        <StatCard
          label="EMI due this month"
          value={money(data.total_emi_due_this_month)}
        />
        <StatCard
          label="EMI paid this month"
          value={money(data.emi_paid_this_month)}
          sub={`${money(data.emi_due_this_month)} still due, ${money(data.emi_upcoming_this_month)} upcoming`}
          tone="good"
        />
        <StatCard
          label="Total remaining to pay (all loans)"
          value={money(data.total_loan_pending_amount)}
        />
        <StatCard
          label="Current monthly salary (gross)"
          value={money(data.current_salary?.gross_amount)}
          sub={data.current_salary ? `since ${dateStr(data.current_salary.effective_date)}` : 'no salary entry yet'}
        />
        <StatCard
          label="Salary credited this month?"
          value={data.salary_credited ? 'Yes' : 'Not yet'}
          sub={`1st Tuesday: ${dateStr(data.salary_credit_date)}`}
          tone={data.salary_credited ? 'good' : 'danger'}
        />
        <StatCard
          label="Remaining salary this month"
          value={data.remaining_salary_this_month === null ? '—' : money(data.remaining_salary_this_month)}
          sub="salary minus EMIs marked paid"
        />
        <StatCard label="PF balance (projected)" value={money(data.pf_current_balance)} tone="good" />
        <StatCard
          label="Insurance premium / year"
          value={money(data.total_insurance_premium_annualized)}
          sub={`${data.insurance_due_this_month.length} due this month`}
        />
        <StatCard
          label="Credit card outstanding"
          value={money(data.total_credit_card_outstanding)}
          sub={`of ${money(data.total_credit_limit)} limit`}
          tone={data.total_credit_card_outstanding > 0 ? 'danger' : 'good'}
        />
        <StatCard
          label="Available credit"
          value={money(netWorthGap)}
        />
      </div>

      <div className="panel">
        <h3>Loans ending soon</h3>
        {data.loans_ending_soon.length === 0 ? (
          <div className="empty-state">No loans ending in the next 3 months.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Lender</th>
                <th>EMI</th>
                <th>Pending months</th>
                <th>Balance principal</th>
                <th>Last EMI date</th>
              </tr>
            </thead>
            <tbody>
              {data.loans_ending_soon.map((l) => (
                <tr key={l.id}>
                  <td>{l.name}</td>
                  <td className="muted">{l.lender}</td>
                  <td>{money(l.computed_emi)}</td>
                  <td>{l.pending_months}</td>
                  <td>{money(l.balance_principal)}</td>
                  <td>{dateStr(l.last_emi_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel">
        <h3>Insurance due this month</h3>
        {data.insurance_due_this_month.length === 0 ? (
          <div className="empty-state">No premiums due this month.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Policy</th>
                <th>Type</th>
                <th>Premium</th>
                <th>Next due date</th>
              </tr>
            </thead>
            <tbody>
              {data.insurance_due_this_month.map((p) => (
                <tr key={p.id}>
                  <td>{p.policy_name}</td>
                  <td className="muted">{p.policy_type}</td>
                  <td>{money(p.premium_amount)}</td>
                  <td>{dateStr(p.next_due_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
