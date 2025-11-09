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
let transactionWasSent = false  // ✅ NOUVEAU FLAG

// Open send modal
export function openSendModal() {
  console.log('💸 Opening send modal...')
  
  // ✅ Reset flag
  transactionWasSent = false
  
  // Pre-fill amount if notes are selected
  if (selectedNotes.size > 0) {
    const totalSelected = Array.from(selectedNotes).reduce((sum, index) => {
      return sum + allNotes[index].value
    }, 0)
    if (amountInput) {
      // Convert nick to nock (divide by 10000)
      const nockAmount = totalSelected / 10000
      amountInput.value = nockAmount.toFixed(4)
    }
  }
  
  // Reset form
  if (recipientInput) recipientInput.value = ''
  if (!selectedNotes.size && amountInput) amountInput.value = ''
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
  const recipient = recipientInput?.value.trim()
  const amountNock = parseFloat(amountInput?.value || 0)
  const fee = parseInt(feeInput?.value || 10)
  
  if (!recipient) {
    alert('⚠️ Please enter a recipient address')
    return
  }
  
  if (!amountNock || amountNock <= 0) {
    alert('⚠️ Please enter a valid amount')
    return
  }
  
  // Convert nock to nick (multiply by 10000)
  const amountNick = Math.floor(amountNock * 10000)
  
  showStep('processing')
  
  try {
    // Prepare transaction data
    const txData = {
      recipient: recipient,
      amount: amountNick,
      fee: fee
    }
    
    // Add note indices if specific notes are selected
    if (selectedNotes.size > 0) {
      txData.note_indices = Array.from(selectedNotes)
    }
    
    console.log('📝 Creating transaction:', txData)
    
    const response = await createTransaction(txData)
    
    if (response.success) {
      currentTransaction = {
        name: response.transaction_name,
        hash: response.transaction_hash,
        recipient: recipient,
        amount: amountNick,
        fee: fee
      }
      
      // Show confirmation step with details
      const txDetailsElem = document.getElementById('txDetails')
      if (txDetailsElem) {
        txDetailsElem.textContent = `
Recipient: ${recipient}
Amount: ${amountNock.toFixed(4)} nock (${amountNick.toLocaleString()} nick)
Fee: ${fee} nick
Transaction: ${response.transaction_name}
Hash: ${response.transaction_hash}
        `.trim()
      }
      
      showStep('confirm')
      showSuccessToast('Transaction created successfully!')
      
      console.log('✅ Transaction created:', response)
    } else {
      showStep('create')
      showErrorToast(response.error || 'Failed to create transaction')
    }
  } catch (error) {
    console.error('❌ Error creating transaction:', error)
    showStep('create')
    showErrorToast(error.message || 'Network error')
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
      // ✅ MARQUER QUE LA TRANSACTION A ÉTÉ ENVOYÉE
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

// ✅ EXPORTER pour history.js
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

// ✅ EXPORTER pour history.js
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
  
  // ✅ NE RECHARGER QUE SI UNE TRANSACTION A ÉTÉ ENVOYÉE
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