import './style.css'
import axios from 'axios'

// Use environment variable or fallback
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5007';

// DOM Elements
const loadingDisplay = document.getElementById('loadingDisplay')
const balanceDisplay = document.getElementById('balanceDisplay')
const errorDisplay = document.getElementById('errorDisplay')
const balanceContent = document.getElementById('balanceContent')
const notesCount = document.getElementById('notesCount')
const totalAssets = document.getElementById('totalAssets')
const notesList = document.getElementById('notesList')
const sendSelectedBtn = document.getElementById('sendSelectedBtn')
const historyList = document.getElementById('historyList')

// View tabs
const notesViewTab = document.getElementById('notesViewTab')
const historyViewTab = document.getElementById('historyViewTab')
const notesView = document.getElementById('notesView')
const historyView = document.getElementById('historyView')

// Transaction Modal Elements
const sendTxModal = document.getElementById('sendTxModal')
const createTxStep = document.getElementById('createTxStep')
const confirmTxStep = document.getElementById('confirmTxStep')
const processingTxStep = document.getElementById('processingTxStep')
const successTxStep = document.getElementById('successTxStep')
let currentTransactionName = null
let allNotes = []
let selectedNotes = new Set()

// Sorting state
let sortBy = 'block_height' // 'block_height' or 'assets'
let sortOrder = 'desc' // 'asc' or 'desc'

// Current view state
let currentView = 'notes' // 'notes' or 'history'

// Convert Nick to Nock
function nickToNock(nick) {
  return (nick / 65536).toFixed(4)
}

// Switch between views
function switchView(view) {
  currentView = view
  
  if (view === 'notes') {
    notesViewTab.classList.add('tab-active')
    historyViewTab.classList.remove('tab-active')
    
    notesView.classList.remove('hidden')
    historyView.classList.add('hidden')
  } else if (view === 'history') {
    historyViewTab.classList.add('tab-active')
    notesViewTab.classList.remove('tab-active')
    
    notesView.classList.add('hidden')
    historyView.classList.remove('hidden')
    
    // Load history when switching to history view
    loadTransactionHistory()
  }
}

