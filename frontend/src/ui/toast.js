// Show loading toast
export function showLoadingToast(message) {
  const toast = document.createElement('div')
  toast.className = 'fixed top-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg z-[10000] animate-slideIn'
  toast.innerHTML = `
    <div class="flex items-center gap-3">
      <div class="loading-spinner-small"></div>
      <span class="font-semibold">${message}</span>
    </div>
  `
  document.body.appendChild(toast)
  return toast
}

// Show success toast
export function showSuccessToast(message) {
  const toast = document.createElement('div')
  toast.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-[10000] animate-slideIn'
  toast.innerHTML = `
    <div class="flex items-center gap-2">
      <span class="text-xl">✅</span>
      <span class="font-semibold">${message}</span>
    </div>
  `
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-out'
    setTimeout(() => {
      if (document.body.contains(toast)) {
        document.body.removeChild(toast)
      }
    }, 300)
  }, 3000)
}

// Show error toast
export function showErrorToast(message) {
  const toast = document.createElement('div')
  toast.className = 'fixed top-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-[10000] animate-slideIn'
  toast.innerHTML = `
    <div class="flex items-center gap-2">
      <span class="text-xl">⚠️</span>
      <span class="font-semibold">${message}</span>
    </div>
  `
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-out'
    setTimeout(() => {
      if (document.body.contains(toast)) {
        document.body.removeChild(toast)
      }
    }, 300)
  }, 5000)
}