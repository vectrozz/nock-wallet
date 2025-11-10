// API Base URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5007'

// Get balance - NO MORE grpcConfig parameter!
export async function getBalance() {
  const response = await fetch(`${API_BASE}/api/balance`)
  return response.json()
}

// Get active address - NO MORE grpcConfig parameter!
export async function getActiveAddress() {
  const response = await fetch(`${API_BASE}/api/active-address`)
  return response.json()
}

// List master addresses - NO MORE grpcConfig parameter!
export async function listMasterAddresses() {
  const response = await fetch(`${API_BASE}/api/list-master-addresses`)
  return response.json()
}

// Set active address - NO MORE grpcConfig in body!
export async function setActiveAddress(address) {
  const response = await fetch(`${API_BASE}/api/set-active-address`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      address: address
    })
  })
  return response.json()
}

// Get transaction history
export async function getTransactionHistory() {
  const response = await fetch(`${API_BASE}/api/transaction-history`)
  return response.json()
}

// Create transaction
export async function createTransaction(data) {
  const response = await fetch(`${API_BASE}/api/create-transaction`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  return response.json()
}

// Sign transaction
export async function signTransaction(transactionName) {
  const response = await fetch(`${API_BASE}/api/sign-transaction`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      transaction_name: transactionName
    })
  })
  return response.json()
}

// Send transaction
export async function sendTransaction(transactionName) {
  const response = await fetch(`${API_BASE}/api/send-transaction`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      transaction_name: transactionName
    })
  })
  return response.json()
}

// Import keys from file
export async function importKeysFromFile(formData) {
  const response = await fetch(`${API_BASE}/api/import-keys`, {
    method: 'POST',
    body: formData
  })
  return response.json()
}

// Import from seedphrase
export async function importFromSeedphrase(seedphrase, version) {
  const response = await fetch(`${API_BASE}/api/import-seedphrase`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      seedphrase: seedphrase,
      version: parseInt(version)
    })
  })
  return response.json()
}

// Show seedphrase
export async function showSeedphrase() {
  const response = await fetch(`${API_BASE}/api/show-seedphrase`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    }
  })
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  return await response.json()
}

// Export keys URL
export function getExportKeysUrl() {
  return `${API_BASE}/api/export-keys`
}

// Import keys from seed (existing - for backward compatibility)
export async function importKeys(data) {
  const response = await fetch(`${API_BASE}/api/import-keys`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  return response.json()
}

// ✅ NEW: Import keys from seedphrase with version
export async function importKeysFromSeedphrase(seed, version) {
  const response = await fetch(`${API_BASE}/api/import-keys-seedphrase`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      seedphrase: seed,
      version: version
    })
  })
  return response.json()
}