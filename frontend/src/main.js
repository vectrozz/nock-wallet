// Import all modules
import { 
  initializeGrpcConfig, 
  handleGrpcServerChange, 
  updateCustomGrpcServer 
} from './config/grpc.js'

import { 
  updateBalance, 
  loadActiveAddress 
} from './components/balance.js'

import { 
  renderNotes, 
  toggleNoteDetails, 
  handleNoteCheckboxChange,  // ✅ Déjà importé
  updateSendSelectedButton   // ✅ AJOUTER
} from './components/notes.js'

import { 
  openHistoryModal, 
  showHistory, 
  showNotes, 
  loadTransactionHistory 
} from './components/history.js'

import { 
  openSendModal, 
  createTransactionHandler, 
  confirmTransactionHandler,
  signTransactionHandler,
  sendTransactionHandler
} from './components/transactions.js'

import { 
  openAddressesModal, 
  setActiveAddress, 
  copyAddress 
} from './components/addresses.js'

import { 
  openImportModal, 
  importKeysHandler, 
  importFromFileHandler 
} from './components/keys.js'

import { 
  openModal, 
  closeModal 
} from './ui/modals.js'

console.log('📦 Main.js loaded')

// Make functions globally accessible for onclick handlers
window.updateBalance = updateBalance
window.openSendModal = openSendModal
window.createTransactionHandler = createTransactionHandler
window.confirmTransactionHandler = confirmTransactionHandler
window.signTransactionHandler = signTransactionHandler
window.sendTransactionHandler = sendTransactionHandler
window.openImportModal = openImportModal
window.importKeysHandler = importKeysHandler
window.importFromFileHandler = importFromFileHandler
window.openAddressesModal = openAddressesModal
window.setActiveAddress = setActiveAddress
window.copyAddress = copyAddress
window.openHistoryModal = openHistoryModal
window.handleGrpcServerChange = handleGrpcServerChange
window.updateCustomGrpcServer = updateCustomGrpcServer
window.closeModal = closeModal
window.handleNoteCheckboxChange = handleNoteCheckboxChange  // ✅ AJOUTER
window.toggleNoteDetails = toggleNoteDetails                // ✅ AJOUTER

// Close modals on background click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal')) {
    closeModal(e.target)
  }
})

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
  console.log('🚀 Nockchain Wallet starting...')
  
  // Initialize gRPC configuration FIRST (wait for it)
  await initializeGrpcConfig()
  
  // Add event listeners for buttons
  const updateBalanceBtn = document.getElementById('updateBalanceBtn')
  if (updateBalanceBtn) {
    console.log('✅ Attaching click handler to updateBalanceBtn')
    updateBalanceBtn.addEventListener('click', () => {
      console.log('🔄 Refresh button clicked')
      updateBalance()
    })
  }
  
  const sendSelectedBtn = document.getElementById('sendSelectedBtn')
  if (sendSelectedBtn) {
    console.log('✅ Attaching click handler to sendSelectedBtn')
    sendSelectedBtn.addEventListener('click', () => {
      console.log('💸 Send selected button clicked')
      openSendModal()
    })
  }
  
  const sendTxBtn = document.getElementById('sendTxBtn')
  if (sendTxBtn) {
    console.log('✅ Attaching click handler to sendTxBtn')
    sendTxBtn.addEventListener('click', () => {
      console.log('💸 Send transaction button clicked')
      openSendModal()
    })
  }
  
  const showAllAddressesBtn = document.getElementById('showAllAddressesBtn')
  if (showAllAddressesBtn) {
    console.log('✅ Attaching click handler to showAllAddressesBtn')
    showAllAddressesBtn.addEventListener('click', () => {
      console.log('📋 Show all addresses button clicked')
      openAddressesModal()
    })
  }
  
  // Initial data load
  console.log('📊 Loading initial balance...')
  updateBalance()
  
  console.log('✅ Wallet initialized successfully')
})