// Format date
function formatDate(isoString) {
  if (!isoString) return 'N/A'
  const date = new Date(isoString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Get status badge color
function getStatusBadge(status) {
  const colors = {
    'created': 'status-created',
    'signed': 'status-signed',
    'sent': 'status-sent'
  }
  return colors[status] || 'bg-gray-100 text-gray-800 border border-gray-200'
}

// Load transaction history
async function loadTransactionHistory() {
  try {
    historyList.innerHTML = '<div class="text-center text-slate-500 py-12">Loading history...</div>'
    
    const response = await axios.get(`${API_BASE}/api/transaction-history`)
    
    if (response.data.success) {
      const transactions = response.data.transactions
      
      if (transactions.length === 0) {
        historyList.innerHTML = `
          <div class="text-center text-slate-500 py-16">
            <div class="text-6xl mb-4 opacity-50">📜</div>
            <p class="text-xl mb-2">No transactions yet</p>
            <p class="text-sm">Your transaction history will appear here</p>
          </div>
        `
        return
      }
      
      // Sort by created_at descending (most recent first)
      transactions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      
      historyList.innerHTML = ''
      transactions.forEach((tx, index) => {
        const txItem = createHistoryItem(tx, index)
        historyList.appendChild(txItem)
      })
    } else {
      throw new Error(response.data.error || 'Failed to load history')
    }
  } catch (error) {
    historyList.innerHTML = `
      <div class="text-center text-red-500 py-12">
        <div class="text-4xl mb-4">⚠️</div>
        <p class="text-lg mb-2">Error loading history</p>
        <p class="text-sm text-slate-600">${error.message}</p>
      </div>
    `
  }
}

// Create history item
function createHistoryItem(tx, index) {
  const txDiv = document.createElement('div')
  txDiv.className = 'border-b border-slate-100 last:border-b-0 history-item'
  
  const statusBadge = getStatusBadge(tx.status)
  
  // Main header
  const header = document.createElement('div')
  header.className = 'flex justify-between items-center px-6 py-4 hover:bg-slate-50 transition-colors cursor-pointer'
  header.onclick = () => toggleHistoryDetails(index)
  
  header.innerHTML = `
    <div class="flex-1">
      <div class="flex items-center gap-3 mb-3">
        <span class="px-3 py-1 rounded-full text-xs font-semibold ${statusBadge}">
          ${tx.status.toUpperCase()}
        </span>
        <span class="text-xs text-slate-500">${formatDate(tx.created_at)}</span>
      </div>
      <div class="flex items-center gap-3 mb-2">
        <div class="text-sm text-slate-600 font-mono truncate max-w-xs">
          Hash: ${tx.hash}
        </div>
        <a href="https://nockblocks.com/tx/${tx.hash}" 
           target="_blank" 
           rel="noopener noreferrer"
           onclick="event.stopPropagation()"
           class="explorer-link"
           title="View on NockBlocks Explorer">
          🔗 Explorer
        </a>
      </div>
    </div>
    <div class="flex items-center gap-4 ml-4">
      <div class="text-right">
        <div class="mb-1">
          <span class="text-2xl font-bold text-green-600">${tx.amount_nock}</span>
          <span class="text-sm text-slate-500 ml-1">nock</span>
        </div>
        <div>
          <span class="text-sm text-slate-600">${tx.amount_nick.toLocaleString()}</span>
          <span class="text-xs text-slate-500 ml-1">nick</span>
        </div>
      </div>
      <svg id="history-arrow-${index}" class="w-5 h-5 text-slate-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </div>
  `
  
  // Details section (hidden by default)
  const details = document.createElement('div')
  details.id = `history-details-${index}`
  details.className = 'hidden px-6 py-4 bg-slate-50 border-t border-slate-200'
  details.innerHTML = `
    <div class="space-y-4 text-sm">
      <div>
        <span class="text-slate-600 font-medium">Transaction Hash:</span>
        <div class="flex items-center gap-3 mt-2">
          <p class="text-slate-800 font-mono break-all bg-white p-3 rounded-lg border flex-1 text-xs">${tx.hash}</p>
          <a href="https://nockblocks.com/tx/${tx.hash}" 
             target="_blank" 
             rel="noopener noreferrer"
             class="explorer-link whitespace-nowrap"
             title="View on NockBlocks Explorer">
            🔗 View on Explorer
          </a>
        </div>
      </div>
      <div>
        <span class="text-slate-600 font-medium">Recipient:</span>
        <p class="text-slate-800 font-mono break-all mt-2 bg-white p-3 rounded-lg border text-xs">${tx.recipient}</p>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white p-3 rounded-lg border">
          <span class="text-slate-600 font-medium text-xs">Amount:</span>
          <p class="text-slate-800 mt-1 font-semibold">
            ${tx.amount_nock} nock<br>
            <span class="text-sm text-slate-600 font-normal">${tx.amount_nick.toLocaleString()} nick</span>
          </p>
        </div>
        <div class="bg-white p-3 rounded-lg border">
          <span class="text-slate-600 font-medium text-xs">Fee:</span>
          <p class="text-slate-800 mt-1 font-semibold">
            ${nickToNock(tx.fee_nick)} nock<br>
            <span class="text-sm text-slate-600 font-normal">${tx.fee_nick.toLocaleString()} nick</span>
          </p>
        </div>
      </div>
      <div class="bg-white p-3 rounded-lg border">
        <span class="text-slate-600 font-medium text-xs">Notes Used:</span>
        <span class="text-slate-800 ml-2 font-semibold">${tx.notes_used}</span>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white p-3 rounded-lg border">
          <span class="text-slate-600 font-medium text-xs">Created:</span>
          <p class="text-slate-800 text-xs mt-1">${formatDate(tx.created_at)}</p>
        </div>
        <div class="bg-white p-3 rounded-lg border">
          <span class="text-slate-600 font-medium text-xs">Last Updated:</span>
          <p class="text-slate-800 text-xs mt-1">${formatDate(tx.updated_at)}</p>
        </div>
      </div>
      ${tx.sent_at ? `
        <div class="bg-green-50 p-3 rounded-lg border border-green-200">
          <span class="text-green-700 font-medium text-xs">Sent:</span>
          <p class="text-green-800 text-xs mt-1">${formatDate(tx.sent_at)}</p>
        </div>
      ` : ''}
    </div>
  `
  
  txDiv.appendChild(header)
  txDiv.appendChild(details)
  
  return txDiv
}

// Toggle history details
function toggleHistoryDetails(index) {
  const details = document.getElementById(`history-details-${index}`)
  const arrow = document.getElementById(`history-arrow-${index}`)
  
  if (details.classList.contains('hidden')) {
    details.classList.remove('hidden')
    arrow.style.transform = 'rotate(180deg)'
  } else {
    details.classList.add('hidden')
    arrow.style.transform = 'rotate(0deg)'
  }
}

// Load active address
async function loadActiveAddress() {
  try {
    console.log('Loading active address...')
    const response = await axios.get(`${API_BASE}/api/active-address`)
    
    if (response.data.success) {
      const activeAddressElem = document.getElementById('activeAddress')
      const activeAddressVersionElem = document.getElementById('activeAddressVersion')
      
      if (activeAddressElem) {
        activeAddressElem.textContent = response.data.active_address
      }
      
      if (activeAddressVersionElem) {
        activeAddressVersionElem.textContent = `v${response.data.version}`
      }
      console.log('Active address loaded successfully')
    }
  } catch (error) {
    console.error('Error loading active address:', error)
    const activeAddressElem = document.getElementById('activeAddress')
    if (activeAddressElem) {
      activeAddressElem.textContent = 'Error loading address'
      activeAddressElem.classList.add('text-red-600')
    }
  }
}

// Set active address
async function setActiveAddress(address, version) {
  console.log('setActiveAddress called with:', address, 'version:', version)
  if (!confirm(`Are you sure you want to set this address as active?\n\n${address}`)) {
    return
  }
  
  try {
    // Show loading state
    const toast = showLoadingToast('Setting active address...')
    
    const response = await axios.post(`${API_BASE}/api/set-active-address`, {
      address: address
    })
    
    console.log('Set active address response:', response.data)
    
    // Remove loading toast
    if (document.body.contains(toast)) {
      document.body.removeChild(toast)
    }
    
    if (response.data.success) {
      // Close the addresses modal
      closeAllAddressesModal()
      
      // Show success message
      showSuccessToast('Address changed! Wallet synchronized.')
      
      // IMPORTANT: Clear all notes and selected notes FIRST
      allNotes = []
      selectedNotes.clear()
      
      // The backend already returns the balance data, so we use it directly
      const balanceData = response.data.balance
      
      // Update the UI with the data from the response
      if (balanceData && !balanceData.error) {
        // Update notes count
        notesCount.textContent = balanceData.notes_count
        
        // Display total in Nock and Nick
        const totalNock = nickToNock(balanceData.total_assets)
        totalAssets.innerHTML = `
          <span class="text-4xl font-bold">${totalNock}</span>
          <span class="text-lg text-blue-100 ml-2">nock</span>
          <br>
          <span class="text-lg text-blue-200">${balanceData.total_assets.toLocaleString()}</span>
          <span class="text-sm text-blue-200 ml-1">nick</span>
        `
        
        // Store all notes (now that allNotes is cleared, we have a fresh start)
        allNotes = balanceData.notes || []
        
        console.log('New notes loaded:', allNotes.length, 'notes for address:', address)
        
        // Render notes with current sorting
        renderNotes()
        
        updateSendSelectedButton()
        
        // Show balance content, hide error
        errorDisplay.classList.add('hidden')
        balanceContent.classList.remove('hidden')
      }
      
      // Update active address display using the version passed as parameter
      const activeAddressElem = document.getElementById('activeAddress')
      const activeAddressVersionElem = document.getElementById('activeAddressVersion')
      
      if (activeAddressElem && response.data.active_address) {
        activeAddressElem.textContent = response.data.active_address
      }
      
      if (activeAddressVersionElem && version !== null && version !== undefined) {
        activeAddressVersionElem.textContent = `v${version}`
      }
      
      // If we're on history view, reload it
      if (currentView === 'history') {
        await loadTransactionHistory()
      }
    } else {
      throw new Error(response.data.error || 'Failed to set active address')
    }
  } catch (error) {
    console.error('Error setting active address:', error)
    showErrorToast('Error: ' + (error.response?.data?.error || error.message))
  }
}

// Load all master addresses
async function loadAllMasterAddresses() {
  console.log('loadAllMasterAddresses called')
  try {
    addressesList.innerHTML = `
      <div class="text-center text-slate-500 py-8">
        <div class="loading-spinner-dark mx-auto mb-4"></div>
        <p>Loading addresses...</p>
      </div>
    `
    
    console.log('Fetching master addresses from API...')
    const response = await axios.get(`${API_BASE}/api/list-master-addresses`)
    console.log('Master addresses response:', response.data)
    
    if (response.data.success && response.data.addresses.length > 0) {
      addressesList.innerHTML = ''
      
      response.data.addresses.forEach((addr, index) => {
        const addressCard = document.createElement('div')
        addressCard.className = `bg-white rounded-lg border-2 p-4 transition-all duration-200 ${
          addr.is_active ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'
        }`
        
        // Escape single quotes in address for onclick handler
        const escapedAddress = addr.address.replace(/'/g, "\\'")
        
        addressCard.innerHTML = `
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-semibold text-slate-600 uppercase">Address ${index + 1}</span>
                <span class="px-2 py-0.5 bg-slate-100 text-slate-700 text-xs font-semibold rounded-full">v${addr.version}</span>
                ${addr.is_active ? '<span class="px-2 py-0.5 bg-blue-500 text-white text-xs font-semibold rounded-full">Active</span>' : ''}
              </div>
              <code class="text-sm font-mono text-slate-800 break-all block mb-3">${addr.address}</code>
              <div class="flex gap-2">
                <button 
                  onclick="window.copyToClipboard('${escapedAddress}')" 
                  class="btn-secondary text-xs px-3 py-1.5"
                  title="Copy to clipboard">
                  📋 Copy
                </button>
                ${!addr.is_active ? `
                  <button 
                    onclick="window.setActiveAddress('${escapedAddress}', ${addr.version})" 
                    class="btn-primary btn-blue text-xs px-3 py-1.5"
                    title="Set as active address">
                    ⭐ Set Active
                  </button>
                ` : ''}
              </div>
            </div>
          </div>
        `
        
        addressesList.appendChild(addressCard)
      })
      console.log('Addresses rendered successfully')
    } else {
      addressesList.innerHTML = `
        <div class="text-center text-slate-500 py-8">
          <div class="text-4xl mb-4 opacity-50">📭</div>
          <p class="text-lg">No addresses found</p>
        </div>
      `
    }
  } catch (error) {
    console.error('Error loading master addresses:', error)
    addressesList.innerHTML = `
      <div class="text-center text-red-500 py-8">
        <div class="text-4xl mb-4">⚠️</div>
        <p class="text-lg mb-2">Error loading addresses</p>
        <p class="text-sm text-slate-600">${error.message}</p>
      </div>
    `
  }
}

// Show all addresses modal
function showAllAddressesModal() {
  console.log('showAllAddressesModal called')
  if (!allAddressesModal) {
    console.error('allAddressesModal element not found!')
    return
  }
  allAddressesModal.classList.remove('hidden')
  loadAllMasterAddresses()
}

// Close all addresses modal
function closeAllAddressesModal() {
  console.log('closeAllAddressesModal called')
  if (!allAddressesModal) {
    console.error('allAddressesModal element not found!')
    return
  }
  allAddressesModal.classList.add('hidden')
}

// Toast notification helpers
function showLoadingToast(message) {
  const toast = document.createElement('div')
  toast.className = 'fixed top-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg z-[10000] animate-slideIn'
  toast.innerHTML = `
    <div class="flex items-center gap-3">
      <div class="loading-spinner-small"></div>
      <span class="font-semibold">${message}</span>
    </div>
  `
  document.body.appendChild(toast)
  return toast
}

function showSuccessToast(message) {
  const toast = document.createElement('div')
  toast.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-[10000] animate-slideIn'
  toast.innerHTML = `
    <div class="flex items-center gap-2">
      <span class="text-xl">✅</span>
      <span class="font-semibold">${message}</span>
    </div>
  `
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-out'
    setTimeout(() => {
      if (document.body.contains(toast)) {
        document.body.removeChild(toast)
      }
    }, 300)
  }, 3000)
}

function showErrorToast(message) {
  const toast = document.createElement('div')
  toast.className = 'fixed top-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-[10000] animate-slideIn'
  toast.innerHTML = `
    <div class="flex items-center gap-2">
      <span class="text-xl">⚠️</span>
      <span class="font-semibold">${message}</span>
    </div>
  `
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-out'
    setTimeout(() => {
      if (document.body.contains(toast)) {
        document.body.removeChild(toast)
      }
    }, 300)
  }, 5000)
}

