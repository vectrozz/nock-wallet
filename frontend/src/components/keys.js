import { importKeys } from '../api/wallet.js'
import { openModal, closeModal } from '../ui/modals.js'
import { showLoadingToast, showSuccessToast, showErrorToast } from '../ui/toast.js'
import { updateBalance } from './balance.js'

// Open import keys modal
export function openImportModal() {
  console.log('🔑 Opening import keys modal...')
  
  const importModal = document.getElementById('importModal')
  
  if (!importModal) {
    console.error('❌ importModal element not found in DOM')
    alert('Error: Import modal not found')
    return
  }
  
  // Reset form
  const seedInput = document.getElementById('seedInput')
  const fileInput = document.getElementById('fileInput')
  
  if (seedInput) seedInput.value = ''
  if (fileInput) fileInput.value = ''
  
  openModal(importModal)
}

// Import keys handler
export async function importKeysHandler() {
  const seedInput = document.getElementById('seedInput')
  const seed = seedInput?.value.trim()
  
  if (!seed) {
    alert('⚠️ Please enter a seed phrase')
    return
  }
  
  const loadingToast = showLoadingToast('Importing keys...')
  
  try {
    console.log('🔑 Importing keys from seed...')
    
    const response = await importKeys({ seed })
    
    document.body.removeChild(loadingToast)
    
    if (response.success) {
      showSuccessToast('Keys imported successfully!')
      
      // Close modal
      const importModal = document.getElementById('importModal')
      if (importModal) {
        closeModal(importModal)
      }
      
      // Refresh balance to show new keys
      setTimeout(() => {
        updateBalance()
      }, 500)
      
      console.log('✅ Keys imported:', response)
    } else {
      showErrorToast(response.error || 'Failed to import keys')
    }
  } catch (error) {
    console.error('❌ Error importing keys:', error)
    document.body.removeChild(loadingToast)
    showErrorToast(error.message || 'Network error')
  }
}

// Import from file handler
export async function importFromFileHandler() {
  const fileInput = document.getElementById('fileInput')
  const file = fileInput?.files?.[0]
  
  if (!file) {
    alert('⚠️ Please select a file')
    return
  }
  
  const loadingToast = showLoadingToast('Importing keys from file...')
  
  try {
    console.log('🔑 Importing keys from file:', file.name)
    
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch('http://127.0.0.1:5007/api/import-keys-file', {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    
    document.body.removeChild(loadingToast)
    
    if (data.success) {
      showSuccessToast('Keys imported successfully from file!')
      
      // Close modal
      const importModal = document.getElementById('importModal')
      if (importModal) {
        closeModal(importModal)
      }
      
      // Refresh balance
      setTimeout(() => {
        updateBalance()
      }, 500)
      
      console.log('✅ Keys imported from file:', data)
    } else {
      showErrorToast(data.error || 'Failed to import keys from file')
    }
  } catch (error) {
    console.error('❌ Error importing keys from file:', error)
    document.body.removeChild(loadingToast)
    showErrorToast(error.message || 'Network error')
  }
}