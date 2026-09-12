import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { money, dateStr } from '../format.js'
import Modal from '../components/Modal.jsx'

const TYPES = ['health', 'term', 'life', 'other']
const FREQUENCIES = ['monthly', 'quarterly', 'half-yearly', 'yearly']

const emptyForm = {
  policy_name: '',
  policy_type: 'health',
  insurer: '',
  policy_number: '',
  sum_assured: '',
  premium_amount: '',
  premium_frequency: 'yearly',
  start_date: '',
  term_years: '',
  maturity_date: '',
  maturity_benefit: '',
  notes: '',
}

export default function Insurance() {
  const [policies, setPolicies] = useState(null)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)
  const [paymentsFor, setPaymentsFor] = useState(null)

  const load = () => api.insurance.list().then(setPolicies).catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  async function handleDelete(id) {
    if (!confirm('Delete this policy?')) return
    await api.insurance.remove(id)
    load()
  }

  if (error) return <div className="error-text">{error}</div>
  if (!policies) return <div className="loading-text">Loading insurance…</div>

  return (
    <>
      <div className="page-header">
        <h2>Insurance</h2>
        <button className="btn btn-primary" onClick={() => setEditing({})}>
          + Add policy
        </button>
      </div>

      <div className="panel">
        {policies.length === 0 ? (
          <div className="empty-state">No policies yet — add a health or term plan above.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Policy</th>
                <th>Type</th>
                <th>Sum assured</th>
                <th>Premium</th>
                <th>Paid so far</th>
                <th>Next due</th>
                <th>Maturity</th>
                <th>Doc</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {policies.map((p) => (
                <tr key={p.id}>
                  <td>
                    <strong>{p.policy_name}</strong>
                    <div className="muted">{p.insurer}</div>
                  </td>
                  <td className="muted">{p.policy_type}</td>
                  <td>{money(p.sum_assured)}</td>
                  <td>
                    {money(p.premium_amount)} <span className="muted">/ {p.premium_frequency}</span>
                  </td>
                  <td>
                    <button className="doc-link" style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 0 }} onClick={() => setPaymentsFor(p)}>
                      {p.premiums_paid_count} paid ({money(p.total_paid)})
                    </button>
                  </td>
                  <td>{dateStr(p.next_due_date)}</td>
                  <td>
                    {dateStr(p.computed_maturity_date)}
                    {p.maturity_benefit ? <div className="muted">{money(p.maturity_benefit)}</div> : null}
                  </td>
                  <td>
                    {p.document_path && (
                      <a className="doc-link" href={api.fileUrl(p.document_path)} target="_blank" rel="noreferrer">
                        View
                      </a>
                    )}
                  </td>
                  <td>
                    <div className="row-actions">
                      <button className="btn btn-small" onClick={() => setEditing(p)}>
                        Edit
                      </button>
                      <button className="btn btn-small btn-danger" onClick={() => handleDelete(p.id)}>
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
        <PolicyFormModal
          policy={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            load()
          }}
        />
      )}
      {paymentsFor && (
        <PaymentsModal
          policy={paymentsFor}
          onClose={() => setPaymentsFor(null)}
          onChanged={() => {
            load()
          }}
        />
      )}
    </>
  )
}

