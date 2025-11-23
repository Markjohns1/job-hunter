// Job Hunter Dashboard - Enhanced JavaScript
// State Management
const state = {
    currentJobId: null,
    selectedJobs: new Set(),
    currentFilters: { status: 'all', source: 'all', sort: 'relevance' },
    jobs: []
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initializing...');
    initializeDashboard();
    setupEventListeners();
});

// Initialize Dashboard
async function initializeDashboard() {
    try {
        await loadDashboard();
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        showError('Failed to initialize dashboard');
    }
}

// Setup all event listeners
function setupEventListeners() {
    // Form submission
    const addJobForm = document.getElementById('add-job-form');
    if (addJobForm) {
        addJobForm.addEventListener('submit', handleAddJobSubmit);
    }

    // Modal close on outside click
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

// Keyboard shortcuts handler
function handleKeyboardShortcuts(e) {
    // ESC to close modals
    if (e.key === 'Escape') {
        closeModal();
        closeAddJobModal();
    }
    
    // Ctrl/Cmd + K to open add job modal
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openAddJobModal();
    }
}

// Load Dashboard Data
async function loadDashboard() {
    await Promise.all([
        loadJobs(state.currentFilters),
        loadStats()
    ]);
}

// Load Jobs with Filters
async function loadJobs(filters = {}) {
    console.log('Loading jobs with filters:', filters);
    showLoading(true, 'Loading jobs...');
    
    try {
        const data = await API.getJobs(filters);
        console.log('Jobs loaded:', data);
        
        if (data && data.jobs) {
            state.jobs = data.jobs;
            displayJobs(data.jobs);
        } else {
            console.error('Invalid data format:', data);
            showError('Invalid response format');
            displayJobs([]);
        }
    } catch (error) {
        console.error('Failed to load jobs:', error);
        showError('Failed to load jobs: ' + error.message);
        displayJobs([]);
    } finally {
        showLoading(false);
    }
}

