import { createTransaction, signTransaction, sendTransaction } from '../api/wallet.js'
import { allNotes, selectedNotes, updateBalance } from './balance.js'
import { showLoadingToast, showSuccessToast, showErrorToast } from '../ui/toast.js'
import { openModal, closeModal } from '../ui/modals.js'

// DOM Elements
const sendModal = document.getElementById('sendTxModal')
const recipientInput = document.getElementById('recipientInput')
const amountInput = document.getElementById('amountInput')
const feeInput = document.getElementById('feeInput')
const createTxBtn = document.getElementById('createTxBtn')
const confirmTxBtn = document.getElementById('confirmTxBtn')
const closeSendTxModal = document.getElementById('closeSendTxModal')

// Modal steps
const createTxStep = document.getElementById('createTxStep')
const confirmTxStep = document.getElementById('confirmTxStep')
const processingTxStep = document.getElementById('processingTxStep')
const successTxStep = document.getElementById('successTxStep')

// Current transaction
let currentTransaction = null
let transactionWasSent = false

// Open send modal
export function openSendModal() {
  console.log('💸 Opening send modal...')
  
  // Reset flag
  transactionWasSent = false
  
  // ✅ Pre-fill and lock amount if notes are selected
  if (selectedNotes.size > 0) {
    const totalSelected = Array.from(selectedNotes).reduce((sum, index) => {
      return sum + allNotes[index].value
    }, 0)
    
    if (amountInput) {
      // Convert nick to nock (divide by 65536)
      const nockAmount = totalSelected / 65536
      amountInput.value = nockAmount.toFixed(4)
      
      // ✅ Lock the input (make it readonly)
      amountInput.readOnly = true
      amountInput.classList.add('bg-gray-100', 'cursor-not-allowed')
      
      console.log(`📊 Selected ${selectedNotes.size} notes, total: ${totalSelected} nick (${nockAmount.toFixed(4)} nock)`)
    }
  } else {
    // ✅ Unlock the input if no notes selected
    if (amountInput) {
      amountInput.value = ''
      amountInput.readOnly = false
      amountInput.classList.remove('bg-gray-100', 'cursor-not-allowed')
    }
  }
  
  // Reset form
  if (recipientInput) recipientInput.value = ''
  if (feeInput) feeInput.value = '10'
  
  // Reset to first step
  showStep('create')
  
  currentTransaction = null
  
  openModal(sendModal)
}

// Show specific step
function showStep(step) {
  // Hide all steps
  if (createTxStep) createTxStep.classList.add('hidden')
  if (confirmTxStep) confirmTxStep.classList.add('hidden')
  if (processingTxStep) processingTxStep.classList.add('hidden')
  if (successTxStep) successTxStep.classList.add('hidden')
  
  // Show requested step
  if (step === 'create' && createTxStep) {
    createTxStep.classList.remove('hidden')
  } else if (step === 'confirm' && confirmTxStep) {
    confirmTxStep.classList.remove('hidden')
  } else if (step === 'processing' && processingTxStep) {
    processingTxStep.classList.remove('hidden')
  } else if (step === 'success' && successTxStep) {
    successTxStep.classList.remove('hidden')
  }
}

// Create transaction
export async function createTransactionHandler() {
  const recipientInput = document.getElementById('recipientInput') 
  const amountInput = document.getElementById('amountInput')         
  const feeInput = document.getElementById('feeInput')            
  
  if (!recipientInput || !amountInput || !feeInput) {
    console.error('❌ Missing input elements')
    return
  }
  
  const recipient = recipientInput.value.trim()
  const amount = parseFloat(amountInput.value)
  const fee = parseInt(feeInput.value) || 10
  
  if (!recipient) {
    alert('Please enter a recipient address')
    return
  }
  
  if (!amount || amount <= 0) {
    alert('Please enter a valid amount')
    return
  }
  
  // Get selected notes with their FULL NAMES
  const selectedNotesArray = Array.from(selectedNotes)
  
  if (selectedNotesArray.length === 0) {
    alert('Please select at least one note')
    return
  }
  
  console.log('📝 Selected note indices:', selectedNotes)
  
  // ✅ Extract the FULL NOTE NAMES from the notes
  const selectedNoteNames = selectedNotesArray.map(noteIndex => {
    const note = allNotes[noteIndex]
    if (!note || !note.name) {
      console.error('❌ Could not find note at index', noteIndex)
      return null
    }
    console.log(`✅ Note ${noteIndex}: ${note.name.substring(0, 50)}...`)
    return note.name  // ← Le nom COMPLET de la note
  }).filter(name => name !== null)
  
  if (selectedNoteNames.length !== selectedNotesArray.length) {
    alert('Error: Could not retrieve all note names')
    return
  }
  
  console.log('📝 Creating transaction with:')
  console.log('  - Recipient:', recipient.substring(0, 30) + '...')
  console.log('  - Amount:', amount, 'NOCK')
  console.log('  - Fee:', fee, 'NICK')
  console.log('  - Notes count:', selectedNoteNames.length)
  
  const txData = {
    recipient: recipient,
    amount_nock: amount,
    fee: fee,
    selected_notes: selectedNoteNames,
    use_all_funds: true
  }
  
  console.log('📝 Transaction data:', {
    ...txData,
    selected_notes: txData.selected_notes.map(n => n.substring(0, 30) + '...')
  })
  
  try {
    const result = await createTransaction(txData)
    
    if (result.success) {
      alert(`Transaction created successfully!\nTransaction: ${result.transaction_name}`)
      
      // Clear selections
      window.selectedNotes = []
      document.querySelectorAll('.note-checkbox').forEach(cb => cb.checked = false)
      updateAmountFromSelection()
      
      // Close modal
      //document.getElementById('sendTxModal').classList.add('hidden')
      
      // Refresh balance
      await updateBalance()
    } else {
      alert(`Failed to create transaction: ${result.error}`)
    }
  } catch (error) {
    console.error('❌ Error creating transaction:', error)
    alert(`Error: ${error.message}`)
  }
}

