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
  handleNoteCheckboxChange 
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
  confirmTransactionHandler 
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

// Close modals on background click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal')) {
    closeModal(e.target)
  }
})

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
  console.log('🚀 Nockchain Wallet starting...')
  
  // ✅ Initialize gRPC configuration FIRST (wait for it)
  await initializeGrpcConfig()
  
  // Add event listeners for buttons
  const updateBalanceBtn = document.getElementById('updateBalanceBtn')
  if (updateBalanceBtn) {
    console.log('✅ Attaching click handler to updateBalanceBtn')
    updateBalanceBtn.addEventListener('click', () => {
      console.log('🔄 Refresh button clicked')
      updateBalance()
    })
  } else {
    console.warn('⚠️ updateBalanceBtn not found')
  }
  
  const sendSelectedBtn = document.getElementById('sendSelectedBtn')
  if (sendSelectedBtn) {
    console.log('✅ Attaching click handler to sendSelectedBtn')
    sendSelectedBtn.addEventListener('click', () => {
      console.log('💸 Send selected button clicked')
      openSendModal()
    })
  } else {
    console.warn('⚠️ sendSelectedBtn not found')
  }
  
  const sendTxBtn = document.getElementById('sendTxBtn')
  if (sendTxBtn) {
    console.log('✅ Attaching click handler to sendTxBtn')
    sendTxBtn.addEventListener('click', () => {
      console.log('💸 Send transaction button clicked')
      openSendModal()
    })
  } else {
    console.warn('⚠️ sendTxBtn not found')
  }
  
  const showAllAddressesBtn = document.getElementById('showAllAddressesBtn')
  if (showAllAddressesBtn) {
    console.log('✅ Attaching click handler to showAllAddressesBtn')
    showAllAddressesBtn.addEventListener('click', () => {
      console.log('📋 Show all addresses button clicked')
      openAddressesModal()
    })
  } else {
    console.warn('⚠️ showAllAddressesBtn not found')
  }
  
  const importKeysBtn = document.getElementById('importKeysBtn')
  if (importKeysBtn) {
    console.log('✅ Attaching click handler to importKeysBtn')
    importKeysBtn.addEventListener('click', () => {
      console.log('🔑 Import keys button clicked')
      openImportModal()
    })
  } else {
    console.warn('⚠️ importKeysBtn not found')
  }
  
  const historyBtn = document.getElementById('historyBtn')
  if (historyBtn) {
    console.log('✅ Attaching click handler to historyBtn')
    historyBtn.addEventListener('click', () => {
      console.log('📜 History button clicked')
      openHistoryModal()
    })
  } else {
    console.warn('⚠️ historyBtn not found')
  }
  
  // Initial data load
  console.log('📊 Loading initial balance...')
  updateBalance()
  
  console.log('✅ Wallet initialized successfully')
})