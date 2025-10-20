import './style.css'
import axios from 'axios'

// Use environment variable or fallback
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5007'

// DOM Elements
const loadingDisplay = document.getElementById('loadingDisplay')
const balanceDisplay = document.getElementById('balanceDisplay')
const errorDisplay = document.getElementById('errorDisplay')
const balanceContent = document.getElementById('balanceContent')
const notesCount = document.getElementById('notesCount')
const totalAssets = document.getElementById('totalAssets')
const notesList = document.getElementById('notesList')
const sendSelectedBtn = document.getElementById('sendSelectedBtn')

// Transaction Modal Elements
const sendTxModal = document.getElementById('sendTxModal')
const createTxStep = document.getElementById('createTxStep')
const confirmTxStep = document.getElementById('confirmTxStep')
const processingTxStep = document.getElementById('processingTxStep')
const successTxStep = document.getElementById('successTxStep')
let currentTransactionName = null
let allNotes = []
let selectedNotes = new Set()

// Convert Nick to Nock
function nickToNock(nick) {
  return (nick / 65536).toFixed(4)
}

// Update Balance Function
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
      errorDisplay.textContent = data.error
      errorDisplay.classList.remove('hidden')
      balanceContent.classList.add('hidden')
    } else {
      errorDisplay.classList.add('hidden')
      balanceContent.classList.remove('hidden')
      
      notesCount.textContent = data.notes_count
      
      // Display total in Nock and Nick
      const totalNock = nickToNock(data.total_assets)
      totalAssets.innerHTML = `
        <span class="text-4xl">${totalNock}</span>
        <span class="text-sm text-gray-400 ml-1">nock</span>
        <br>
        <span class="text-lg text-gray-400">${data.total_assets.toLocaleString()}</span>
        <span class="text-xs text-gray-500 ml-1">nick</span>
      `
      
      // Store all notes
      allNotes = data.notes
      selectedNotes.clear()
      
      // Clear and populate notes list
      notesList.innerHTML = ''
      data.notes.forEach((note, index) => {
        const noteItem = createNoteItem(note, index)
        notesList.appendChild(noteItem)
      })
      
      updateSendSelectedButton()
    }
  } catch (error) {
    // Hide loading animation on error
    loadingDisplay.classList.add('hidden')
    alert('Error: ' + error.message)
  }
}

// Update Send Selected Button state
function updateSendSelectedButton() {
  sendSelectedBtn.disabled = selectedNotes.size === 0
  if (selectedNotes.size > 0) {
    const totalSelected = Array.from(selectedNotes).reduce((sum, index) => {
      return sum + allNotes[index].assets
    }, 0)
    const totalNock = nickToNock(totalSelected)
    sendSelectedBtn.textContent = `💸 Send Selected (${selectedNotes.size} notes - ${totalNock} nock)`
  } else {
    sendSelectedBtn.textContent = '💸 Send Selected'
  }
}

// Handle note checkbox change
function handleNoteCheckbox(index, checked) {
  if (checked) {
    selectedNotes.add(index)
  } else {
    selectedNotes.delete(index)
  }
  updateSendSelectedButton()
}

// Create a note item with expandable details
function createNoteItem(note, index) {
  const noteDiv = document.createElement('div')
  noteDiv.className = 'bg-gray-800 rounded-lg overflow-hidden mb-2'
  
  const nockAmount = nickToNock(note.assets)
  
  // Main clickable header
  const header = document.createElement('div')
  header.className = 'flex justify-between items-center px-4 py-3 hover:bg-gray-700 transition-colors'
  
  header.innerHTML = `
    <div class="flex items-center gap-3 flex-1">
      <input type="checkbox" 
             id="checkbox-${index}" 
             class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-yellow-600 focus:ring-yellow-500 cursor-pointer"
             onchange="window.handleNoteCheckboxChange(${index}, this.checked)">
      <div class="flex-1 cursor-pointer" onclick="window.toggleNoteDetails(${index})">
        <span class="text-sm text-gray-400 font-mono break-all">${truncateString(note.name, 50)}</span>
      </div>
    </div>
    <div class="flex items-center gap-4 ml-4 cursor-pointer" onclick="window.toggleNoteDetails(${index})">
      <span class="text-sm text-blue-400">Block: ${note.block_height}</span>
      <div class="text-right">
        <div>
          <span class="text-2xl font-bold text-green-400">${nockAmount}</span>
          <span class="text-xs text-gray-400 ml-1">nock</span>
        </div>
        <div>
          <span class="text-sm text-gray-400">${note.assets.toLocaleString()}</span>
          <span class="text-xs text-gray-500 ml-1">nick</span>
        </div>
      </div>
      <svg id="arrow-${index}" class="w-5 h-5 text-gray-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </div>
  `
  
  // Details section (hidden by default)
  const details = document.createElement('div')
  details.id = `details-${index}`
  details.className = 'hidden px-4 py-3 bg-gray-900 border-t border-gray-700'
  details.innerHTML = `
    <div class="space-y-2 text-sm">
      <div>
        <span class="text-gray-400">Full Name:</span>
        <p class="text-gray-200 font-mono break-all mt-1">${note.name}</p>
      </div>
      <div>
        <span class="text-gray-400">Source:</span>
        <p class="text-gray-200 font-mono break-all mt-1">${note.source}</p>
      </div>
      <div>
        <span class="text-gray-400">Required Signatures:</span>
        <span class="text-gray-200 ml-2">${note.required_signatures}</span>
      </div>
      <div>
        <span class="text-gray-400">Signers:</span>
        <div class="mt-1 space-y-1">
          ${note.signers.map(signer => `
            <p class="text-gray-200 font-mono text-xs break-all bg-gray-800 p-2 rounded">${signer}</p>
          `).join('')}
        </div>
      </div>
    </div>
  `
  
  noteDiv.appendChild(header)
  noteDiv.appendChild(details)
  
  return noteDiv
}

