import { listMasterAddresses, setActiveAddress as setActiveAddressAPI } from '../api/wallet.js'
import { updateBalance } from './balance.js'
import { openModal, closeModal } from '../ui/modals.js'
import { showLoadingToast, showSuccessToast, showErrorToast } from '../ui/toast.js'
import { copyToClipboard } from '../utils/helpers.js'

// Open addresses modal
export async function openAddressesModal() {
  console.log('🔓 Opening addresses modal...')
  
  // Get the modal element at runtime
  const addressesModal = document.getElementById('addressesModal')
  const addressesList = document.getElementById('addressesList')
  
  if (!addressesModal) {
    console.error('❌ addressesModal element not found in DOM')
    alert('Error: Addresses modal not found')
    return
  }
  
  if (!addressesList) {
    console.error('❌ addressesList element not found in DOM')
    alert('Error: Addresses list container not found')
    return
  }
  
  openModal(addressesModal)
  await loadMasterAddresses(addressesList, addressesModal)
}

// Load master addresses
async function loadMasterAddresses(addressesList, addressesModal) {
  try {
    console.log('📋 Loading master addresses...')
    if (addressesList) {
      addressesList.innerHTML = '<div class="p-8 text-center text-slate-500">Loading addresses...</div>'
    }
    
    // No grpcConfig needed - backend reads from config file
    const data = await listMasterAddresses()
    
    console.log('📊 Addresses data:', data)
    
    // Check both 'addresses' and 'master_addresses' keys (API might return either)
    const addresses = data.addresses || data.master_addresses || []
    
    if (addresses && addresses.length > 0) {
      if (addressesList) addressesList.innerHTML = ''
      
      addresses.forEach((addr, index) => {
        const addrDiv = document.createElement('div')
        addrDiv.className = 'border-b border-slate-100 last:border-b-0 p-4 hover:bg-slate-50 transition-colors'
        
        const isActive = addr.is_active
        
        addrDiv.innerHTML = `
          <div class="flex items-center justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs px-2 py-1 rounded-full ${isActive ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-slate-100 text-slate-600 border border-slate-200'}">
                  ${isActive ? '✓ Active' : 'Inactive'}
                </span>
                <span class="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                  v${addr.version}
                </span>
              </div>
              <div class="flex items-center gap-2">
                <code class="text-xs font-mono text-slate-700 break-all">${addr.address}</code>
                <button onclick="window.copyAddress('${addr.address}')" class="text-slate-400 hover:text-blue-600 transition-colors flex-shrink-0" title="Copy address">
                  📋
                </button>
              </div>
            </div>
            ${!isActive ? `
              <button onclick="window.setActiveAddress('${addr.address}', ${addr.version})" class="btn-primary btn-blue text-sm whitespace-nowrap">
                Set Active
              </button>
            ` : `
              <div class="text-green-600 font-semibold text-sm whitespace-nowrap">
                Currently Active
              </div>
            `}
          </div>
        `
        
        if (addressesList) addressesList.appendChild(addrDiv)
      })
      
      console.log(`✅ ${addresses.length} addresses loaded and displayed`)
    } else {
      console.warn('⚠️ No addresses found in response')
      if (addressesList) {
        addressesList.innerHTML = `
          <div class="p-8 text-center">
            <div class="text-6xl mb-4">📭</div>
            <p class="text-slate-600 font-semibold mb-2">No addresses found</p>
            <p class="text-slate-500 text-sm">Import keys to see addresses here</p>
          </div>
        `
      }
    }
  } catch (error) {
    console.error('❌ Error loading master addresses:', error)
    if (addressesList) {
      addressesList.innerHTML = `
        <div class="p-8 text-center">
          <div class="text-6xl mb-4">⚠️</div>
          <p class="text-red-600 font-semibold mb-2">Error loading addresses</p>
          <p class="text-slate-500 text-sm">${error.message}</p>
        </div>
      `
    }
  }
}

// Set active address
export async function setActiveAddress(address, version) {
  console.log('🔄 Setting active address:', address)
  const loadingToast = showLoadingToast('Setting active address...')
  
  try {
    // No grpcConfig needed - backend reads from config file
    const response = await setActiveAddressAPI(address)
    
    document.body.removeChild(loadingToast)
    
    if (response.success) {
      showSuccessToast('Active address updated!')
      
      // Close modal and refresh
      const addressesModal = document.getElementById('addressesModal')
      if (addressesModal) {
        closeModal(addressesModal)
      }
      await updateBalance()
    } else {
      showErrorToast(response.error || 'Failed to set active address')
    }
  } catch (error) {
    console.error('❌ Error setting active address:', error)
    document.body.removeChild(loadingToast)
    showErrorToast(error.message || 'Network error')
  }
}

// Copy address
export function copyAddress(address) {
  console.log('📋 Copying address:', address)
  copyToClipboard(address)
}