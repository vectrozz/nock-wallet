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
      
      // Clear and populate notes list
      notesList.innerHTML = ''
      data.notes.forEach((note, index) => {
        const noteItem = createNoteItem(note, index)
        notesList.appendChild(noteItem)
      })
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
  noteDiv.className = 'bg-gray-800 rounded-lg overflow-hidden mb-2'
  
  const nockAmount = nickToNock(note.assets)
  
  // Main clickable header
  const header = document.createElement('div')
  header.className = 'flex justify-between items-center px-4 py-3 cursor-pointer hover:bg-gray-700 transition-colors'
  header.onclick = () => toggleDetails(index)
  
  header.innerHTML = `
    <div class="flex-1">
      <span class="text-sm text-gray-400 font-mono break-all">${truncateString(note.name, 50)}</span>
    </div>
    <div class="flex items-center gap-4 ml-4">
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

// Attach event listeners
document.getElementById('updateBalanceBtn').addEventListener('click', updateBalance)
document.getElementById('exportKeysBtn').addEventListener('click', exportKeys)
document.getElementById('importFile').addEventListener('change', (e) => importKeys(e.target))