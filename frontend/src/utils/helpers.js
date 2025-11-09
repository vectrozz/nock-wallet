// Convert Nick to Nock
export function nickToNock(nick) {
  return (nick / 65536).toFixed(4)
}

// Truncate string with ellipsis
export function truncateString(str, maxLength) {
  if (str.length <= maxLength) return str
  return str.substring(0, maxLength) + '...'
}

// Format date
export function formatDate(isoString) {
  if (!isoString) return 'N/A'
  const date = new Date(isoString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Get status badge color
export function getStatusBadge(status) {
  const colors = {
    'created': 'status-created',
    'signed': 'status-signed',
    'sent': 'status-sent'
  }
  return colors[status] || 'bg-gray-100 text-gray-800 border border-gray-200'
}

// Copy to clipboard
export function copyToClipboard(text) {
  console.log('Copying to clipboard:', text)
  navigator.clipboard.writeText(text).then(() => {
    const { showSuccessToast } = require('../ui/toast')
    showSuccessToast('Address copied to clipboard!')
  }).catch(err => {
    console.error('Failed to copy:', err)
    const { showErrorToast } = require('../ui/toast')
    showErrorToast('Failed to copy address to clipboard')
  })
}