// Toggle note details visibility
function toggleDetails(index) {
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

// Truncate long strings
function truncateString(str, maxLength) {
  if (str.length <= maxLength) return str
  return str.substring(0, maxLength) + '...'
}

// Show Send Transaction Modal
function showSendTxModal(useSelectedNotes = false) {
  sendTxModal.classList.remove('hidden')
  resetTxModal()
  
  // Store if we're using selected notes
  window.useSelectedNotesForTx = useSelectedNotes
  
  if (useSelectedNotes && selectedNotes.size > 0) {
    // Calculate total amount from selected notes minus fee
    const totalNick = Array.from(selectedNotes).reduce((sum, index) => {
      return sum + allNotes[index].assets
    }, 0)
    
    const feeNick = parseInt(document.getElementById('feeInput').value || 10)
    const availableNick = totalNick - feeNick
    const availableNock = nickToNock(availableNick)
    
    // Pre-fill and disable amount field
    const amountInput = document.getElementById('amountInput')
    amountInput.value = availableNock
    amountInput.readOnly = true
    amountInput.classList.add('bg-gray-600', 'cursor-not-allowed')
    
    // Add info text
    const amountLabel = amountInput.previousElementSibling
    amountLabel.innerHTML = `Amount (Nock) - <span class="text-yellow-400">Total from ${selectedNotes.size} selected notes</span>`
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
  amountInput.classList.remove('bg-gray-600', 'cursor-not-allowed')
  
  // Reset label
  const amountLabel = amountInput.previousElementSibling
  amountLabel.textContent = 'Amount (Nock)'
  
  document.getElementById('feeInput').value = '10'
  currentTransactionName = null
}

// Close Send Transaction Modal
function closeSendTxModal() {
  sendTxModal.classList.add('hidden')
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
      
      // Refresh balance after successful transaction
      setTimeout(() => {
        updateBalance()
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

// Import Keys Function
async function importKeys(input) {
  const file = input.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await axios.post(`${API_BASE}/api/import-keys`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.success) {
      alert('✅ ' + response.data.message)
      updateBalance()
    } else {
      alert('❌ ' + (response.data.error || 'Unknown error'))
    }
  } catch (error) {
    alert('❌ Error: ' + error.message)
  }

  // Reset input
  input.value = ''
}

// Make functions globally accessible for onclick handlers
window.toggleNoteDetails = toggleDetails
window.handleNoteCheckboxChange = handleNoteCheckbox

// Attach event listeners
document.getElementById('updateBalanceBtn').addEventListener('click', updateBalance)
document.getElementById('sendTxBtn').addEventListener('click', () => showSendTxModal(false))
document.getElementById('sendSelectedBtn').addEventListener('click', () => showSendTxModal(true))
document.getElementById('exportKeysBtn').addEventListener('click', exportKeys)
document.getElementById('importFile').addEventListener('change', (e) => importKeys(e.target))

// Transaction modal event listeners
document.getElementById('closeSendTxModal').addEventListener('click', closeSendTxModal)
document.getElementById('closeTxSuccessBtn').addEventListener('click', closeSendTxModal)
document.getElementById('createTxBtn').addEventListener('click', createTransaction)
document.getElementById('backToCreateBtn').addEventListener('click', () => {
  confirmTxStep.classList.add('hidden')
  createTxStep.classList.remove('hidden')
})
document.getElementById('confirmTxBtn').addEventListener('click', signAndSendTransaction)