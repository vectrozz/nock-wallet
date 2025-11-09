import { importKeysFromFile, importFromSeedphrase, showSeedphrase, getExportKeysUrl } from '../api/wallet.js'
import { updateBalance } from '../components/balance.js'
import { showLoadingToast, showSuccessToast, showErrorToast } from './toast.js'

// Open modal
export function openModal(modal) {
  if (!modal) {
    console.error('Modal element not found')
    return
  }
  modal.classList.remove('hidden')
  setTimeout(() => {
    const content = modal.querySelector('.modal-content')
    if (content) {
      content.classList.remove('scale-95', 'opacity-0')
      content.classList.add('scale-100', 'opacity-100')
    }
  }, 10)
}

// Close modal
export function closeModal(modal) {
  if (!modal) return
  const content = modal.querySelector('.modal-content')
  if (content) {
    content.classList.remove('scale-100', 'opacity-100')
    content.classList.add('scale-95', 'opacity-0')
  }
  setTimeout(() => {
    modal.classList.add('hidden')
  }, 200)
}

// Import keys modal
export async function openImportModal() {
  const modal = document.getElementById('importModal')
  openModal(modal)
}

export async function importKeys() {
  const fileInput = document.getElementById('importKeysFile')
  const file = fileInput.files[0]
  
  if (!file) {
    alert('⚠️ Please select a file')
    return
  }
  
  const formData = new FormData()
  formData.append('file', file)
  
  const loadingToast = showLoadingToast('Importing keys...')
  
  try {
    const response = await importKeysFromFile(formData)
    
    document.body.removeChild(loadingToast)
    
    if (response.success) {
      showSuccessToast('Keys imported successfully!')
      closeModal(document.getElementById('importModal'))
      fileInput.value = ''
      await updateBalance()
    } else {
      showErrorToast(response.error || 'Import failed')
    }
  } catch (error) {
    console.error('Error importing keys:', error)
    document.body.removeChild(loadingToast)
    showErrorToast(error.message || 'Network error')
  }
}

// Import seedphrase modal
export async function openImportSeedphraseModal() {
  const modal = document.getElementById('importSeedphraseModal')
  openModal(modal)
}

export async function importSeedphrase() {
  const seedphrase = document.getElementById('seedphraseInput').value.trim()
  const version = document.getElementById('seedphraseVersion').value
  
  if (!seedphrase) {
    alert('⚠️ Please enter a seedphrase')
    return
  }
  
  const loadingToast = showLoadingToast('Importing from seedphrase...')
  
  try {
    const response = await importFromSeedphrase(seedphrase, version)
    
    document.body.removeChild(loadingToast)
    
    if (response.success) {
      showSuccessToast('Seedphrase imported successfully!')
      closeModal(document.getElementById('importSeedphraseModal'))
      document.getElementById('seedphraseInput').value = ''
      await updateBalance()
    } else {
      showErrorToast(response.error || 'Import failed')
    }
  } catch (error) {
    console.error('Error importing seedphrase:', error)
    document.body.removeChild(loadingToast)
    showErrorToast(error.message || 'Network error')
  }
}

// Show seedphrase modal
export async function openShowSeedphraseModal() {
  if (!confirm('⚠️ WARNING: Your seedphrase gives full access to your wallet. Never share it with anyone!\n\nDo you want to continue?')) {
    return
  }
  
  const modal = document.getElementById('showSeedphraseModal')
  const seedphraseDisplay = document.getElementById('seedphraseDisplay')
  
  if (seedphraseDisplay) {
    seedphraseDisplay.innerHTML = '<div class="text-center text-slate-500 py-8">Loading...</div>'
  }
  openModal(modal)
  
  try {
    const data = await showSeedphrase()
    
    if (data.success && seedphraseDisplay) {
      seedphraseDisplay.innerHTML = `
        <div class="bg-amber-50 border-2 border-amber-300 rounded-lg p-6">
          <div class="flex items-start gap-3 mb-4">
            <span class="text-3xl">⚠️</span>
            <div class="flex-1">
              <h4 class="font-bold text-amber-900 mb-1">Security Warning</h4>
              <p class="text-sm text-amber-800">Never share this seedphrase with anyone. Anyone with access to it can steal your funds.</p>
            </div>
          </div>
          <div class="bg-white border border-amber-200 rounded p-4 font-mono text-sm break-all">
            ${data.seedphrase}
          </div>
          <button onclick="window.copySeedphrase('${data.seedphrase}')" class="btn-primary btn-blue w-full mt-4">
            📋 Copy to Clipboard
          </button>
        </div>
      `
    } else if (seedphraseDisplay) {
      seedphraseDisplay.innerHTML = `
        <div class="text-center text-red-600 py-8">
          <p class="font-semibold mb-2">Error</p>
          <p class="text-sm">${data.error || 'Failed to retrieve seedphrase'}</p>
        </div>
      `
    }
  } catch (error) {
    console.error('Error showing seedphrase:', error)
    if (seedphraseDisplay) {
      seedphraseDisplay.innerHTML = `
        <div class="text-center text-red-600 py-8">
          <p class="font-semibold mb-2">Network Error</p>
          <p class="text-sm">${error.message}</p>
        </div>
      `
    }
  }
}

// Export keys
export function exportKeys() {
  window.location.href = getExportKeysUrl()
}

// Copy seedphrase
export function copySeedphrase(seedphrase) {
  navigator.clipboard.writeText(seedphrase).then(() => {
    showSuccessToast('Seedphrase copied to clipboard!')
  }).catch(err => {
    console.error('Failed to copy:', err)
    showErrorToast('Failed to copy seedphrase')
  })
}