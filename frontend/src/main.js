// Import all modules
import { 
  initGrpcConfig
} from './config/grpc.js'

import { 
  updateBalance, 
  loadActiveAddress 
} from './components/balance.js'

import { 
  renderNotes, 
  toggleNoteDetails, 
  handleNoteCheckboxChange,
  updateSendSelectedButton
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

import { 
  showLoadingToast, 
  showSuccessToast, 
  showErrorToast 
} from './ui/toast.js'

import { importKeys, importFromSeedphrase } from './api/wallet.js'
import { saveGrpcConfig } from './api/config.js' // ✅ Importer depuis config.js

console.log('📦 Main.js loaded')

// Import keys from seedphrase function
async function importKeysFromSeedphrase() {
  const seedphraseInput = document.getElementById('seedphraseInput')
  const seedphraseVersion = document.getElementById('seedphraseVersion')
  const importSeedphraseBtn = document.getElementById('importSeedphraseBtn')
  
  const seedphrase = seedphraseInput?.value.trim()
  const version = seedphraseVersion?.value
  
  if (!seedphrase) {
    alert('⚠️ Please enter a seed phrase')
    return
  }
  
  if (version === '') {
    alert('⚠️ Please select a version')
    return
  }
  
  // Disable button during import
  if (importSeedphraseBtn) {
    importSeedphraseBtn.disabled = true
    importSeedphraseBtn.innerHTML = '<span class="loading-spinner"></span> Importing...'
  }
  
  const loadingToast = showLoadingToast('Importing keys from seedphrase...')
  
  try {
    console.log('🌱 Importing keys from seedphrase, version:', version)
    
    const response = await importFromSeedphrase(seedphrase, parseInt(version))
    
    document.body.removeChild(loadingToast)
    
    if (response.success) {
      showSuccessToast('Keys imported successfully from seedphrase!')
      
      // Clear inputs
      if (seedphraseInput) seedphraseInput.value = ''
      if (seedphraseVersion) seedphraseVersion.value = ''
      
      // Refresh balance to show new keys
      setTimeout(() => {
        updateBalance()
      }, 500)
      
      console.log('✅ Keys imported from seedphrase:', response)
    } else {
      showErrorToast(response.error || 'Failed to import keys from seedphrase')
    }
  } catch (error) {
    console.error('❌ Error importing keys from seedphrase:', error)
    document.body.removeChild(loadingToast)
    showErrorToast(error.message || 'Network error')
  } finally {
    // Re-enable button
    if (importSeedphraseBtn) {
      importSeedphraseBtn.disabled = false
      importSeedphraseBtn.innerHTML = '<span class="btn-icon">🚀</span><span>Import from Seedphrase</span>'
    }
  }
}

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
window.importKeysFromSeedphrase = importKeysFromSeedphrase
window.openAddressesModal = openAddressesModal
window.setActiveAddress = setActiveAddress
window.copyAddress = copyAddress
window.openHistoryModal = openHistoryModal
window.closeModal = closeModal
window.handleNoteCheckboxChange = handleNoteCheckboxChange
window.toggleNoteDetails = toggleNoteDetails

// ✅ Utiliser l'API depuis config.js
window.handleGrpcServerChange = async function() {
  console.log('📻 Radio changed - saving configuration...')
  
  const publicRadio = document.getElementById('grpcPublic')
  const privateRadio = document.getElementById('grpcPrivate')
  const customRadio = document.getElementById('grpcCustom')
  const customAddressInput = document.getElementById('customGrpcAddress')
  
  // Déterminer le type sélectionné
  let selectedType = 'public'
  if (privateRadio?.checked) {
    selectedType = 'private'
  } else if (customRadio?.checked) {
    selectedType = 'custom'
  }
  
  const config = {
    type: selectedType,
    customAddress: selectedType === 'custom' ? (customAddressInput?.value.trim() || '') : ''
  }
  
  console.log('💾 Saving gRPC config:', config)
  
  try {
    // ✅ Utiliser la fonction importée au lieu de fetch direct
    const result = await saveGrpcConfig(config)
    
    if (result.success) {
      console.log('✅ gRPC configuration saved:', config)
      showSuccessToast('Configuration saved! Reloading...')
      
      // Reload page après 1 seconde
      setTimeout(() => {
        window.location.reload()
      }, 1000)
    } else {
      console.error('❌ Failed to save config:', result.error)
      showErrorToast('Failed to save configuration')
    }
  } catch (error) {
    console.error('❌ Error saving gRPC config:', error)
    showErrorToast('Error saving configuration: ' + error.message)
  }
}

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
  await initGrpcConfig()
  
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