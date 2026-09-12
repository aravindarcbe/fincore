const BASE = '/api'

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // ignore
    }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  return res.json()
}

function toFormData(fields) {
  const fd = new FormData()
  for (const [key, value] of Object.entries(fields)) {
    if (value === null || value === undefined || value === '') continue
    fd.append(key, value)
  }
  return fd
}

const json = (method, path, body) =>
  fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }).then(handle)

const form = (method, path, fields, file) => {
  const fd = toFormData(fields)
  if (file) fd.append('document', file)
  return fetch(`${BASE}${path}`, { method, body: fd }).then(handle)
}

export const api = {
  dashboard: () => json('GET', '/dashboard'),

  loans: {
    list: () => json('GET', '/loans'),
    create: (fields, file) => form('POST', '/loans', fields, file),
    update: (id, fields) => json('PUT', `/loans/${id}`, fields),
    remove: (id) => json('DELETE', `/loans/${id}`),
    attachDocument: (id, file) => form('POST', `/loans/${id}/document`, {}, file),
  },

  salary: {
    list: () => json('GET', '/salary'),
    create: (fields, file) => form('POST', '/salary', fields, file),
    remove: (id) => json('DELETE', `/salary/${id}`),
  },

  pf: {
    get: () => json('GET', '/pf'),
    updateProfile: (fields) => json('PUT', '/pf/profile', fields),
    addSnapshot: (fields, file) => form('POST', '/pf/snapshots', fields, file),
    removeSnapshot: (id) => json('DELETE', `/pf/snapshots/${id}`),
  },

  insurance: {
    list: () => json('GET', '/insurance'),
    create: (fields, file) => form('POST', '/insurance', fields, file),
    update: (id, fields) => json('PUT', `/insurance/${id}`, fields),
    remove: (id) => json('DELETE', `/insurance/${id}`),
    addPayment: (id, fields) => json('POST', `/insurance/${id}/payments`, fields),
    removePayment: (id) => json('DELETE', `/insurance/payments/${id}`),
  },

  creditCards: {
    list: () => json('GET', '/creditcards'),
    create: (fields) => json('POST', '/creditcards', fields),
    update: (id, fields) => json('PUT', `/creditcards/${id}`, fields),
    remove: (id) => json('DELETE', `/creditcards/${id}`),
  },

  fileUrl: (storedName) => `${BASE}/files/${storedName}`,

  extract: {
    loan: (file) => form('POST', '/extract/loan', {}, file),
    insurance: (file) => form('POST', '/extract/insurance', {}, file),
    salary: (file) => form('POST', '/extract/salary', {}, file),
  },
}