// Copy to clipboard function
function copyToClipboard(text) {
  console.log('Copying to clipboard:', text)
  navigator.clipboard.writeText(text).then(() => {
    showSuccessToast('Address copied to clipboard!')
  }).catch(err => {
    console.error('Failed to copy:', err)
    showErrorToast('Failed to copy address to clipboard')
  })
}

// Update Balance Function - Modified to also load active address
async function updateBalance() {
  try {
    // Show loading animation
    loadingDisplay.classList.remove('hidden')
    balanceDisplay.classList.add('hidden')
    
    const response = await axios.get(`${API_BASE}/api/balance`)
    const data = response.data
    
    // Hide loading animation
    loadingDisplay.classList.add('hidden')
    balanceDisplay.classList.remove('hidden')
    
    if (data.error) {
      document.getElementById('errorMessage').textContent = data.error
      errorDisplay.classList.remove('hidden')
      balanceContent.classList.add('hidden')
    } else {
      errorDisplay.classList.add('hidden')
      balanceContent.classList.remove('hidden')
      
      notesCount.textContent = data.notes_count
      
      // Display total in Nock and Nick
      const totalNock = nickToNock(data.total_assets)
      totalAssets.innerHTML = `
        <span class="text-4xl font-bold">${totalNock}</span>
        <span class="text-lg text-blue-100 ml-2">nock</span>
        <br>
        <span class="text-lg text-blue-200">${data.total_assets.toLocaleString()}</span>
        <span class="text-sm text-blue-200 ml-1">nick</span>
      `
      
      // IMPORTANT: Clear before storing new notes
      allNotes = []
      selectedNotes.clear()
      
      // Store all notes
      allNotes = data.notes || []
      
      console.log('Balance updated:', allNotes.length, 'notes loaded')
      
      // Render notes with current sorting
      renderNotes()
      
      updateSendSelectedButton()
      
      // Load active address
      loadActiveAddress()
    }
  } catch (error) {
    // Hide loading animation on error
    loadingDisplay.classList.add('hidden')
    alert('Error: ' + error.message)
  }
}

