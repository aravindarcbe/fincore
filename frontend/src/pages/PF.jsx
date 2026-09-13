import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { money, dateStr } from '../format.js'
import Modal from '../components/Modal.jsx'
import StatCard from '../components/StatCard.jsx'

export default function PF() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [editingProfile, setEditingProfile] = useState(false)
  const [addingSnapshot, setAddingSnapshot] = useState(false)

  const load = () => api.pf.get().then(setData).catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  async function handleDeleteSnapshot(id) {
    if (!confirm('Delete this PF snapshot?')) return
    await api.pf.removeSnapshot(id)
    load()
  }

  if (error) return <div className="error-text">{error}</div>
  if (!data) return <div className="loading-text">Loading PF…</div>

  return (
    <>
      <div className="page-header">
        <h2>Provident Fund</h2>
        <div className="row-actions">
          <button className="btn" onClick={() => setEditingProfile(true)}>
            Edit contribution profile
          </button>
          <button className="btn btn-primary" onClick={() => setAddingSnapshot(true)}>
            + Add passbook balance
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <StatCard
          label="Projected current balance"
          value={money(data.current_balance)}
          sub={`as of ${dateStr(data.as_of)}`}
          tone="good"
          icon="piggy"
        />
        <StatCard label="Monthly employee contribution" value={money(data.profile.monthly_employee_contribution)} icon="wallet" />
        <StatCard label="Monthly employer contribution" value={money(data.profile.monthly_employer_contribution)} icon="wallet" />
        <StatCard label="Declared interest rate" value={`${data.profile.interest_rate_annual}%`} icon="trendUp" />
      </div>
      <p className="muted" style={{ marginTop: -12 }}>
        Projection = latest passbook balance + {data.months_projected} month(s) of contributions since, plus an estimated
        interest accrual. Add a fresh passbook/payslip balance snapshot whenever you get one for a more accurate baseline.
      </p>

      <div className="panel">
        <h3>Balance snapshots</h3>
        {data.snapshots.length === 0 ? (
          <div className="empty-state">No snapshots yet. Add your latest PF passbook balance to start tracking.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Balance</th>
                <th>Source</th>
                <th>Note</th>
                <th>Doc</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.snapshots.map((s) => (
                <tr key={s.id}>
                  <td>{dateStr(s.entry_date)}</td>
                  <td>{money(s.balance)}</td>
                  <td className="muted">{s.source}</td>
                  <td className="muted">{s.note}</td>
                  <td>
                    {s.document_path && (
                      <a className="doc-link" href={api.fileUrl(s.document_path)} target="_blank" rel="noreferrer">
                        View
                      </a>
                    )}
                  </td>
                  <td>
                    <button className="btn btn-small btn-danger" onClick={() => handleDeleteSnapshot(s.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editingProfile && (
        <ProfileFormModal
          profile={data.profile}
          onClose={() => setEditingProfile(false)}
          onSaved={() => {
            setEditingProfile(false)
            load()
          }}
        />
      )}
      {addingSnapshot && (
        <SnapshotFormModal
          onClose={() => setAddingSnapshot(false)}
          onSaved={() => {
            setAddingSnapshot(false)
            load()
          }}
        />
      )}
    </>
  )
}

function ProfileFormModal({ profile, onClose, onSaved }) {
  const [form, setForm] = useState({
    account_number: profile.account_number,
    monthly_employee_contribution: profile.monthly_employee_contribution,
    monthly_employer_contribution: profile.monthly_employer_contribution,
    interest_rate_annual: profile.interest_rate_annual,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.pf.updateProfile({
        ...form,
        monthly_employee_contribution: Number(form.monthly_employee_contribution),
        monthly_employer_contribution: Number(form.monthly_employer_contribution),
        interest_rate_annual: Number(form.interest_rate_annual),
      })
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title="PF contribution profile" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="full">
            <label>PF account number</label>
            <input value={form.account_number} onChange={(e) => set('account_number', e.target.value)} />
          </div>
          <div>
            <label>Monthly employee contribution (from payslip)</label>
            <input type="number" step="0.01" value={form.monthly_employee_contribution} onChange={(e) => set('monthly_employee_contribution', e.target.value)} />
          </div>
          <div>
            <label>Monthly employer contribution (from payslip)</label>
            <input type="number" step="0.01" value={form.monthly_employer_contribution} onChange={(e) => set('monthly_employer_contribution', e.target.value)} />
          </div>
          <div className="full">
            <label>Declared annual interest rate (%)</label>
            <input type="number" step="0.01" value={form.interest_rate_annual} onChange={(e) => set('interest_rate_annual', e.target.value)} />
          </div>
        </div>
        {error && <div className="error-text">{error}</div>}
        <div className="form-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function SnapshotFormModal({ onClose, onSaved }) {
  const [form, setForm] = useState({ entry_date: '', balance: '', source: 'passbook', note: '' })
  const [file, setFile] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.pf.addSnapshot({ ...form, balance: Number(form.balance) }, file)
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title="Add PF balance snapshot" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div>
            <label>As of date *</label>
            <input required type="date" value={form.entry_date} onChange={(e) => set('entry_date', e.target.value)} />
          </div>
          <div>
            <label>Balance *</label>
            <input required type="number" step="0.01" value={form.balance} onChange={(e) => set('balance', e.target.value)} />
          </div>
          <div>
            <label>Source</label>
            <select value={form.source} onChange={(e) => set('source', e.target.value)}>
              <option value="passbook">EPFO passbook</option>
              <option value="payslip">Payslip</option>
              <option value="manual">Manual estimate</option>
            </select>
          </div>
          <div className="full">
            <label>Note</label>
            <input value={form.note} onChange={(e) => set('note', e.target.value)} />
          </div>
          <div className="full">
            <label>Attach passbook / payslip (optional)</label>
            <input type="file" onChange={(e) => setFile(e.target.files[0] || null)} />
          </div>
        </div>
        {error && <div className="error-text">{error}</div>}
        <div className="form-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