// Display Jobs in Table
function displayJobs(jobs) {
    console.log('Displaying jobs:', jobs.length);
    const tbody = document.getElementById('jobs-tbody') || document.querySelector('tbody');
    
    if (!tbody) {
        console.error('Table body not found in DOM');
        return;
    }
    
    tbody.innerHTML = '';
    
    if (!jobs || jobs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 3rem;">
                    <div style="color: var(--text-secondary); justify-content: center; align-items: center;">
                        <i class="fas fa-inbox" style="font-size: 48px; margin-bottom: 1rem; opacity: 0.5;"></i>
                        <h3 style="margin-bottom: 0.5rem;">No jobs found</h3>
                        <p>Click "Scrape Jobs" to find fresh opportunities or add jobs manually</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    jobs.forEach(job => {
        const row = createJobRow(job);
        tbody.appendChild(row);
    });
    
    console.log('Jobs displayed successfully');
}

// Create Job Row
function createJobRow(job) {
    const row = document.createElement('tr');
    const statusClass = job.status ? job.status.toLowerCase() : 'found';
    const relevanceScore = job.relevance_score ? Math.round(job.relevance_score) : 0;
    
    // Determine relevance color
    let relevanceColor = '#e4163a'; // red
    if (relevanceScore >= 70) relevanceColor = '#31a24c'; // green
    else if (relevanceScore >= 40) relevanceColor = '#f59e0b'; // orange
    
    row.innerHTML = `
        <td style="text-align: center;">
            <input type="checkbox" 
                   class="job-checkbox" 
                   data-job-id="${job.id}"
                   ${state.selectedJobs.has(job.id) ? 'checked' : ''}
                   onchange="handleCheckboxChange(${job.id}, this.checked)">
        </td>
        <td>
            <div style="line-height: 1.4;">
                <strong style="display: block; margin-bottom: 4px;">${escapeHtml(job.title || 'Untitled')}</strong>
                <small style="color: var(--text-secondary);">
                    <i class="fas fa-map-marker-alt" style="width: 12px;"></i> ${escapeHtml(job.location || 'Remote')}
                </small>
            </div>
        </td>
        <td>${escapeHtml(job.company || 'Unknown')}</td>
        <td>
            <span class="badge" style="background: var(--bg-tertiary); color: var(--text-secondary);">
                ${escapeHtml(job.source || 'Manual')}
            </span>
        </td>
        <td>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div class="progress-bar" style="flex: 1; height: 8px; background: var(--bg-tertiary); border-radius: 4px; overflow: hidden;">
                    <div class="progress-fill" style="width: ${relevanceScore}%; height: 100%; background: ${relevanceColor}; transition: width 0.3s;"></div>
                </div>
                <span style="font-size: 13px; font-weight: 600; min-width: 35px;">${relevanceScore}%</span>
            </div>
        </td>
        <td>
            <span class="status status-${statusClass}" style="display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; background: ${getStatusColor(job.status).bg}; color: ${getStatusColor(job.status).text};">
                ${escapeHtml(job.status || 'Found')}
            </span>
        </td>
        <td>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                ${job.status === 'Found' ? `
                    <button onclick="applyToJob(${job.id})" class="btn btn-sm btn-primary" title="Apply to this job">
                        <i class="fas fa-paper-plane"></i> Apply
                    </button>
                ` : ''}
                <a href="${escapeHtml(job.url || '#')}" target="_blank" class="btn btn-sm btn-secondary" title="Open job posting">
                    <i class="fas fa-external-link-alt"></i> Open
                </a>
                <button onclick="deleteJob(${job.id})" class="btn btn-sm btn-danger" title="Delete job">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </td>
    `;
    
    return row;
}

// Get status colors
function getStatusColor(status) {
    const colors = {
        'found': { bg: 'rgba(35, 116, 225, 0.2)', text: '#2374e1' },
        'applied': { bg: 'rgba(49, 162, 76, 0.2)', text: '#31a24c' },
        'interview': { bg: 'rgba(245, 158, 11, 0.2)', text: '#f59e0b' },
        'offer': { bg: 'rgba(139, 92, 246, 0.2)', text: '#8b5cf6' },
        'rejected': { bg: 'rgba(228, 22, 58, 0.2)', text: '#e4163a' }
    };
    return colors[status?.toLowerCase()] || colors.found;
}

// Load Statistics
async function loadStats() {
    console.log('Loading stats...');
    try {
        const data = await API.getStats();
        console.log('Stats loaded:', data);
        
        if (data && data.stats) {
            updateStatDisplay('stat-total', data.stats.total_jobs_found || 0);
            updateStatDisplay('stat-applied', data.stats.jobs_applied || 0);
            updateStatDisplay('stat-pending', data.stats.pending_applications || 0);
            updateStatDisplay('stat-response', (data.stats.response_rate || 0) + '%');
        }
    } catch (error) {
        console.error('Stats error:', error);
    }
}

// Animate stat value update
function updateStatDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.transition = 'transform 0.2s';
        element.style.transform = 'scale(1.1)';
        element.textContent = value;
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
}