// Create a note item with expandable details
function createNoteItem(note, index) {
  const noteDiv = document.createElement('div')
  noteDiv.className = 'border-b border-slate-100 last:border-b-0 note-item'
  
  const nockAmount = nickToNock(note.value)
  
  // Main clickable header
  const header = document.createElement('div')
  header.className = 'flex justify-between items-center px-6 py-4 hover:bg-slate-50 transition-colors'
  
  header.innerHTML = `
    <div class="flex items-center gap-4 flex-1">
      <input type="checkbox" 
             id="checkbox-${index}" 
             class="note-checkbox"
             onchange="window.handleNoteCheckboxChange(${index}, this.checked)">
      <div class="flex-1 cursor-pointer" onclick="window.toggleNoteDetails(${index})">
        <span class="text-sm text-slate-600 font-mono break-all">${truncateString(note.name, 50)}</span>
      </div>
    </div>
    <div class="flex items-center gap-6 ml-4 cursor-pointer" onclick="window.toggleNoteDetails(${index})">
      <span class="text-sm text-blue-600 font-medium bg-blue-50 px-3 py-1 rounded-full">Block: ${note.block_height}</span>
      <div class="text-right">
        <div class="mb-1">
          <span class="text-2xl font-bold text-green-600">${nockAmount}</span>
          <span class="text-sm text-slate-500 ml-1">nock</span>
        </div>
        <div>
          <span class="text-sm text-slate-600">${note.value.toLocaleString()}</span>
          <span class="text-xs text-slate-500 ml-1">nick</span>
        </div>
      </div>
      <svg id="arrow-${index}" class="w-5 h-5 text-slate-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </div>
  `
  
  // Details section (hidden by default)
  const details = document.createElement('div')
  details.id = `details-${index}`
  details.className = 'hidden px-6 py-4 bg-slate-50 border-t border-slate-200'
  details.innerHTML = `
    <div class="space-y-4 text-sm">
      <div>
        <span class="text-slate-600 font-medium">Full Name:</span>
        <p class="text-slate-800 font-mono break-all mt-2 bg-white p-3 rounded-lg border text-xs">${note.name}</p>
      </div>
      <div>
        <span class="text-slate-600 font-medium">Source:</span>
        <p class="text-slate-800 font-mono break-all mt-2 bg-white p-3 rounded-lg border text-xs">${note.source}</p>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white p-3 rounded-lg border">
          <span class="text-slate-600 font-medium text-xs">Block Height:</span>
          <span class="text-slate-800 ml-2 font-semibold">${note.block_height}</span>
        </div>
        <div class="bg-white p-3 rounded-lg border">
          <span class="text-slate-600 font-medium text-xs">Value:</span>
          <p class="text-slate-800 mt-1 font-semibold">
            ${nockAmount} nock<br>
            <span class="text-sm text-slate-600 font-normal">${note.value.toLocaleString()} nick</span>
          </p>
        </div>
      </div>
      <div>
        <span class="text-slate-600 font-medium">Signer:</span>
        <p class="text-slate-800 font-mono text-xs break-all mt-2 bg-white p-3 rounded-lg border">${note.signer}</p>
      </div>
    </div>
  `
  
  noteDiv.appendChild(header)
  noteDiv.appendChild(details)
  
  return noteDiv
}

