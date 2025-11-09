/**
 * gRPC Configuration Management
 */
import { getGrpcConfig, saveGrpcConfig } from '../api/config.js'

// DOM Elements
const publicRadio = document.getElementById('grpcPublic')
const privateRadio = document.getElementById('grpcPrivate')
const customRadio = document.getElementById('grpcCustom')
const customAddressInput = document.getElementById('customGrpcAddress')
const saveGrpcBtn = document.getElementById('saveGrpcBtn')

// Current config
let currentConfig = {
  type: 'public',
  customAddress: ''
}

/**
 * Load gRPC configuration from backend
 */
export async function loadGrpcConfig() {
  console.log('🔧 Initializing gRPC config...')
  
  try {
    const response = await getGrpcConfig()
    
    console.log('📋 Loaded config:', response)
    
    if (response && response.config && response.config.grpc) {
      currentConfig = {
        type: response.config.grpc.type || 'public', 
        customAddress: response.config.grpc.customAddress || ''  
      }
      console.log('🎯 gRPC type from config:', currentConfig.type)
    }
    
    // Update UI to reflect loaded config
    updateGrpcUI()
    
  } catch (error) {
    console.error('❌ Error loading gRPC config:', error)
    // Use default config on error
    currentConfig = { type: 'public', customAddress: '' }
    updateGrpcUI()
  }
}

/**
 * Update UI based on current config
 */
function updateGrpcUI() {
  console.log('🔍 Radio elements found:', {
    public: !!publicRadio,
    private: !!privateRadio,
    custom: !!customRadio
  })
  
  // D'ABORD décocher TOUS les radios
  if (publicRadio) {
    publicRadio.checked = false
    console.log('🔄 Cleared public radio')
  }
  
  if (privateRadio) {
    privateRadio.checked = false
    console.log('🔄 Cleared private radio')
  }
  
  if (customRadio) {
    customRadio.checked = false
    console.log('🔄 Cleared custom radio')
  }
  
  // ENSUITE cocher le bon selon currentConfig.type
  if (currentConfig.type === 'public' && publicRadio) {
    publicRadio.checked = true
    console.log('✅ Set public radio as checked')
    if (customAddressInput) {
      customAddressInput.disabled = true
      customAddressInput.value = ''
    }
  } else if (currentConfig.type === 'private' && privateRadio) {
    privateRadio.checked = true
    console.log('✅ Set private radio as checked')
    if (customAddressInput) {
      customAddressInput.disabled = true
      customAddressInput.value = ''
    }
  } else if (currentConfig.type === 'custom' && customRadio) {
    customRadio.checked = true
    console.log('✅ Set custom radio as checked')
    if (customAddressInput) {
      customAddressInput.disabled = false
      customAddressInput.value = currentConfig.customAddress
    }
  }
  
  console.log('🔍 Final radio states:', {
    public: publicRadio?.checked,
    private: privateRadio?.checked,
    custom: customRadio?.checked
  })
  
  console.log('✅ gRPC config initialized:', currentConfig)
}

/**
 * Save gRPC configuration
 */
async function saveGrpcConfiguration() {
  console.log('💾 Saving gRPC config...')
  
  // Get selected type
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
  
  console.log('📤 Saving config:', config)
  
  // Validate custom address if selected
  if (config.type === 'custom' && !config.customAddress) {
    alert('⚠️ Please enter a custom gRPC address')
    return
  }
  
  try {
    const response = await saveGrpcConfig(config.type, config.customAddress)
    
    if (response.success) {
      currentConfig = config
      alert('✅ gRPC configuration saved successfully!')
      console.log('✅ Config saved:', currentConfig)
      
      // Reload page to apply new config
      if (confirm('🔄 Reload page to apply changes?')) {
        window.location.reload()
      }
    } else {
      alert('❌ Failed to save configuration: ' + (response.error || 'Unknown error'))
    }
  } catch (error) {
    console.error('❌ Error saving gRPC config:', error)
    alert('❌ Error saving configuration: ' + error.message)
  }
}

/**
 * Initialize gRPC configuration UI
 */
export function initGrpcConfig() {
  console.log('🎬 Initializing gRPC config UI...')
  
  // Load config from backend
  loadGrpcConfig()
  
  // Radio change handlers
  if (publicRadio) {
    publicRadio.addEventListener('change', () => {
      if (publicRadio.checked && customAddressInput) {
        customAddressInput.disabled = true
        customAddressInput.value = ''
      }
    })
  }
  
  if (privateRadio) {
    privateRadio.addEventListener('change', () => {
      if (privateRadio.checked && customAddressInput) {
        customAddressInput.disabled = true
        customAddressInput.value = ''
      }
    })
  }
  
  if (customRadio) {
    customRadio.addEventListener('change', () => {
      if (customRadio.checked && customAddressInput) {
        customAddressInput.disabled = false
        customAddressInput.focus()
      }
    })
  }
  
  // Save button
  if (saveGrpcBtn) {
    saveGrpcBtn.addEventListener('click', saveGrpcConfiguration)
  }
  
  console.log('✅ gRPC config UI initialized')
}

/**
 * Get current gRPC config
 */
export function getCurrentGrpcConfig() {
  return currentConfig
}