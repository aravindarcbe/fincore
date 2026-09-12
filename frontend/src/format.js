export function money(value) {
  if (value === null || value === undefined) return '—'
  return '₹' + Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

export function dateStr(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}
