// API base URL
const API_BASE = 'http://0.0.0.0:8000';

// Utility functions
function showMessage(elementId, message, isError = false) {
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML = `<div class="${isError ? 'error' : 'success'}">${message}</div>`;
    setTimeout(() => element.innerHTML = '', 5000);
  }
}

function showLoading(elementId, isLoading = true) {
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML = isLoading ? '<div class="loading">Processing...</div>' : '';
  }
}

// PDF Upload functionality
document.getElementById('pdfUploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const fileInput = document.getElementById('pdfFile');
  const file = fileInput.files[0];
  
  if (!file) {
    showMessage('uploadStatus', 'Please select a PDF file', true);
    return;
  }
  
  const formData = new FormData();
  formData.append('file', file);
  
  showLoading('uploadStatus', true);
  
  try {
    const response = await fetch('/upload-pdf', {
      method: 'POST',
      body: formData
    });
    
    if (response.ok) {
      const result = await response.json();
      showMessage('uploadStatus', 
        `PDF parsed successfully! Found ${result.toc_count} TOC entries and ${result.sections_count} sections.`);
      
      // Auto-load the data
      setTimeout(() => {
        loadTOC();
        loadSections();
        getStats();
      }, 1000);
      
    } else {
      const error = await response.json();
      showMessage('uploadStatus', `Error: ${error.detail}`, true);
    }
  } catch (error) {
    showMessage('uploadStatus', `Network error: ${error.message}`, true);
  }
});

// Load TOC data
async function loadTOC() {
  try {
    const response = await fetch('/api/toc');
    if (response.ok) {
      const data = await response.json();
      populateTOCTable(data.toc_entries);
      showMessage('uploadStatus', `Loaded ${data.total_count} TOC entries`);
    } else {
      const error = await response.json();
      showMessage('uploadStatus', `Error loading TOC: ${error.detail}`, true);
    }
  } catch (error) {
    showMessage('uploadStatus', `Error: ${error.message}`, true);
  }
}

// Load Sections data
async function loadSections() {
  try {
    const response = await fetch('/api/sections');
    if (response.ok) {
      const data = await response.json();
      populateSectionTable(data.sections);
      showMessage('uploadStatus', `Loaded ${data.total_count} sections`);
    } else {
      const error = await response.json();
      showMessage('uploadStatus', `Error loading sections: ${error.detail}`, true);
    }
  } catch (error) {
    showMessage('uploadStatus', `Error: ${error.message}`, true);
  }
}

// Search sections
async function searchSections() {
  const query = document.getElementById('searchQuery').value.trim();
  const limit = document.getElementById('searchLimit').value;
  
  if (!query) {
    showMessage('searchResults', 'Please enter a search term', true);
    return;
  }
  
  try {
    const response = await fetch(`/api/search?query=${encodeURIComponent(query)}&limit=${limit}`);
    if (response.ok) {
      const data = await response.json();
      displaySearchResults(data);
    } else {
      const error = await response.json();
      showMessage('searchResults', `Error: ${error.detail}`, true);
    }
  } catch (error) {
    showMessage('searchResults', `Error: ${error.message}`, true);
  }
}

// Display search results
function displaySearchResults(data) {
  const resultsDiv = document.getElementById('searchResults');
  
  if (data.total_found === 0) {
    resultsDiv.innerHTML = '<p>No results found for your search.</p>';
    return;
  }
  
  let html = `<h3>Search Results for "${data.query}" (${data.total_found} found)</h3>`;
  html += '<div class="search-results">';
  
  data.results.forEach(result => {
    html += `
      <div class="search-result">
        <h4>${result.section_id}: ${result.title}</h4>
        <p><strong>Page:</strong> ${result.page}</p>
        <p><strong>Content:</strong> ${result.content_preview}</p>
      </div>
    `;
  });
  
  html += '</div>';
  resultsDiv.innerHTML = html;
}