// Sort notes based on current sort settings
function sortNotes(notes) {
  const sorted = [...notes].sort((a, b) => {
    let comparison = 0
    
    if (sortBy === 'block_height') {
      comparison = a.block_height - b.block_height
    } else if (sortBy === 'value') {
      comparison = a.value - b.value
    }
    
    return sortOrder === 'asc' ? comparison : -comparison
  })
  
  return sorted
}

// Render notes list
function renderNotes() {
  notesList.innerHTML = ''
  
  // Add sort controls header
  const sortHeader = document.createElement('div')
  sortHeader.className = 'bg-slate-50 border-b border-slate-200 p-4 flex items-center justify-between'
  sortHeader.innerHTML = `
    <div class="text-sm text-slate-700 font-semibold">Sort by:</div>
    <div class="flex gap-3">
      <button id="sortByBlock" class="sort-btn ${sortBy === 'block_height' ? 'sort-active' : ''}">
        <span>Block Height</span>
        <svg class="w-4 h-4 ${sortBy === 'block_height' && sortOrder === 'asc' ? 'rotate-180' : ''} transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>
      <button id="sortByAmount" class="sort-btn ${sortBy === 'value' ? 'sort-active' : ''}">
        <span>Amount</span>
        <svg class="w-4 h-4 ${sortBy === 'value' && sortOrder === 'asc' ? 'rotate-180' : ''} transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>
    </div>
  `
  notesList.appendChild(sortHeader)
  
  // Add event listeners to sort buttons
  document.getElementById('sortByBlock').addEventListener('click', () => {
    if (sortBy === 'block_height') {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy = 'block_height'
      sortOrder = 'desc'
    }
    renderNotes()
  })
  
  document.getElementById('sortByAmount').addEventListener('click', () => {
    if (sortBy === 'value') {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy = 'value'
      sortOrder = 'desc'
    }
    renderNotes()
  })
  
  // Sort and render notes
  const sortedNotes = sortNotes(allNotes)
  sortedNotes.forEach((note, originalIndex) => {
    // Find original index in allNotes array
    const index = allNotes.findIndex(n => n.name === note.name)
    const noteItem = createNoteItem(note, index)
    notesList.appendChild(noteItem)
    
    // Restore checkbox state
    const checkbox = document.getElementById(`checkbox-${index}`)
    if (checkbox && selectedNotes.has(index)) {
      checkbox.checked = true
    }
  })
}

// Update Send Selected Button state
function updateSendSelectedButton() {
  sendSelectedBtn.disabled = selectedNotes.size === 0
  if (selectedNotes.size > 0) {
    const totalSelected = Array.from(selectedNotes).reduce((sum, index) => {
      return sum + allNotes[index].value
    }, 0)
    const totalNock = nickToNock(totalSelected)
    sendSelectedBtn.innerHTML = `
      <span class="btn-icon">💸</span>
      <span>Send Selected (${selectedNotes.size} notes - ${totalNock} nock)</span>
    `
  } else {
    sendSelectedBtn.innerHTML = `
      <span class="btn-icon">💸</span>
      <span>Send Selected</span>
    `
  }
}