// Confirm and send transaction
export async function confirmTransactionHandler() {
  if (!currentTransaction) {
    alert('⚠️ No transaction to send')
    return
  }
  
  showStep('processing')
  
  try {
    console.log('✍️ Signing transaction:', currentTransaction.name)
    
    // Sign transaction
    const signResponse = await signTransaction(currentTransaction.name)
    
    if (!signResponse.success) {
      showStep('confirm')
      showErrorToast(signResponse.error || 'Failed to sign transaction')
      return
    }
    
    console.log('✅ Transaction signed')
    
    // Send transaction
    console.log('📤 Sending transaction:', currentTransaction.name)
    const sendResponse = await sendTransaction(currentTransaction.name)
    
    if (sendResponse.success) {
      transactionWasSent = true
      
      showStep('success')
      showSuccessToast('Transaction sent successfully!')
      
      console.log('✅ Transaction sent:', sendResponse)
      
      // Refresh balance after a delay
      setTimeout(() => {
        updateBalance()
      }, 2000)
      
    } else {
      showStep('confirm')
      showErrorToast(sendResponse.error || 'Failed to send transaction')
    }
  } catch (error) {
    console.error('❌ Error sending transaction:', error)
    showStep('confirm')
    showErrorToast(error.message || 'Network error')
  }
}

// Export for history.js
export async function signTransactionHandler(transactionName) {
  console.log('✍️ Signing transaction:', transactionName)
  
  try {
    const signResponse = await signTransaction(transactionName)
    
    if (signResponse.success) {
      showSuccessToast('Transaction signed successfully!')
      return signResponse
    } else {
      showErrorToast(signResponse.error || 'Failed to sign transaction')
      return signResponse
    }
  } catch (error) {
    console.error('❌ Error signing transaction:', error)
    showErrorToast(error.message || 'Network error')
    throw error
  }
}

// Export for history.js
export async function sendTransactionHandler(transactionName) {
  console.log('📤 Sending transaction:', transactionName)
  
  try {
    const sendResponse = await sendTransaction(transactionName)
    
    if (sendResponse.success) {
      showSuccessToast('Transaction sent successfully!')
      
      // Refresh balance after sending
      setTimeout(() => {
        updateBalance()
      }, 2000)
      
      return sendResponse
    } else {
      showErrorToast(sendResponse.error || 'Failed to send transaction')
      return sendResponse
    }
  } catch (error) {
    console.error('❌ Error sending transaction:', error)
    showErrorToast(error.message || 'Network error')
    throw error
  }
}

// Close modal
function closeSendTxModalHandler() {
  closeModal(sendModal)
  
  // Only reload if transaction was sent
  if (transactionWasSent) {
    console.log('🔄 Transaction was sent, reloading balance...')
    setTimeout(() => {
      updateBalance()
    }, 500)
  } else {
    console.log('ℹ️ No transaction sent, skipping balance reload')
  }
}

// Attach event listeners when DOM is ready
if (createTxBtn) {
  createTxBtn.addEventListener('click', createTransactionHandler)
}

if (confirmTxBtn) {
  confirmTxBtn.addEventListener('click', confirmTransactionHandler)
}

if (closeSendTxModal) {
  closeSendTxModal.addEventListener('click', closeSendTxModalHandler)
}

const backToCreateBtn = document.getElementById('backToCreateBtn')
if (backToCreateBtn) {
  backToCreateBtn.addEventListener('click', () => showStep('create'))
}

const closeTxSuccessBtn = document.getElementById('closeTxSuccessBtn')
if (closeTxSuccessBtn) {
  closeTxSuccessBtn.addEventListener('click', closeSendTxModalHandler)
}