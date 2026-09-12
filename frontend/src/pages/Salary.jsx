import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { money, dateStr } from '../format.js'
import Modal from '../components/Modal.jsx'
import StatCard from '../components/StatCard.jsx'

const emptyForm = { effective_date: '', gross_amount: '', net_amount: '', notes: '' }

export default function Salary() {
  const [entries, setEntries] = useState(null)
  const [error, setError] = useState('')
  const [adding, setAdding] = useState(false)

  const load = () => api.salary.list().then(setEntries).catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  async function handleDelete(id) {
    if (!confirm('Delete this salary entry?')) return
    await api.salary.remove(id)
    load()
  }

  if (error) return <div className="error-text">{error}</div>
  if (!entries) return <div className="loading-text">Loading salary history…</div>

  const today = new Date().toISOString().slice(0, 10)
  const current = entries.find((e) => e.effective_date <= today)

  return (
    <>
      <div className="page-header">
        <h2>Salary</h2>
        <button className="btn btn-primary" onClick={() => setAdding(true)}>
          + Add salary revision
        </button>
      </div>

      <div className="stats-grid">
        <StatCard label="Current gross (monthly)" value={money(current?.gross_amount)} />
        <StatCard label="Current net / in-hand" value={money(current?.net_amount)} />
        <StatCard label="Effective since" value={current ? dateStr(current.effective_date) : '—'} />
      </div>

      <div className="panel">
        <h3>Revision history</h3>
        <p className="muted" style={{ marginTop: -8 }}>
          Every hike / revision is a new entry (dated from when it took effect) — nothing is overwritten, so your full salary
          history stays visible.
        </p>
        {entries.length === 0 ? (
          <div className="empty-state">No salary entries yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Effective from</th>
                <th>Gross</th>
                <th>Net</th>
                <th>Notes</th>
                <th>Doc</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id}>
                  <td>{dateStr(e.effective_date)}</td>
                  <td>{money(e.gross_amount)}</td>
                  <td>{money(e.net_amount)}</td>
                  <td className="muted">{e.notes}</td>
                  <td>
                    {e.document_path && (
                      <a className="doc-link" href={api.fileUrl(e.document_path)} target="_blank" rel="noreferrer">
                        View
                      </a>
                    )}
                  </td>
                  <td>
                    <button className="btn btn-small btn-danger" onClick={() => handleDelete(e.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {adding && (
        <SalaryFormModal
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false)
            load()
          }}
        />
      )}
    </>
  )
}

function SalaryFormModal({ onClose, onSaved }) {
  const [form, setForm] = useState(emptyForm)
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
      await api.salary.create(
        {
          ...form,
          gross_amount: Number(form.gross_amount),
          net_amount: form.net_amount === '' ? null : Number(form.net_amount),
        },
        file,
      )
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title="Add salary revision" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div>
            <label>Effective from *</label>
            <input required type="date" value={form.effective_date} onChange={(e) => set('effective_date', e.target.value)} />
          </div>
          <div>
            <label>Gross (monthly) *</label>
            <input required type="number" step="0.01" value={form.gross_amount} onChange={(e) => set('gross_amount', e.target.value)} />
          </div>
          <div className="full">
            <label>Net / in-hand (monthly)</label>
            <input type="number" step="0.01" value={form.net_amount} onChange={(e) => set('net_amount', e.target.value)} />
          </div>
          <div className="full">
            <label>Notes (e.g. "annual hike letter")</label>
            <textarea rows={2} value={form.notes} onChange={(e) => set('notes', e.target.value)} />
          </div>
          <div className="full">
            <label>Attach payslip / hike letter (optional)</label>
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
