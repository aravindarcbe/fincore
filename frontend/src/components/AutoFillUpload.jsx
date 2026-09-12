import { useState } from 'react'

// Uploads a PDF, sends it to the given extract endpoint, and reports back
// the fields it could pull out plus any likely-duplicate existing record.
// The same file is also handed back via onFileSelected so it can be
// attached to the record on save - no need to upload it twice.
export default function AutoFillUpload({ extractFn, onExtracted, onFileSelected, renderDuplicate, label }) {
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [duplicate, setDuplicate] = useState(null)
  const [error, setError] = useState('')

  async function handleChange(e) {
    const file = e.target.files[0]
    if (!file) return
    onFileSelected?.(file)
    setStatus('loading')
    setError('')
    setDuplicate(null)
    try {
      const result = await extractFn(file)
      onExtracted(result.extracted)
      setDuplicate(result.duplicate)
      setStatus('done')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <div className="full">
      <label>{label || 'Auto-fill from PDF (optional)'}</label>
      <input type="file" accept="application/pdf" onChange={handleChange} />
      <p className="muted" style={{ marginTop: 4, marginBottom: 0 }}>
        Reads what it can from the document and fills in the fields below — always double-check before saving. Also
        gets attached to the record automatically.
      </p>
      {status === 'loading' && <p className="muted">Reading document…</p>}
      {status === 'done' && !duplicate && (
        <p style={{ color: 'var(--good)', fontSize: 13 }}>Filled in what we could find — please review the fields below.</p>
      )}
      {error && <div className="error-text">{error}</div>}
      {duplicate && (
        <div className="warning-banner">
          This looks like it may already be added: {renderDuplicate ? renderDuplicate(duplicate) : JSON.stringify(duplicate)}.
          You can still save this as a new entry if it's actually different.
        </div>
      )}
    </div>
  )
}