// Get statistics
async function getStats() {
  try {
    const response = await fetch('/api/stats');
    if (response.ok) {
      const data = await response.json();
      displayStats(data);
    } else {
      const error = await response.json();
      showMessage('statsDisplay', `Error: ${error.detail}`, true);
    }
  } catch (error) {
    showMessage('statsDisplay', `Error: ${error.message}`, true);
  }
}

// Display statistics
function displayStats(data) {
  const statsDiv = document.getElementById('statsDisplay');
  
  if (data.status === 'No data') {
    statsDiv.innerHTML = '<p>No data available. Please upload a PDF first.</p>';
    return;
  }
  
  let html = `
    <div class="stats-grid">
      <div class="stat-item">
        <h4>TOC Entries</h4>
        <p>${data.toc_entries_count}</p>
      </div>
      <div class="stat-item">
        <h4>Sections</h4>
        <p>${data.sections_count}</p>
      </div>
      <div class="stat-item">
        <h4>Current PDF</h4>
        <p>${data.current_pdf ? data.current_pdf.split('/').pop() : 'None'}</p>
      </div>
    </div>
  `;
  
  if (data.toc_levels_distribution) {
    html += '<h4>TOC Level Distribution:</h4><ul>';
    Object.entries(data.toc_levels_distribution).forEach(([level, count]) => {
      html += `<li>Level ${level}: ${count} entries</li>`;
    });
    html += '</ul>';
  }
  
  statsDiv.innerHTML = html;
}

// Export functions
async function exportTOC() {
  try {
    const response = await fetch('/api/export/toc');
    if (response.ok) {
      const data = await response.json();
      downloadJSON(data, 'toc_export.json');
    } else {
      const error = await response.json();
      showMessage('uploadStatus', `Error: ${error.detail}`, true);
    }
  } catch (error) {
    showMessage('uploadStatus', `Error: ${error.message}`, true);
  }
}

async function exportSections() {
  try {
    const response = await fetch('/api/export/sections');
    if (response.ok) {
      const data = await response.json();
      downloadJSON(data, 'sections_export.json');
    } else {
      const error = await response.json();
      showMessage('uploadStatus', `Error: ${error.detail}`, true);
    }
  } catch (error) {
    showMessage('uploadStatus', `Error: ${error.message}`, true);
  }
}

// Download JSON helper
function downloadJSON(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Clear all data
async function clearData() {
  if (!confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
    return;
  }
  
  try {
    const response = await fetch('/api/clear', { method: 'DELETE' });
    if (response.ok) {
      const result = await response.json();
      showMessage('uploadStatus', result.message);
      
      // Clear tables
      document.querySelector('#tocTable tbody').innerHTML = '';
      document.querySelector('#sectionTable tbody').innerHTML = '';
      document.getElementById('searchResults').innerHTML = '';
      document.getElementById('statsDisplay').innerHTML = '';
      
      // Reset file input
      document.getElementById('pdfFile').value = '';
    } else {
      const error = await response.json();
      showMessage('uploadStatus', `Error: ${error.detail}`, true);
    }
  } catch (error) {
    showMessage('uploadStatus', `Error: ${error.message}`, true);
  }
}

// Populate TOC table
function populateTOCTable(data) {
  const tbody = document.querySelector("#tocTable tbody");
  tbody.innerHTML = "";
  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.section_id || ''}</td>
      <td>${row.title || ''}</td>
      <td>${row.page || ''}</td>
      <td>${row.level || ''}</td>
      <td>${row.tags ? row.tags.join(", ") : ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Populate Sections table
function populateSectionTable(data) {
  const tbody = document.querySelector("#sectionTable tbody");
  tbody.innerHTML = "";
  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.section_id || ''}</td>
      <td>${row.title || ''}</td>
      <td>${row.page || ''}</td>
      <td>${row.content ? (row.content.substring(0, 200) + (row.content.length > 200 ? '...' : '')) : ''}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
  // Check if there's existing data
  getStats();
});