function PolicyFormModal({ policy, onClose, onSaved }) {
  const isNew = policy.id === undefined
  const [form, setForm] = useState(
    isNew
      ? emptyForm
      : {
          policy_name: policy.policy_name,
          policy_type: policy.policy_type,
          insurer: policy.insurer,
          policy_number: policy.policy_number,
          sum_assured: policy.sum_assured,
          premium_amount: policy.premium_amount,
          premium_frequency: policy.premium_frequency,
          start_date: policy.start_date,
          term_years: policy.term_years ?? '',
          maturity_date: policy.maturity_date ?? '',
          maturity_benefit: policy.maturity_benefit ?? '',
          notes: policy.notes,
          active: policy.active,
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
        sum_assured: Number(form.sum_assured || 0),
        premium_amount: Number(form.premium_amount),
        term_years: form.term_years === '' ? null : Number(form.term_years),
        maturity_date: form.maturity_date === '' ? null : form.maturity_date,
        maturity_benefit: form.maturity_benefit === '' ? null : Number(form.maturity_benefit),
      }
      if (isNew) {
        await api.insurance.create(payload, file)
      } else {
        await api.insurance.update(policy.id, { ...payload, active: form.active !== false })
      }
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={isNew ? 'Add insurance policy' : 'Edit policy'} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="full">
            <label>Policy name *</label>
            <input required value={form.policy_name} onChange={(e) => set('policy_name', e.target.value)} />
          </div>
          <div>
            <label>Type</label>
            <select value={form.policy_type} onChange={(e) => set('policy_type', e.target.value)}>
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Insurer</label>
            <input value={form.insurer} onChange={(e) => set('insurer', e.target.value)} />
          </div>
          <div>
            <label>Policy number</label>
            <input value={form.policy_number} onChange={(e) => set('policy_number', e.target.value)} />
          </div>
          <div>
            <label>Sum assured / cover</label>
            <input type="number" step="0.01" value={form.sum_assured} onChange={(e) => set('sum_assured', e.target.value)} />
          </div>
          <div>
            <label>Premium amount *</label>
            <input required type="number" step="0.01" value={form.premium_amount} onChange={(e) => set('premium_amount', e.target.value)} />
          </div>
          <div>
            <label>Premium frequency</label>
            <select value={form.premium_frequency} onChange={(e) => set('premium_frequency', e.target.value)}>
              {FREQUENCIES.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>First installment date *</label>
            <input required type="date" value={form.start_date} onChange={(e) => set('start_date', e.target.value)} />
          </div>
          <div>
            <label>Policy term (years)</label>
            <input type="number" value={form.term_years} onChange={(e) => set('term_years', e.target.value)} />
          </div>
          <div>
            <label>Maturity date (overrides term calc)</label>
            <input type="date" value={form.maturity_date} onChange={(e) => set('maturity_date', e.target.value)} />
          </div>
          <div className="full">
            <label>Maturity / benefit amount</label>
            <input type="number" step="0.01" value={form.maturity_benefit} onChange={(e) => set('maturity_benefit', e.target.value)} />
          </div>
          <div className="full">
            <label>Notes</label>
            <textarea rows={2} value={form.notes} onChange={(e) => set('notes', e.target.value)} />
          </div>
          {isNew && (
            <div className="full">
              <label>Attach policy document (optional)</label>
              <input type="file" onChange={(e) => setFile(e.target.files[0] || null)} />
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

function PaymentsModal({ policy, onClose, onChanged }) {
  const [payments, setPayments] = useState(policy.payments)
  const [form, setForm] = useState({ paid_date: '', amount: policy.premium_amount, note: '' })
  const [error, setError] = useState('')

  async function handleAdd(e) {
    e.preventDefault()
    setError('')
    try {
      const updated = await api.insurance.addPayment(policy.id, { ...form, amount: Number(form.amount) })
      setPayments(updated.payments)
      setForm({ paid_date: '', amount: policy.premium_amount, note: '' })
      onChanged()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(id) {
    await api.insurance.removePayment(id)
    setPayments((p) => p.filter((x) => x.id !== id))
    onChanged()
  }

  return (
    <Modal title={`Premium payments — ${policy.policy_name}`} onClose={onClose}>
      {payments.length === 0 ? (
        <p className="muted">No payments logged yet — premiums-paid count is estimated from the start date instead.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Note</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => (
              <tr key={p.id}>
                <td>{dateStr(p.paid_date)}</td>
                <td>{money(p.amount)}</td>
                <td className="muted">{p.note}</td>
                <td>
                  <button className="btn btn-small btn-danger" onClick={() => handleDelete(p.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <form onSubmit={handleAdd} style={{ marginTop: 16 }}>
        <div className="form-grid">
          <div>
            <label>Paid date *</label>
            <input required type="date" value={form.paid_date} onChange={(e) => setForm((f) => ({ ...f, paid_date: e.target.value }))} />
          </div>
          <div>
            <label>Amount *</label>
            <input required type="number" step="0.01" value={form.amount} onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))} />
          </div>
          <div className="full">
            <label>Note</label>
            <input value={form.note} onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))} />
          </div>
        </div>
        {error && <div className="error-text">{error}</div>}
        <div className="form-actions">
          <button type="submit" className="btn btn-primary">
            Log payment
          </button>
        </div>
      </form>
    </Modal>
  )
}
