import { getBalance, getActiveAddress } from '../api/wallet.js'
import { nickToNock } from '../utils/helpers.js'
import { renderNotes, updateSendSelectedButton } from './notes.js'

// DOM Elements
const loadingDisplay = document.getElementById('loadingDisplay')
const balanceDisplay = document.getElementById('balanceDisplay')
const errorDisplay = document.getElementById('errorDisplay')
const balanceContent = document.getElementById('balanceContent')
const notesCount = document.getElementById('notesCount')
const totalAssets = document.getElementById('totalAssets')
const notesList = document.getElementById('notesList')

// State
export let allNotes = []
export let selectedNotes = new Set()

// Update Balance
export async function updateBalance() {
  try {
    console.log('🔄 Updating balance...')
    
    // Show loading animation
    if (loadingDisplay) loadingDisplay.classList.remove('hidden')
    if (balanceDisplay) balanceDisplay.classList.add('hidden')
    
    // Get balance (no grpcConfig needed - backend reads from config file)
    const data = await getBalance()
    
    console.log('📊 Balance data received:', data)
    
    // Hide loading animation
    if (loadingDisplay) loadingDisplay.classList.add('hidden')
    if (balanceDisplay) balanceDisplay.classList.remove('hidden')
    
    if (data.error) {
      handleBalanceError(data)
    } else {
      handleBalanceSuccess(data)
    }
  } catch (error) {
    console.error('❌ Balance error:', error)
    handleBalanceNetworkError(error)
  }
}

// Handle balance error
function handleBalanceError(data) {
  console.warn('⚠️ Balance error:', data.error)
  
  // Show balance UI with zero values
  if (errorDisplay) errorDisplay.classList.add('hidden')
  if (balanceContent) balanceContent.classList.remove('hidden')
  
  // Set balance to zero
  if (notesCount) notesCount.textContent = '0'
  if (totalAssets) {
    totalAssets.innerHTML = `
      <span class="text-4xl font-bold">0</span>
      <span class="text-lg text-blue-100 ml-2">nock</span>
      <br>
      <span class="text-lg text-blue-200">0</span>
      <span class="text-sm text-blue-200 ml-1">nick</span>
    `
  }
  
  // Clear notes
  allNotes = []
  selectedNotes.clear()
  
  // Show error banner
  showErrorBanner(data)
  
  // Render empty notes list
  renderNotes()
  updateSendSelectedButton()
  
  // Try to load active address anyway
  loadActiveAddress().catch(e => console.error('Failed to load active address:', e))
}

// Handle balance success
function handleBalanceSuccess(data) {
  console.log('✅ Balance loaded successfully')
  
  // Remove error banner if it exists
  const existingBanner = document.getElementById('rpcErrorBanner')
  if (existingBanner) {
    existingBanner.remove()
  }
  
  if (errorDisplay) errorDisplay.classList.add('hidden')
  if (balanceContent) balanceContent.classList.remove('hidden')
  
  if (notesCount) notesCount.textContent = data.notes_count
  
  // Display total in Nock and Nick
  const totalNock = nickToNock(data.total_assets)
  if (totalAssets) {
    totalAssets.innerHTML = `
      <span class="text-4xl font-bold">${totalNock}</span>
      <span class="text-lg text-blue-100 ml-2">nock</span>
      <br>
      <span class="text-lg text-blue-200">${data.total_assets.toLocaleString()}</span>
      <span class="text-sm text-blue-200 ml-1">nick</span>
    `
  }
  
  // Clear before storing new notes
  allNotes = []
  selectedNotes.clear()
  
  // Store all notes
  allNotes = data.notes || []
  
  console.log(`📦 ${allNotes.length} notes loaded`)
  
  // Render notes
  renderNotes()
  updateSendSelectedButton()
  
  // Load active address
  loadActiveAddress()
}

// Handle network error
function handleBalanceNetworkError(error) {
  if (loadingDisplay) loadingDisplay.classList.add('hidden')
  if (balanceDisplay) balanceDisplay.classList.remove('hidden')
  
  if (errorDisplay) errorDisplay.classList.add('hidden')
  if (balanceContent) balanceContent.classList.remove('hidden')
  
  if (notesCount) notesCount.textContent = '0'
  if (totalAssets) {
    totalAssets.innerHTML = `
      <span class="text-4xl font-bold">0</span>
      <span class="text-lg text-blue-100 ml-2">nock</span>
      <br>
      <span class="text-lg text-blue-200">0</span>
      <span class="text-sm text-blue-200 ml-1">nick</span>
    `
  }
  
  allNotes = []
  selectedNotes.clear()
  
  showNetworkErrorBanner(error.message)
  renderNotes()
  updateSendSelectedButton()
}

