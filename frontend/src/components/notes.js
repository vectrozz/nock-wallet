import { allNotes, selectedNotes } from './balance.js'
import { nickToNock, truncateString } from '../utils/helpers.js'

// DOM Elements
const notesList = document.getElementById('notesList')
const sendSelectedBtn = document.getElementById('sendSelectedBtn')

// Sorting state
let sortBy = 'block_height'
let sortOrder = 'desc'

// Sort notes
function sortNotes(notes) {
  const sorted = [...notes].sort((a, b) => {
    let comparison = 0
    
    if (sortBy === 'block_height') {
      comparison = a.block_height - b.block_height
    } else if (sortBy === 'value') {
      comparison = a.value - b.value
    }
    
    return sortOrder === 'asc' ? comparison : -comparison
  })
  
  return sorted
}

// Create note item
function createNoteItem(note, index) {
  const noteDiv = document.createElement('div')
  noteDiv.className = 'border-b border-slate-100 last:border-b-0 note-item'
  
  const nockAmount = nickToNock(note.value)
  
  // ✅ Note row avec ID
  const header = document.createElement('div')
  header.id = `note-row-${index}` // ✅ AJOUTER L'ID ICI
  header.className = 'note-row flex justify-between items-center px-6 py-4 transition-all duration-200'
  
  header.innerHTML = `
    <div class="flex items-center gap-4 flex-1">
      <input type="checkbox" 
             id="checkbox-${index}" 
             class="note-checkbox w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
             onchange="window.handleNoteCheckboxChange(${index}, this.checked)">
      <div class="flex-1 cursor-pointer" onclick="window.toggleNoteDetails(${index})">
        <span class="text-sm text-slate-600 font-mono break-all">${truncateString(note.name, 50)}</span>
      </div>
    </div>
    <div class="flex items-center gap-6 ml-4 cursor-pointer" onclick="window.toggleNoteDetails(${index})">
      <span class="text-sm text-blue-600 font-medium bg-blue-50 px-3 py-1 rounded-full">Block: ${note.block_height}</span>
      <div class="text-right">
        <div class="mb-1">
          <span class="text-2xl font-bold text-green-600">${nockAmount}</span>
          <span class="text-sm text-slate-500 ml-1">nock</span>
        </div>
        <div>
          <span class="text-sm text-slate-600">${note.value.toLocaleString()}</span>
          <span class="text-xs text-slate-500 ml-1">nick</span>
        </div>
      </div>
      <svg id="arrow-${index}" class="w-5 h-5 text-slate-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
      </svg>
    </div>
  `
  
  // ✅ Details row avec ID correct
  const details = document.createElement('div')
  details.id = `note-details-${index}` // ✅ ID CORRECT
  details.className = 'hidden px-6 py-4 bg-slate-50 border-t border-slate-200 note-details-panel'
  details.innerHTML = `
    <div class="space-y-4 text-sm">
      <div>
        <span class="text-slate-600 font-medium">Full Name:</span>
        <p class="text-slate-800 font-mono break-all mt-2 bg-white p-3 rounded-lg border text-xs">${note.name}</p>
      </div>
      ${note.source ? `
      <div>
        <span class="text-slate-600 font-medium">Source:</span>
        <p class="text-slate-800 font-mono break-all mt-2 bg-white p-3 rounded-lg border text-xs">${note.source}</p>
      </div>
      ` : ''}
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white p-3 rounded-lg border">
          <span class="text-slate-600 font-medium text-xs">Block Height:</span>
          <span class="text-slate-800 ml-2 font-semibold">${note.block_height}</span>
        </div>
        <div class="bg-white p-3 rounded-lg border">
          <span class="text-slate-600 font-medium text-xs">Value:</span>
          <p class="text-slate-800 mt-1 font-semibold">
            ${nockAmount} nock<br>
            <span class="text-sm text-slate-600 font-normal">${note.value.toLocaleString()} nick</span>
          </p>
        </div>
      </div>
      <div>
        <span class="text-slate-600 font-medium">Signer:</span>
        <p class="text-slate-800 font-mono text-xs break-all mt-2 bg-white p-3 rounded-lg border">${note.signer}</p>
      </div>
    </div>
  `
  
  noteDiv.appendChild(header)
  noteDiv.appendChild(details)
  
  return noteDiv
}

