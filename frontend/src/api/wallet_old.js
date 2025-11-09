import axios from 'axios'

// API Base URL
export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5007'

// Get balance
export async function getBalance(grpcConfig) {
  const response = await axios.post(`${API_BASE}/api/balance`, {
    grpc_config: grpcConfig
  })
  return response.data
}

// Get active address
export async function getActiveAddress() {
  const response = await axios.get(`${API_BASE}/api/active-address`)
  return response.data
}

// Set active address
export async function setActiveAddress(address, grpcConfig) {
  const response = await axios.post(`${API_BASE}/api/set-active-address`, {
    address: address,
    grpc_config: grpcConfig
  })
  return response.data
}

// List master addresses
export async function listMasterAddresses() {
  const response = await axios.get(`${API_BASE}/api/list-master-addresses`)
  return response.data
}

// Get transaction history
export async function getTransactionHistory() {
  const response = await axios.get(`${API_BASE}/api/transaction-history`)
  return response.data
}

// Create transaction
export async function createTransaction(data) {
  const response = await axios.post(`${API_BASE}/api/create-transaction`, data)
  return response.data
}

// Sign transaction
export async function signTransaction(transactionName) {
  const response = await axios.post(`${API_BASE}/api/sign-transaction`, {
    transaction_name: transactionName
  })
  return response.data
}

// Send transaction
export async function sendTransaction(transactionName) {
  const response = await axios.post(`${API_BASE}/api/send-transaction`, {
    transaction_name: transactionName
  })
  return response.data
}

// Import keys from file
export async function importKeysFromFile(formData) {
  const response = await axios.post(`${API_BASE}/api/import-keys`, formData)
  return response.data
}

// Import from seedphrase
export async function importFromSeedphrase(seedphrase, version) {
  const response = await axios.post(`${API_BASE}/api/import-seedphrase`, {
    seedphrase: seedphrase,
    version: parseInt(version)
  })
  return response.data
}

// Show seedphrase
export async function showSeedphrase() {
  const response = await axios.get(`${API_BASE}/api/show-seedphrase`)
  return response.data
}

// Export keys URL
export function getExportKeysUrl() {
  return `${API_BASE}/api/export-keys`
}