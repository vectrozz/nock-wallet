import { getTransactionHistory } from '../api/wallet.js'
import { openModal, closeModal } from '../ui/modals.js'
import { signTransactionHandler, sendTransactionHandler } from './transactions.js'

// Open history modal
export async function openHistoryModal() {
  console.log('📜 Opening history modal...')
  
  const historyModal = document.getElementById('historyModal')
  
  if (!historyModal) {
    console.error('❌ historyModal element not found in DOM')
    alert('Error: History modal not found')
    return
  }
  
  openModal(historyModal)
  
  // Load transaction history
  await loadTransactionHistory()
}

// Load transaction history
export async function loadTransactionHistory() {
  const historyList = document.getElementById('historyList')
  const historyLoading = document.getElementById('historyLoading')
  const historyError = document.getElementById('historyError')
  
  if (!historyList) {
    console.error('❌ historyList element not found')
    return
  }
  
  try {
    console.log('📋 Loading transaction history...')
    
    // Show loading
    if (historyLoading) historyLoading.classList.remove('hidden')
    if (historyError) historyError.classList.add('hidden')
    if (historyList) historyList.innerHTML = ''
    
    const data = await getTransactionHistory()
    
    // Hide loading
    if (historyLoading) historyLoading.classList.add('hidden')
    
    if (data.success && data.transactions && data.transactions.length > 0) {
      console.log(`📊 ${data.transactions.length} transactions loaded`)
      
      data.transactions.forEach(tx => {
        const txDiv = document.createElement('div')
        txDiv.className = 'border-b border-slate-100 last:border-b-0 p-4 hover:bg-slate-50 transition-colors'
        
        const statusClass = tx.status === 'sent' ? 'bg-green-100 text-green-800 border-green-200' :
                           tx.status === 'signed' ? 'bg-blue-100 text-blue-800 border-blue-200' :
                           'bg-yellow-100 text-yellow-800 border-yellow-200'
        
        const statusIcon = tx.status === 'sent' ? '✅' :
                          tx.status === 'signed' ? '✍️' : '📝'
        
        txDiv.innerHTML = `
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs px-2 py-1 rounded-full ${statusClass} border">
                  ${statusIcon} ${tx.status.toUpperCase()}
                </span>
                <span class="text-xs text-slate-500">${new Date(tx.sent_at).toLocaleString()}</span>
              </div>
              
              <div class="space-y-1 text-sm">
                <div class="flex gap-2">
                  <span class="text-slate-500 font-medium">Name:</span>
                  <code class="text-slate-700 font-mono text-xs">${tx.transaction_name}</code>
                </div>
                ${tx.transaction_hash ? `
                  <div class="flex gap-2">
                    <span class="text-slate-500 font-medium">Hash:</span>
                    <code class="text-slate-700 font-mono text-xs break-all">${tx.transaction_hash}</code>
                  </div>
                ` : ''}
                ${tx.recipient ? `
                  <div class="flex gap-2">
                    <span class="text-slate-500 font-medium">To:</span>
                    <code class="text-slate-700 font-mono text-xs break-all">${tx.recipient}</code>
                  </div>
                ` : ''}
                ${tx.amount ? `
                  <div class="flex gap-2">
                    <span class="text-slate-500 font-medium">Amount:</span>
                    <span class="text-slate-700">${(tx.amount / 10000).toFixed(4)} nock</span>
                  </div>
                ` : ''}
              </div>
            </div>
            
            <div class="flex flex-col gap-2">
              ${tx.status === 'created' ? `
                <button onclick="window.signTransactionHandler('${tx.transaction_name}')" class="btn-primary btn-blue text-xs px-3 py-1">
                  Sign
                </button>
              ` : ''}
              ${tx.status === 'signed' ? `
                <button onclick="window.sendTransactionHandler('${tx.transaction_name}')" class="btn-primary btn-green text-xs px-3 py-1">
                  Send
                </button>
              ` : ''}
            </div>
          </div>
        `
        
        historyList.appendChild(txDiv)
      })
    } else {
      console.log('📭 No transaction history found')
      historyList.innerHTML = `
        <div class="p-8 text-center">
          <div class="text-6xl mb-4">📭</div>
          <p class="text-slate-600 font-semibold mb-2">No transaction history</p>
          <p class="text-slate-500 text-sm">Your transaction history will appear here</p>
        </div>
      `
    }
  } catch (error) {
    console.error('❌ Error loading transaction history:', error)
    
    if (historyLoading) historyLoading.classList.add('hidden')
    if (historyError) {
      historyError.classList.remove('hidden')
      historyError.textContent = error.message || 'Failed to load transaction history'
    }
    
    if (historyList) {
      historyList.innerHTML = `
        <div class="p-8 text-center">
          <div class="text-6xl mb-4">⚠️</div>
          <p class="text-red-600 font-semibold mb-2">Error loading history</p>
          <p class="text-slate-500 text-sm">${error.message}</p>
        </div>
      `
    }
  }
}

// Show history tab
export function showHistory() {
  const historyContent = document.getElementById('historyContent')
  const notesContent = document.getElementById('notesContent')
  const historyTab = document.getElementById('historyTab')
  const notesTab = document.getElementById('notesTab')
  
  if (historyContent) historyContent.classList.remove('hidden')
  if (notesContent) notesContent.classList.add('hidden')
  
  if (historyTab) {
    historyTab.classList.add('border-blue-500', 'text-blue-600')
    historyTab.classList.remove('border-transparent', 'text-slate-600')
  }
  if (notesTab) {
    notesTab.classList.remove('border-blue-500', 'text-blue-600')
    notesTab.classList.add('border-transparent', 'text-slate-600')
  }
  
  loadTransactionHistory()
}

// Show notes tab
export function showNotes() {
  const historyContent = document.getElementById('historyContent')
  const notesContent = document.getElementById('notesContent')
  const historyTab = document.getElementById('historyTab')
  const notesTab = document.getElementById('notesTab')
  
  if (historyContent) historyContent.classList.add('hidden')
  if (notesContent) notesContent.classList.remove('hidden')
  
  if (historyTab) {
    historyTab.classList.remove('border-blue-500', 'text-blue-600')
    historyTab.classList.add('border-transparent', 'text-slate-600')
  }
  if (notesTab) {
    notesTab.classList.add('border-blue-500', 'text-blue-600')
    notesTab.classList.remove('border-transparent', 'text-slate-600')
  }
}