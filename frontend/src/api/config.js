/**
 * Configuration API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5007';

/**
 * Get gRPC configuration
 */
export async function getGrpcConfig() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/grpc-config`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Error fetching gRPC config:', error)
    throw error
  }
}

/**
 * Save gRPC configuration
 */
export async function saveGrpcConfig(config) {
  console.log('💾 Saving gRPC config to API:', config)
  
  // ✅ Structure attendue par le backend: {grpc: {type: ..., customAddress: ...}}
  const payload = {
    grpc: {
      type: config.type || 'public',
      customAddress: config.customAddress || ''
    }
  }
  
  console.log('📤 Payload sent to API:', payload)
  
  const response = await fetch(`${API_BASE_URL}/api/grpc-config`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    console.error('❌ API error:', errorText)
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  const result = await response.json()
  console.log('✅ Config saved, server response:', result)
  
  return result
}