// Scrape Jobs
async function scrapeJobs() {
    if (!confirm('Start scraping fresh jobs from job boards? This may take a few minutes.')) return;
    
    showLoading(true, 'Scraping jobs from multiple sources...');
    
    try {
        const data = await API.scrapeJobs();
        console.log('Scrape result:', data);
        
        if (data.success) {
            showSuccess(`✓ Found ${data.jobs_found} new jobs!`);
            await loadDashboard();
        } else {
            showError(data.error || 'Scraping failed');
        }
    } catch (error) {
        console.error('Scraping error:', error);
        showError('Scraping failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Apply to Job
async function applyToJob(jobId) {
    state.currentJobId = jobId;
    
    showLoading(true, 'Generating personalized cover letter with AI...');
    
    try {
        const data = await API.applyToJob(jobId);
        
        if (data.success) {
            const textarea = document.getElementById('cover-letter-text');
            if (textarea) {
                textarea.value = data.cover_letter;
                document.getElementById('cover-letter-modal').classList.add('active');
            }
        } else {
            showError(data.error || 'Failed to generate cover letter');
        }
    } catch (error) {
        console.error('Apply error:', error);
        showError('Failed to generate cover letter: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Confirm Application
async function confirmApply() {
    if (!state.currentJobId) return;
    
    const coverLetter = document.getElementById('cover-letter-text')?.value;
    
    if (!coverLetter || !coverLetter.trim()) {
        showError('Cover letter cannot be empty');
        return;
    }
    
    showLoading(true, 'Submitting application...');
    
    try {
        const response = await fetch(`/api/job/${state.currentJobId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                status: 'Applied', 
                cover_letter: coverLetter 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('✓ Application submitted successfully!');
            closeModal();
            await loadDashboard();
        } else {
            showError(data.error || 'Failed to submit application');
        }
    } catch (error) {
        console.error('Submit error:', error);
        showError('Failed to submit application: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Delete Job
async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) return;
    
    showLoading(true, 'Deleting job...');
    
    try {
        const response = await fetch(`/api/job/${jobId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess('✓ Job deleted');
            state.selectedJobs.delete(jobId);
            await loadDashboard();
        } else {
            showError(data.error || 'Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showError('Delete failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Filter Jobs
function filterJobs() {
    const status = document.getElementById('filter-status')?.value || 'all';
    const source = document.getElementById('filter-source')?.value || 'all';
    const sort = document.getElementById('sort-by')?.value || 'relevance';
    
    state.currentFilters = { status, source, sort };
    loadJobs(state.currentFilters);
}

// Checkbox Handling
function handleCheckboxChange(jobId, checked) {
    if (checked) {
        state.selectedJobs.add(jobId);
    } else {
        state.selectedJobs.delete(jobId);
    }
    updateBulkActionsBar();
    updateSelectAllCheckbox();
}

// Toggle Select All
function toggleSelectAll(checked) {
    const checkboxes = document.querySelectorAll('.job-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = checked;
        const jobId = parseInt(checkbox.dataset.jobId);
        if (checked) {
            state.selectedJobs.add(jobId);
        } else {
            state.selectedJobs.delete(jobId);
        }
    });
    updateBulkActionsBar();
}

// Update Select All Checkbox
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all');
    const allCheckboxes = document.querySelectorAll('.job-checkbox');
    const checkedCheckboxes = document.querySelectorAll('.job-checkbox:checked');
    
    if (selectAllCheckbox && allCheckboxes.length > 0) {
        selectAllCheckbox.checked = allCheckboxes.length === checkedCheckboxes.length;
        selectAllCheckbox.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < allCheckboxes.length;
    }
}

// Update Bulk Actions Bar
function updateBulkActionsBar() {
    const bar = document.getElementById('bulk-actions-bar');
    const count = document.getElementById('selected-count');
    
    if (bar && count) {
        if (state.selectedJobs.size > 0) {
            bar.classList.add('active');
            count.textContent = `${state.selectedJobs.size} job${state.selectedJobs.size > 1 ? 's' : ''} selected`;
        } else {
            bar.classList.remove('active');
        }
    }
}

// Bulk Delete Jobs
async function bulkDeleteJobs() {
    if (state.selectedJobs.size === 0) return;
    
    if (!confirm(`Delete ${state.selectedJobs.size} selected job${state.selectedJobs.size > 1 ? 's' : ''}? This action cannot be undone.`)) return;
    
    showLoading(true, `Deleting ${state.selectedJobs.size} jobs...`);
    
    try {
        const deletePromises = Array.from(state.selectedJobs).map(jobId =>
            fetch(`/api/job/${jobId}`, { method: 'DELETE' })
        );
        
        await Promise.all(deletePromises);
        showSuccess(`✓ ${state.selectedJobs.size} job${state.selectedJobs.size > 1 ? 's' : ''} deleted successfully`);
        clearSelection();
        await loadDashboard();
    } catch (error) {
        console.error('Bulk delete error:', error);
        showError('Failed to delete some jobs');
    } finally {
        showLoading(false);
    }
}

// Clear Selection
function clearSelection() {
    state.selectedJobs.clear();
    const checkboxes = document.querySelectorAll('.job-checkbox');
    checkboxes.forEach(checkbox => checkbox.checked = false);
    
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
    
    updateBulkActionsBar();
}

// Modal Functions
function openAddJobModal() {
    document.getElementById('add-job-modal')?.classList.add('active');
    document.getElementById('job-url')?.focus();
}

function closeAddJobModal() {
    document.getElementById('add-job-modal')?.classList.remove('active');
    document.getElementById('add-job-form')?.reset();
}

function closeModal() {
    document.getElementById('cover-letter-modal')?.classList.remove('active');
    state.currentJobId = null;
}

// Extract Job from URL
async function extractJobFromUrl() {
    const urlInput = document.getElementById('job-url');
    const url = urlInput?.value;
    
    if (!url || !url.trim()) {
        showError('Please enter a job URL first');
        urlInput?.focus();
        return;
    }
    
    showLoading(true, 'Extracting job details from URL...');
    
    try {
        const response = await fetch('/api/extract-job', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url.trim() })
        });
        
        const data = await response.json();
        
        if (data.success && data.job) {
            document.getElementById('job-title').value = data.job.title || '';
            document.getElementById('job-company').value = data.job.company || '';
            document.getElementById('job-location').value = data.job.location || 'Kenya';
            document.getElementById('job-description').value = data.job.description || '';
            showSuccess('✓ Job details extracted! Review and save.');
        } else {
            showError('Could not extract job details. Please fill manually.');
        }
    } catch (error) {
        console.error('Extract error:', error);
        showError('Extraction failed. Please fill manually.');
    } finally {
        showLoading(false);
    }
}

// Handle Add Job Form Submission
async function handleAddJobSubmit(e) {
    e.preventDefault();
    
    const jobData = {
        title: document.getElementById('job-title')?.value.trim(),
        company: document.getElementById('job-company')?.value.trim(),
        location: document.getElementById('job-location')?.value.trim() || 'Kenya',
        url: document.getElementById('job-url')?.value.trim(),
        description: document.getElementById('job-description')?.value.trim(),
        source: 'Manual'
    };
    
    // Validation
    if (!jobData.title || !jobData.company || !jobData.url) {
        showError('Please fill in all required fields (Title, Company, URL)');
        return;
    }
    
    showLoading(true, 'Adding job...');
    
    try {
        const response = await fetch('/api/job', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('✓ Job added successfully');
            closeAddJobModal();
            await loadDashboard();
        } else {
            showError(data.error || 'Failed to add job');
        }
    } catch (error) {
        console.error('Add job error:', error);
        showError('Failed to add job: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Export Jobs
function exportJobs() {
    if (typeof API !== 'undefined' && API.exportJobs) {
        API.exportJobs();
    } else {
        window.location.href = '/api/export';
    }
}

// UI Helper Functions
function showLoading(show, message = 'Loading...') {
    const loading = document.getElementById('loading');
    if (!loading) return;
    if (show) {
        loading.querySelector('.loading-text').textContent = message;
        loading.classList.add('active');
    } else {
        loading.classList.remove('active');
    }
}


function showSuccess(message) {
    console.log('Success:', message);
    showNotification(message, 'success');
}

function showError(message) {
    console.error('Error:', message);
    showNotification(message, 'error');
}

function showNotification(message, type = 'info') {
    // Simple notification - can be replaced with a better notification system
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 70px;
        right: 20px;
        background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : 'var(--accent)'};
        color: white;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        max-width: 400px;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);