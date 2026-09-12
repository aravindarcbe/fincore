import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { money, dateStr } from '../format.js'
import Modal from '../components/Modal.jsx'
import AutoFillUpload from '../components/AutoFillUpload.jsx'

const LOAN_TYPES = ['personal', 'home', 'car', 'education', 'gold', 'other']

const emptyForm = {
  name: '',
  lender: '',
  loan_type: 'personal',
  principal_amount: '',
  interest_rate: '',
  tenure_months: '',
  emi_amount: '',
  start_date: '',
  notes: '',
}

export default function Loans() {
  const [loans, setLoans] = useState(null)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null) // null = closed, {} = new, {...loan} = edit
  const [showClosed, setShowClosed] = useState(false)

  const load = () => api.loans.list().then(setLoans).catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  async function handleDelete(id) {
    if (!confirm('Delete this loan?')) return
    await api.loans.remove(id)
    load()
  }

  async function handleAttach(id, file) {
    await api.loans.attachDocument(id, file)
    load()
  }

  if (error) return <div className="error-text">{error}</div>
  if (!loans) return <div className="loading-text">Loading loans…</div>

  const closedCount = loans.filter((l) => l.status === 'closed').length
  const visibleLoans = showClosed ? loans : loans.filter((l) => l.status !== 'closed')

  return (
    <>
      <div className="page-header">
        <h2>Loans</h2>
        <button className="btn btn-primary" onClick={() => setEditing({})}>
          + Add loan
        </button>
      </div>

      {closedCount > 0 && (
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12, cursor: 'pointer' }}>
          <input
            type="checkbox"
            style={{ width: 'auto' }}
            checked={showClosed}
            onChange={(e) => setShowClosed(e.target.checked)}
          />
          Show closed loans ({closedCount})
        </label>
      )}

      <div className="panel">
        {visibleLoans.length === 0 ? (
          <div className="empty-state">
            {loans.length === 0
              ? 'No loans yet. Add your first personal loan above.'
              : 'No active loans — all your loans are closed.'}
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name / Lender</th>
                <th>Type</th>
                <th>Principal</th>
                <th>Rate</th>
                <th>EMI</th>
                <th>Pending</th>
                <th>Balance principal</th>
                <th>Balance to pay</th>
                <th>Last EMI</th>
                <th>Status</th>
                <th>Doc</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {visibleLoans.map((l) => (
                <tr key={l.id}>
                  <td>
                    <strong>{l.name}</strong>
                    <div className="muted">{l.lender}</div>
                  </td>
                  <td className="muted">{l.loan_type}</td>
                  <td>{money(l.principal_amount)}</td>
                  <td>{l.interest_rate}%</td>
                  <td>{money(l.computed_emi)}</td>
                  <td>{l.pending_months} mo</td>
                  <td>{money(l.balance_principal)}</td>
                  <td>{money(l.balance_amount_to_pay)}</td>
                  <td>{dateStr(l.last_emi_date)}</td>
                  <td>
                    <span className={`badge badge-${l.status === 'active' ? 'active' : 'closed'}`}>
                      {l.status}
                    </span>
                  </td>
                  <td>
                    {l.document_path ? (
                      <a className="doc-link" href={api.fileUrl(l.document_path)} target="_blank" rel="noreferrer">
                        View
                      </a>
                    ) : (
                      <label className="doc-link" style={{ cursor: 'pointer' }}>
                        Attach
                        <input
                          type="file"
                          hidden
                          onChange={(e) => e.target.files[0] && handleAttach(l.id, e.target.files[0])}
                        />
                      </label>
                    )}
                  </td>
                  <td>
                    <div className="row-actions">
                      <button className="btn btn-small" onClick={() => setEditing(l)}>
                        Edit
                      </button>
                      <button className="btn btn-small btn-danger" onClick={() => handleDelete(l.id)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editing !== null && (
        <LoanFormModal
          loan={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            load()
          }}
        />
      )}
    </>
  )
}

function LoanFormModal({ loan, onClose, onSaved }) {
  const isNew = loan.id === undefined
  const [form, setForm] = useState(
    isNew
      ? emptyForm
      : {
          name: loan.name,
          lender: loan.lender,
          loan_type: loan.loan_type,
          principal_amount: loan.principal_amount,
          interest_rate: loan.interest_rate,
          tenure_months: loan.tenure_months,
          emi_amount: loan.emi_amount ?? '',
          start_date: loan.start_date,
          notes: loan.notes,
          closed: loan.closed,
        },
  )
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
      const payload = {
        ...form,
        principal_amount: Number(form.principal_amount),
        interest_rate: Number(form.interest_rate || 0),
        tenure_months: Number(form.tenure_months),
        emi_amount: form.emi_amount === '' ? null : Number(form.emi_amount),
      }
      if (isNew) {
        await api.loans.create(payload, file)
      } else {
        await api.loans.update(loan.id, { ...payload, closed: !!form.closed })
      }
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={isNew ? 'Add loan' : 'Edit loan'} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          {isNew && (
            <AutoFillUpload
              extractFn={api.extract.loan}
              onFileSelected={setFile}
              onExtracted={(extracted) =>
                setForm((f) => ({
                  ...f,
                  lender: f.lender || extracted.lender || f.lender,
                  principal_amount: f.principal_amount || extracted.principal_amount || f.principal_amount,
                  interest_rate: f.interest_rate || extracted.interest_rate || f.interest_rate,
                  tenure_months: f.tenure_months || extracted.tenure_months || f.tenure_months,
                  emi_amount: f.emi_amount || extracted.emi_amount || f.emi_amount,
                  start_date: f.start_date || extracted.start_date || f.start_date,
                }))
              }
              renderDuplicate={(d) =>
                `"${d.name}" (${d.lender || 'no lender listed'}, ${money(d.principal_amount)}, started ${dateStr(d.start_date)})`
              }
            />
          )}
          <div className="full">
            <label>Loan name *</label>
            <input required value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="e.g. Personal Loan - HDFC" />
          </div>
          <div>
            <label>Lender / Bank</label>
            <input value={form.lender} onChange={(e) => set('lender', e.target.value)} />
          </div>
          <div>
            <label>Type</label>
            <select value={form.loan_type} onChange={(e) => set('loan_type', e.target.value)}>
              {LOAN_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Total loan amount (principal) *</label>
            <input required type="number" step="0.01" value={form.principal_amount} onChange={(e) => set('principal_amount', e.target.value)} />
          </div>
          <div>
            <label>Annual interest rate (%) *</label>
            <input required type="number" step="0.01" value={form.interest_rate} onChange={(e) => set('interest_rate', e.target.value)} />
          </div>
          <div>
            <label>Tenure (months) *</label>
            <input required type="number" value={form.tenure_months} onChange={(e) => set('tenure_months', e.target.value)} />
          </div>
          <div>
            <label>EMI amount (leave blank to auto-calculate)</label>
            <input type="number" step="0.01" value={form.emi_amount} onChange={(e) => set('emi_amount', e.target.value)} />
          </div>
          <div className="full">
            <label>First EMI date *</label>
            <input required type="date" value={form.start_date} onChange={(e) => set('start_date', e.target.value)} />
          </div>
          <div className="full">
            <label>Notes</label>
            <textarea rows={2} value={form.notes} onChange={(e) => set('notes', e.target.value)} />
          </div>
          {!isNew && (
            <div className="full">
              <label>
                <input
                  type="checkbox"
                  style={{ width: 'auto', display: 'inline-block', marginRight: 6 }}
                  checked={!!form.closed}
                  onChange={(e) => set('closed', e.target.checked)}
                />
                Mark as closed / foreclosed
              </label>
            </div>
          )}
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