// Show Send Transaction Modal
function showSendTxModal(useSelectedNotes = false) {
  console.log('showSendTxModal called, useSelectedNotes:', useSelectedNotes)
  sendTxModal.classList.remove('hidden')
  resetTxModal()
  
  // Store if we're using selected notes
  window.useSelectedNotesForTx = useSelectedNotes
  
  if (useSelectedNotes && selectedNotes.size > 0) {
    // Calculate total amount from selected notes minus fee
    const totalNick = Array.from(selectedNotes).reduce((sum, index) => {
      return sum + allNotes[index].value
    }, 0)
    
    const feeNick = parseInt(document.getElementById('feeInput').value || 10)
    const availableNick = totalNick - feeNick
    const availableNock = nickToNock(availableNick)
    
    // Pre-fill and disable amount field
    const amountInput = document.getElementById('amountInput')
    amountInput.value = availableNock
    amountInput.readOnly = true
    amountInput.classList.add('bg-slate-100', 'cursor-not-allowed')
    
    // Add info text
    const amountLabel = amountInput.previousElementSibling
    amountLabel.innerHTML = `Amount (Nock) - <span class="text-amber-600 font-medium">Total from ${selectedNotes.size} selected notes</span>`
  }
}

// Reset Transaction Modal to initial state
function resetTxModal() {
  createTxStep.classList.remove('hidden')
  confirmTxStep.classList.add('hidden')
  processingTxStep.classList.add('hidden')
  successTxStep.classList.add('hidden')
  
  document.getElementById('recipientInput').value = ''
  
  const amountInput = document.getElementById('amountInput')
  amountInput.value = ''
  amountInput.readOnly = false
  amountInput.classList.remove('bg-slate-100', 'cursor-not-allowed')
  
  // Reset label
  const amountLabel = amountInput.previousElementSibling
  amountLabel.textContent = 'Amount (Nock)'
  
  document.getElementById('feeInput').value = '10'
  currentTransactionName = null
}

// Close Send Transaction Modal
function closeSendTxModal() {
  console.log('closeSendTxModal called')
  sendTxModal.classList.add('hidden')
  resetTxModal()
}

// Create Transaction
async function createTransaction() {
  const recipient = document.getElementById('recipientInput').value.trim()
  const amount = document.getElementById('amountInput').value
  const fee = document.getElementById('feeInput').value

  if (!recipient || !amount) {
    alert('Please fill in all fields')
    return
  }

  try {
    createTxStep.classList.add('hidden')
    processingTxStep.classList.remove('hidden')

    // Prepare selected notes if using manual selection
    let selectedNoteNames = null
    let useAllFunds = false
    
    if (window.useSelectedNotesForTx && selectedNotes.size > 0) {
      selectedNoteNames = Array.from(selectedNotes).map(index => allNotes[index].name)
      useAllFunds = true // Send all funds from selected notes
    }

    const response = await axios.post(`${API_BASE}/api/create-transaction`, {
      recipient,
      amount_nock: parseFloat(amount),
      fee: parseInt(fee),
      selected_notes: selectedNoteNames,
      use_all_funds: useAllFunds
    })

    if (response.data.success) {
      currentTransactionName = response.data.transaction_name
      document.getElementById('txDetails').textContent = response.data.output
      
      processingTxStep.classList.add('hidden')
      confirmTxStep.classList.remove('hidden')
    } else {
      throw new Error(response.data.error || 'Failed to create transaction')
    }
  } catch (error) {
    processingTxStep.classList.add('hidden')
    createTxStep.classList.remove('hidden')
    alert('Error: ' + (error.response?.data?.error || error.message))
  }
}

// Sign and Send Transaction
async function signAndSendTransaction() {
  if (!currentTransactionName) {
    alert('No transaction to send')
    return
  }

  try {
    confirmTxStep.classList.add('hidden')
    processingTxStep.classList.remove('hidden')

    // Sign transaction
    await axios.post(`${API_BASE}/api/sign-transaction`, {
      transaction_name: currentTransactionName
    })

    // Send transaction
    const response = await axios.post(`${API_BASE}/api/send-transaction`, {
      transaction_name: currentTransactionName
    })

    if (response.data.success) {
      processingTxStep.classList.add('hidden')
      successTxStep.classList.remove('hidden')
      
      // Clear selected notes
      selectedNotes.clear()
      
      // Refresh balance and history after successful transaction
      setTimeout(() => {
        updateBalance()
        if (currentView === 'history') {
          loadTransactionHistory()
        }
      }, 1000)
    } else {
      throw new Error(response.data.error || 'Failed to send transaction')
    }
  } catch (error) {
    processingTxStep.classList.add('hidden')
    confirmTxStep.classList.remove('hidden')
    alert('Error: ' + (error.response?.data?.error || error.message))
  }
}

// Export Keys Function
function exportKeys() {
  window.location.href = `${API_BASE}/api/export-keys`
}