// Show error banner
function showErrorBanner(data) {
  const errorBanner = document.createElement('div')
  errorBanner.id = 'rpcErrorBanner'
  errorBanner.className = 'mx-8 my-6'
  
  if (data.is_rpc_error) {
    errorBanner.innerHTML = `
      <div class="bg-amber-50 border-l-4 border-amber-500 rounded-lg shadow-lg overflow-hidden">
        <div class="p-6">
          <div class="flex items-start gap-4">
            <div class="text-4xl flex-shrink-0">🔌</div>
            <div class="flex-1">
              <h3 class="text-xl font-bold text-amber-800 mb-2">RPC Service Unavailable</h3>
              <p class="text-amber-700 mb-4">Unable to connect to the Nockchain RPC server. Your wallet data is safe, just not accessible right now.</p>
              
              <details class="mb-4">
                <summary class="cursor-pointer text-sm font-semibold text-amber-800 hover:text-amber-900 mb-2">
                  📋 What this means (click to expand)
                </summary>
                <div class="bg-white rounded-lg p-4 border border-amber-200 mt-2">
                  <ul class="text-sm text-slate-700 space-y-2 list-disc list-inside">
                    <li>The Nockchain RPC service is temporarily down or unreachable</li>
                    <li>Your wallet keys and data are stored locally and are safe</li>
                    <li>No transactions can be synced until the service is available</li>
                    <li>Try refreshing in a few moments</li>
                  </ul>
                </div>
              </details>
              
              <details>
                <summary class="cursor-pointer text-sm font-semibold text-amber-800 hover:text-amber-900 mb-2">
                  🔧 Technical Details (click to expand)
                </summary>
                <div class="bg-slate-900 text-slate-100 rounded-lg p-4 text-xs font-mono mt-2 max-h-64 overflow-y-auto">
                  <pre class="whitespace-pre-wrap break-all text-slate-300">${data.error_details || 'No details available'}</pre>
                </div>
              </details>
              
              <button onclick="window.updateBalance()" class="mt-4 btn-primary btn-blue">
                🔄 Retry Connection
              </button>
            </div>
          </div>
        </div>
      </div>
    `
  } else {
    errorBanner.innerHTML = `
      <div class="bg-red-50 border-l-4 border-red-500 rounded-lg shadow-lg overflow-hidden">
        <div class="p-6">
          <div class="flex items-start gap-4">
            <div class="text-4xl flex-shrink-0">⚠️</div>
            <div class="flex-1">
              <h3 class="text-xl font-bold text-red-800 mb-2">${data.error}</h3>
              <p class="text-red-700 mb-4">An error occurred while fetching your balance.</p>
              
              <details>
                <summary class="cursor-pointer text-sm font-semibold text-red-800 hover:text-red-900 mb-2">
                  🔧 Error Details (click to expand)
                </summary>
                <div class="bg-slate-900 text-slate-100 rounded-lg p-4 text-xs font-mono mt-2 max-h-64 overflow-y-auto">
                  <pre class="whitespace-pre-wrap break-all text-slate-300">${data.error_details || 'No details available'}</pre>
                </div>
              </details>
              
              <button onclick="window.updateBalance()" class="mt-4 btn-primary btn-blue">
                🔄 Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    `
  }
  
  // Remove any existing error banner
  const existingBanner = document.getElementById('rpcErrorBanner')
  if (existingBanner) {
    existingBanner.remove()
  }
  
  // Insert error banner before notes list
  if (notesList && notesList.parentElement) {
    notesList.parentElement.insertBefore(errorBanner, notesList)
  }
}

// Show network error banner
function showNetworkErrorBanner(message) {
  const errorBanner = document.createElement('div')
  errorBanner.id = 'rpcErrorBanner'
  errorBanner.className = 'mx-8 my-6'
  errorBanner.innerHTML = `
    <div class="bg-red-50 border-l-4 border-red-500 rounded-lg shadow-lg overflow-hidden">
      <div class="p-6">
        <div class="flex items-start gap-4">
          <div class="text-4xl flex-shrink-0">❌</div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-red-800 mb-2">Network Error</h3>
            <p class="text-red-700 mb-4">Failed to communicate with the wallet backend.</p>
            
            <div class="bg-white rounded-lg p-4 border border-red-200 mb-4">
              <p class="text-sm text-slate-700">${message}</p>
            </div>
            
            <button onclick="window.updateBalance()" class="btn-primary btn-blue">
              🔄 Try Again
            </button>
          </div>
        </div>
      </div>
    </div>
  `
  
  const existingBanner = document.getElementById('rpcErrorBanner')
  if (existingBanner) {
    existingBanner.remove()
  }
  
  if (notesList && notesList.parentElement) {
    notesList.parentElement.insertBefore(errorBanner, notesList)
  }
}

// Load active address
export async function loadActiveAddress() {
  try {
    console.log('🔄 Loading active address...')
    const data = await getActiveAddress()  // No grpcConfig needed
    
    if (data.success) {
      const activeAddressElem = document.getElementById('activeAddress')
      const activeAddressVersionElem = document.getElementById('activeAddressVersion')
      
      if (activeAddressElem) {
        activeAddressElem.textContent = data.active_address
      }
      
      if (activeAddressVersionElem) {
        activeAddressVersionElem.textContent = `v${data.version}`
      }
      console.log('✅ Active address loaded')
    }
  } catch (error) {
    console.error('❌ Error loading active address:', error)
    const activeAddressElem = document.getElementById('activeAddress')
    if (activeAddressElem) {
      activeAddressElem.textContent = 'Error loading address'
      activeAddressElem.classList.add('text-red-600')
    }
  }
}