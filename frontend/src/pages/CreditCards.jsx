import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { money, dateStr } from '../format.js'
import Modal from '../components/Modal.jsx'
import StatCard from '../components/StatCard.jsx'

const emptyForm = { card_name: '', bank: '', credit_limit: '', outstanding_amount: '', min_due: '', due_date: '', notes: '' }

export default function CreditCards() {
  const [cards, setCards] = useState(null)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)

  const load = () => api.creditCards.list().then(setCards).catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  async function handleDelete(id) {
    if (!confirm('Delete this card?')) return
    await api.creditCards.remove(id)
    load()
  }

  if (error) return <div className="error-text">{error}</div>
  if (!cards) return <div className="loading-text">Loading credit cards…</div>

  const totalOutstanding = cards.reduce((s, c) => s + c.outstanding_amount, 0)
  const totalLimit = cards.reduce((s, c) => s + c.credit_limit, 0)

  return (
    <>
      <div className="page-header">
        <h2>Credit Cards</h2>
        <button className="btn btn-primary" onClick={() => setEditing({})}>
          + Add card
        </button>
      </div>

      <div className="stats-grid">
        <StatCard label="Total outstanding" value={money(totalOutstanding)} tone={totalOutstanding > 0 ? 'danger' : 'good'} icon="card" />
        <StatCard label="Total credit limit" value={money(totalLimit)} icon="card" />
        <StatCard label="Available credit" value={money(totalLimit - totalOutstanding)} tone="good" icon="card" />
      </div>

      <div className="panel">
        {cards.length === 0 ? (
          <div className="empty-state">No cards yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Card / Bank</th>
                <th>Limit</th>
                <th>Outstanding</th>
                <th>Min due</th>
                <th>Due date</th>
                <th>Last updated</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {cards.map((c) => (
                <tr key={c.id}>
                  <td>
                    <strong>{c.card_name}</strong>
                    <div className="muted">{c.bank}</div>
                  </td>
                  <td>{money(c.credit_limit)}</td>
                  <td>{money(c.outstanding_amount)}</td>
                  <td>{money(c.min_due)}</td>
                  <td>{dateStr(c.due_date)}</td>
                  <td className="muted">{dateStr(c.last_updated_date)}</td>
                  <td>
                    <div className="row-actions">
                      <button className="btn btn-small" onClick={() => setEditing(c)}>
                        Edit
                      </button>
                      <button className="btn btn-small btn-danger" onClick={() => handleDelete(c.id)}>
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
        <CardFormModal
          card={editing}
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

function CardFormModal({ card, onClose, onSaved }) {
  const isNew = card.id === undefined
  const [form, setForm] = useState(
    isNew
      ? emptyForm
      : {
          card_name: card.card_name,
          bank: card.bank,
          credit_limit: card.credit_limit,
          outstanding_amount: card.outstanding_amount,
          min_due: card.min_due ?? '',
          due_date: card.due_date ?? '',
          notes: card.notes,
        },
  )
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
        credit_limit: Number(form.credit_limit || 0),
        outstanding_amount: Number(form.outstanding_amount || 0),
        min_due: form.min_due === '' ? null : Number(form.min_due),
        due_date: form.due_date === '' ? null : form.due_date,
      }
      if (isNew) {
        await api.creditCards.create(payload)
      } else {
        await api.creditCards.update(card.id, payload)
      }
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={isNew ? 'Add credit card' : 'Update credit card'} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div>
            <label>Card name *</label>
            <input required value={form.card_name} onChange={(e) => set('card_name', e.target.value)} />
          </div>
          <div>
            <label>Bank</label>
            <input value={form.bank} onChange={(e) => set('bank', e.target.value)} />
          </div>
          <div>
            <label>Credit limit</label>
            <input type="number" step="0.01" value={form.credit_limit} onChange={(e) => set('credit_limit', e.target.value)} />
          </div>
          <div>
            <label>Current outstanding *</label>
            <input required type="number" step="0.01" value={form.outstanding_amount} onChange={(e) => set('outstanding_amount', e.target.value)} />
          </div>
          <div>
            <label>Minimum due</label>
            <input type="number" step="0.01" value={form.min_due} onChange={(e) => set('min_due', e.target.value)} />
          </div>
          <div>
            <label>Due date</label>
            <input type="date" value={form.due_date} onChange={(e) => set('due_date', e.target.value)} />
          </div>
          <div className="full">
            <label>Notes</label>
            <textarea rows={2} value={form.notes} onChange={(e) => set('notes', e.target.value)} />
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