// Render notes
export function renderNotes() {
  notesList.innerHTML = ''
  
  // Add sort controls
  const sortHeader = document.createElement('div')
  sortHeader.className = 'bg-slate-50 border-b border-slate-200 p-4 flex items-center justify-between'
  sortHeader.innerHTML = `
    <div class="text-sm text-slate-700 font-semibold">Sort by:</div>
    <div class="flex gap-3">
      <button id="sortByBlock" class="sort-btn ${sortBy === 'block_height' ? 'sort-active' : ''}">
        <span>Block Height</span>
        <svg class="w-4 h-4 ${sortBy === 'block_height' && sortOrder === 'asc' ? 'rotate-180' : ''} transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>
      <button id="sortByAmount" class="sort-btn ${sortBy === 'value' ? 'sort-active' : ''}">
        <span>Amount</span>
        <svg class="w-4 h-4 ${sortBy === 'value' && sortOrder === 'asc' ? 'rotate-180' : ''} transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>
    </div>
  `
  notesList.appendChild(sortHeader)
  
  // Sort buttons event listeners
  document.getElementById('sortByBlock').addEventListener('click', () => {
    if (sortBy === 'block_height') {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy = 'block_height'
      sortOrder = 'desc'
    }
    renderNotes()
  })
  
  document.getElementById('sortByAmount').addEventListener('click', () => {
    if (sortBy === 'value') {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy = 'value'
      sortOrder = 'desc'
    }
    renderNotes()
  })
  
  // Render sorted notes
  const sortedNotes = sortNotes(allNotes)
  sortedNotes.forEach((note) => {
    const index = allNotes.findIndex(n => n.name === note.name)
    const noteItem = createNoteItem(note, index)
    notesList.appendChild(noteItem)
    
    // Restore checkbox state
    const checkbox = document.getElementById(`checkbox-${index}`)
    if (checkbox && selectedNotes.has(index)) {
      checkbox.checked = true
    }
  })
  
  updateSendSelectedButton()
}

// ✅ Toggle note details - FONCTION CORRIGÉE
export function toggleNoteDetails(index) {
  console.log('🔍 Toggling note details for index:', index)
  
  const detailsRow = document.getElementById(`note-details-${index}`)
  const noteRow = document.getElementById(`note-row-${index}`)
  const arrow = document.getElementById(`arrow-${index}`)
  
  console.log('Details row:', detailsRow)
  console.log('Note row:', noteRow)
  
  if (detailsRow && noteRow) {
    if (detailsRow.classList.contains('hidden')) {
      // Show details
      console.log('✅ Showing details for note', index)
      detailsRow.classList.remove('hidden')
      detailsRow.classList.add('active')
      noteRow.classList.add('selected')
      if (arrow) {
        arrow.style.transform = 'rotate(180deg)'
      }
    } else {
      // Hide details
      console.log('❌ Hiding details for note', index)
      detailsRow.classList.add('hidden')
      detailsRow.classList.remove('active')
      noteRow.classList.remove('selected')
      if (arrow) {
        arrow.style.transform = 'rotate(0deg)'
      }
    }
  } else {
    console.error('❌ Elements not found for index', index)
  }
}

// Handle checkbox change
export function handleNoteCheckboxChange(index, checked) {
  console.log('📋 Checkbox changed for note', index, ':', checked)
  
  if (checked) {
    selectedNotes.add(index)
  } else {
    selectedNotes.delete(index)
  }
  updateSendSelectedButton()
}

// Update send selected button
export function updateSendSelectedButton() {
  sendSelectedBtn.disabled = selectedNotes.size === 0
  if (selectedNotes.size > 0) {
    const totalSelected = Array.from(selectedNotes).reduce((sum, index) => {
      return sum + allNotes[index].value
    }, 0)
    const totalNock = nickToNock(totalSelected)
    sendSelectedBtn.innerHTML = `
      <span class="btn-icon">💸</span>
      <span>Send Selected (${selectedNotes.size} notes - ${totalNock} nock)</span>
    `
  } else {
    sendSelectedBtn.innerHTML = `
      <span class="btn-icon">💸</span>
      <span>Send Selected</span>
    `
  }
}