// Import Keys from File Function
async function importKeysFromFile(input) {
  const file = input.files[0]
  console.log('Import keys from file called, file:', file)
  if (!file) {
    console.log('No file selected')
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  console.log('API_BASE:', API_BASE)
  console.log('Sending request to:', `${API_BASE}/api/import-keys`)

  try {
    const response = await axios.post(`${API_BASE}/api/import-keys`, formData)
    
    console.log('Response:', response.data)
    
    if (response.data.success) {
      alert('✅ ' + response.data.message + '\n\n⏳ Synchronizing wallet, please wait...')
      
      // Wait for wallet sync
      console.log('Waiting for wallet sync...')
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // Update balance
      console.log('Updating balance...')
      await updateBalance()
      
      alert('✅ Wallet synchronized! Balance updated.')
    } else {
      alert('❌ ' + (response.data.error || 'Unknown error'))
    }
  } catch (error) {
    console.error('Import error:', error)
    console.error('Error response:', error.response?.data)
    alert('❌ Error: ' + (error.response?.data?.error || error.message))
  }

  // Reset input
  input.value = ''
}

// Import Keys from Seedphrase Function
async function importKeysFromSeedphrase() {
  const seedphrase = document.getElementById('seedphraseInput').value.trim()
  const version = document.getElementById('seedphraseVersion').value
  
  if (!seedphrase) {
    alert('❌ Please enter your seed phrase')
    return
  }
  
  if (!version) {
    alert('❌ Please select a version (0 or 1)')
    return
  }
  
  console.log('Importing from seedphrase, version:', version)
  
  // Get the button element
  const importBtn = event.target
  const originalHTML = importBtn.innerHTML
  
  // Disable button and show loading state
  importBtn.disabled = true
  importBtn.innerHTML = `
    <div class="flex items-center justify-center gap-2">
      <div class="loading-spinner-small"></div>
      <span>Importing seed phrase...</span>
    </div>
  `
  
  try {
    const response = await axios.post(`${API_BASE}/api/import-seedphrase`, {
      seedphrase: seedphrase,
      version: parseInt(version)
    })
    
    console.log('Response:', response.data)
    
    if (response.data.success) {
      // Clear seedphrase input for security
      document.getElementById('seedphraseInput').value = ''
      
      // Show success message with loading for sync
      importBtn.innerHTML = `
        <div class="flex items-center justify-center gap-2">
          <div class="loading-spinner-small"></div>
          <span>Synchronizing wallet...</span>
        </div>
      `
      
      alert('✅ ' + response.data.message + '\n\n⏳ Synchronizing wallet, please wait...')
      
      // Wait for wallet sync
      console.log('Waiting for wallet sync...')
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // Update balance
      console.log('Updating balance...')
      await updateBalance()
      
      alert('✅ Wallet synchronized! Balance updated.')
      
      // Restore button
      importBtn.disabled = false
      importBtn.innerHTML = originalHTML
    } else {
      // Restore button
      importBtn.disabled = false
      importBtn.innerHTML = originalHTML
      alert('❌ ' + (response.data.error || 'Unknown error'))
    }
  } catch (error) {
    console.error('Import seedphrase error:', error)
    console.error('Error response:', error.response?.data)
    
    // Restore button
    importBtn.disabled = false
    importBtn.innerHTML = originalHTML
    alert('❌ Error: ' + (error.response?.data?.error || error.message))
  }
}

// Show Seedphrase Function
async function showSeedphrase() {
  if (!confirm('⚠️ Warning: Your seed phrase will be displayed on screen.\n\nMake sure nobody is watching and you are in a secure environment.\n\nContinue?')) {
    return
  }
  
  try {
    const response = await axios.get(`${API_BASE}/api/show-seedphrase`)
    
    console.log('Seedphrase retrieved')
    
    if (response.data.success) {
      // Create a modal to display the seedphrase
      const modal = document.createElement('div')
      modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
      `
      
      const content = document.createElement('div')
      content.style.cssText = `
        background: #1a1a1a;
        padding: 2rem;
        border-radius: 8px;
        max-width: 600px;
        width: 90%;
        border: 2px solid #ff6b35;
      `
      
      content.innerHTML = `
        <h2 style="color: #ff6b35; margin-bottom: 1rem;">🔑 Your Seed Phrase</h2>
        <div style="background: #2a2a2a; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; word-break: break-word; font-family: monospace; color: #fff;">
          ${response.data.seedphrase}
        </div>
        <div style="color: #ffa500; margin-bottom: 1rem; font-size: 0.9rem;">
          ⚠️ <strong>IMPORTANT:</strong> Write this down and store it safely. Never share it with anyone!
        </div>
        <button id="closeSeedphraseModal" style="
          background: #ff6b35;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 1rem;
          width: 100%;
        ">Close</button>
      `
      
      modal.appendChild(content)
      document.body.appendChild(modal)
      
      // Close modal handler
      document.getElementById('closeSeedphraseModal').addEventListener('click', () => {
        document.body.removeChild(modal)
      })
      
      // Close on outside click
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          document.body.removeChild(modal)
        }
      })
    } else {
      alert('❌ ' + (response.data.error || 'Unknown error'))
    }
  } catch (error) {
    console.error('Show seedphrase error:', error)
    console.error('Error response:', error.response?.data)
    alert('❌ Error: ' + (error.response?.data?.error || error.message))
  }
}

// Add missing utility function
function truncateString(str, maxLength) {
  if (str.length <= maxLength) return str
  return str.substring(0, maxLength) + '...'
}

// Toggle note details
function toggleNoteDetails(index) {
  const details = document.getElementById(`details-${index}`)
  const arrow = document.getElementById(`arrow-${index}`)
  
  if (details.classList.contains('hidden')) {
    details.classList.remove('hidden')
    arrow.style.transform = 'rotate(180deg)'
  } else {
    details.classList.add('hidden')
    arrow.style.transform = 'rotate(0deg)'
  }
}

// Handle note checkbox change
function handleNoteCheckboxChange(index, checked) {
  if (checked) {
    selectedNotes.add(index)
  } else {
    selectedNotes.delete(index)
  }
  updateSendSelectedButton()
}

// Make functions globally accessible for onclick handlers
window.toggleNoteDetails = toggleNoteDetails
window.handleNoteCheckboxChange = handleNoteCheckboxChange
window.switchView = switchView
window.importKeysFromFile = importKeysFromFile
window.importKeysFromSeedphrase = importKeysFromSeedphrase
window.showSeedphrase = showSeedphrase
window.copyToClipboard = copyToClipboard
window.setActiveAddress = setActiveAddress

// Event handlers functions
function handleSendTxBtnClick() {
  console.log('Send transaction button clicked')
  showSendTxModal(false)
}

function handleSendSelectedBtnClick() {
  console.log('Send selected button clicked')  
  showSendTxModal(true)
}

function handleCloseSendTxModal() {
  console.log('Close modal button clicked')
  closeSendTxModal()
}

function handleShowAllAddressesClick() {
  console.log('Show all addresses button clicked')
  showAllAddressesModal()
}

function handleCloseAllAddressesModal() {
  console.log('Close addresses modal button clicked')
  closeAllAddressesModal()
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM Content Loaded')
  
  // Make sure modals start hidden
  if (sendTxModal) {
    sendTxModal.classList.add('hidden')
  }
  if (allAddressesModal) {
    allAddressesModal.classList.add('hidden')
  }
  
  // Attach event listeners
  const updateBalanceBtn = document.getElementById('updateBalanceBtn')
  if (updateBalanceBtn) {
    updateBalanceBtn.addEventListener('click', updateBalance)
  }
  
  const sendTxBtn = document.getElementById('sendTxBtn')
  if (sendTxBtn) {
    sendTxBtn.addEventListener('click', handleSendTxBtnClick)
  }
  
  if (sendSelectedBtn) {
    sendSelectedBtn.addEventListener('click', handleSendSelectedBtnClick)
  }
  
  const exportKeysBtn = document.getElementById('exportKeysBtn')
  if (exportKeysBtn) {
    exportKeysBtn.addEventListener('click', exportKeys)
  }

  // Check if import file input exists before adding listener
  const importFileInput = document.getElementById('importFile')
  if (importFileInput) {
    importFileInput.addEventListener('change', (e) => importKeysFromFile(e.target))
  }

  // View tabs event listeners
  if (notesViewTab) {
    notesViewTab.addEventListener('click', () => switchView('notes'))
  }
  if (historyViewTab) {
    historyViewTab.addEventListener('click', () => switchView('history'))
  }

  // Transaction modal event listeners
  const closeSendTxModalBtn = document.getElementById('closeSendTxModal')
  if (closeSendTxModalBtn) {
    closeSendTxModalBtn.addEventListener('click', handleCloseSendTxModal)
  }
  
  const closeTxSuccessBtn = document.getElementById('closeTxSuccessBtn')  
  if (closeTxSuccessBtn) {
    closeTxSuccessBtn.addEventListener('click', handleCloseSendTxModal)
  }
  
  const createTxBtn = document.getElementById('createTxBtn')
  if (createTxBtn) {
    createTxBtn.addEventListener('click', createTransaction)
  }
  
  const backToCreateBtn = document.getElementById('backToCreateBtn')
  if (backToCreateBtn) {
    backToCreateBtn.addEventListener('click', () => {
      confirmTxStep.classList.add('hidden')
      createTxStep.classList.remove('hidden')
    })
  }
  
  const confirmTxBtn = document.getElementById('confirmTxBtn')
  if (confirmTxBtn) {
    confirmTxBtn.addEventListener('click', signAndSendTransaction)
  }

  // Close modal when clicking outside
  if (sendTxModal) {
    sendTxModal.addEventListener('click', (e) => {
      if (e.target === sendTxModal) {
        console.log('Clicked outside modal, closing')
        closeSendTxModal()
      }
    })
  }
  
  // All Addresses Modal event listeners
  const showAllAddressesBtn = document.getElementById('showAllAddressesBtn')
  if (showAllAddressesBtn) {
    showAllAddressesBtn.addEventListener('click', handleShowAllAddressesClick)
  }
  
  const closeAllAddressesModalBtn = document.getElementById('closeAllAddressesModal')
  if (closeAllAddressesModalBtn) {
    closeAllAddressesModalBtn.addEventListener('click', handleCloseAllAddressesModal)
  }
  
  const closeAllAddressesModalBtn2 = document.getElementById('closeAllAddressesModalBtn')
  if (closeAllAddressesModalBtn2) {
    closeAllAddressesModalBtn2.addEventListener('click', handleCloseAllAddressesModal)
  }
  
  // Close modal when clicking outside
  if (allAddressesModal) {
    allAddressesModal.addEventListener('click', (e) => {
      if (e.target === allAddressesModal) {
        console.log('Clicked outside addresses modal, closing')
        closeAllAddressesModal()
      }
    })
  }

  // Initialize
  updateBalance()
})
