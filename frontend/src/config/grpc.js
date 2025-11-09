// API Base URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5007'

// Load config from backend
export async function loadConfig() {
  try {
    const response = await fetch(`${API_BASE}/api/config`)
    const data = await response.json()
    
    if (data.success) {
      return data.config
    }
    return getDefaultConfig()
  } catch (error) {
    console.error('Error loading config:', error)
    return getDefaultConfig()
  }
}

// Save config to backend
export async function saveConfig(config) {
  try {
    const response = await fetch(`${API_BASE}/api/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    })
    return response.json()
  } catch (error) {
    console.error('Error saving config:', error)
    throw error
  }
}

// Get default config
function getDefaultConfig() {
  return {
    grpc: {
      type: 'public',
      customAddress: ''
    }
  }
}

// Initialize gRPC config from backend
export async function initializeGrpcConfig() {
  console.log('🔧 Initializing gRPC config...')
  
  // Wait for config to load
  const config = await loadConfig()
  const grpcType = config.grpc.type
  
  console.log('📋 Loaded config:', config)
  console.log('🎯 gRPC type from config:', grpcType)
  
  // Wait a bit for DOM to be fully ready
  await new Promise(resolve => setTimeout(resolve, 100))
  
  const publicRadio = document.getElementById('grpcPublic')
  const privateRadio = document.getElementById('grpcPrivate')
  const customRadio = document.getElementById('grpcCustom')
  const customAddressInput = document.getElementById('customGrpcAddress')
  
  console.log('🔍 Radio elements found:', {
    public: !!publicRadio,
    private: !!privateRadio,
    custom: !!customRadio
  })
  
  // Clear all first
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
  
  // Set the correct radio button based on config
  if (grpcType === 'private') {
    if (privateRadio) {
      privateRadio.checked = true
      // Force DOM update
      privateRadio.setAttribute('checked', 'checked')
      console.log('✅ Set private radio as checked')
      console.log('🔍 Private radio checked state:', privateRadio.checked)
    } else {
      console.error('❌ Private radio element not found!')
    }
  } else if (grpcType === 'custom') {
    if (customRadio) {
      customRadio.checked = true
      customRadio.setAttribute('checked', 'checked')
      if (customAddressInput) {
        customAddressInput.value = config.grpc.customAddress || ''
      }
      console.log('✅ Set custom radio as checked')
      console.log('🔍 Custom radio checked state:', customRadio.checked)
    } else {
      console.error('❌ Custom radio element not found!')
    }
  } else {
    // Default to public
    if (publicRadio) {
      publicRadio.checked = true
      publicRadio.setAttribute('checked', 'checked')
      console.log('✅ Set public radio as checked')
      console.log('🔍 Public radio checked state:', publicRadio.checked)
    } else {
      console.error('❌ Public radio element not found!')
    }
  }
  
  updateCustomGrpcVisibility()
  
  // Verify final state
  console.log('🔍 Final radio states:', {
    public: publicRadio?.checked,
    private: privateRadio?.checked,
    custom: customRadio?.checked
  })
  
  console.log('✅ gRPC config initialized:', config.grpc)
}

// Handle gRPC server type change
export async function handleGrpcServerChange(type) {
  console.log('🔄 gRPC server type changing to:', type)
  
  const config = await loadConfig()
  config.grpc.type = type
  
  console.log('💾 Saving new config:', config)
  
  // Save to backend
  const response = await saveConfig(config)
  
  if (response.success) {
    console.log('✅ Config saved successfully')
    console.log('🔄 Reloading page in 500ms...')
    
    // Show a brief notification before refresh
    const toast = document.createElement('div')
    toast.className = 'fixed top-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg z-50'
    toast.innerHTML = `🔄 Switching to ${type} gRPC server...`
    document.body.appendChild(toast)
    
    // ✅ AUTO-REFRESH after 500ms
    setTimeout(() => {
      window.location.reload()
    }, 500)
  } else {
    console.error('❌ Failed to save config')
  }
}

// Update custom gRPC server address
export async function updateCustomGrpcServer() {
  const customAddressInput = document.getElementById('customGrpcAddress')
  const customAddress = customAddressInput?.value || ''
  
  console.log('🔄 Custom gRPC server updating to:', customAddress)
  
  const config = await loadConfig()
  config.grpc.customAddress = customAddress
  
  console.log('💾 Saving custom address config:', config)
  
  // Save to backend
  const response = await saveConfig(config)
  
  if (response.success) {
    console.log('✅ Config saved, refreshing page...')
    
    // Show a brief notification before refresh
    const toast = document.createElement('div')
    toast.className = 'fixed top-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg z-50'
    toast.innerHTML = '🔄 Custom gRPC address updated, reloading...'
    document.body.appendChild(toast)
    
    // ✅ AUTO-REFRESH after 500ms
    setTimeout(() => {
      window.location.reload()
    }, 500)
  }
}

// Update visibility of custom address input
function updateCustomGrpcVisibility() {
  const customRadio = document.getElementById('grpcCustom')
  const customAddressDiv = document.getElementById('customGrpcAddressDiv')
  
  if (customAddressDiv) {
    if (customRadio?.checked) {
      customAddressDiv.classList.remove('hidden')
    } else {
      customAddressDiv.classList.add('hidden')
    }
  }
}