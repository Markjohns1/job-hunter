const state = {
    currentJobId: null,
    selectedJobs: new Set(),
    currentFilters: { status: 'all', source: 'all', sort: 'relevance' },
    jobs: [],
    abortController: null
};

document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initializing...');
    initializeDashboard();
    setupEventListeners();
});

async function initializeDashboard() {
    try {
        await loadDashboard();
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        showError('Failed to initialize dashboard');
    }
}

function setupEventListeners() {
    const addJobForm = document.getElementById('add-job-form');
    if (addJobForm) {
        addJobForm.addEventListener('submit', handleAddJobSubmit);
    }

    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    document.addEventListener('keydown', handleKeyboardShortcuts);
}

function handleKeyboardShortcuts(e) {
    if (e.key === 'Escape') {
        closeModal();
        closeAddJobModal();
    }
    
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openAddJobModal();
    }
}

async function loadDashboard() {
    await Promise.all([
        loadJobs(state.currentFilters),
        loadStats()
    ]);
}

async function loadJobs(filters = {}) {
    console.log('Loading jobs with filters:', filters);
    
    if (state.abortController) {
        state.abortController.abort();
    }
    state.abortController = new AbortController();
    
    showLoading(true, 'Loading jobs...');
    
    try {
        const data = await API.getJobs(filters);
        console.log('Jobs loaded:', data);
        
        const jobsList = Array.isArray(data?.jobs) ? data.jobs : [];
        state.jobs = jobsList;
        displayJobs(jobsList);
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('Failed to load jobs:', error);
            showError('Failed to load jobs: ' + error.message);
            displayJobs([]);
        }
    } finally {
        showLoading(false);
    }
}

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
                    <div style="color: var(--text-secondary); display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 1rem;">
                        <i class="fas fa-inbox" style="font-size: 48px; opacity: 0.5;"></i>
                        <h3 style="margin: 0;">No jobs found</h3>
                        <p style="margin: 0;">Click "Scrape Jobs" to find fresh opportunities or add jobs manually</p>
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
}

function createJobRow(job) {
    const row = document.createElement('tr');
    const relevanceScore = job.relevance_score ? Math.round(job.relevance_score) : 0;
    
    let relevanceColor = '#e4163a';
    if (relevanceScore >= 70) relevanceColor = '#31a24c';
    else if (relevanceScore >= 40) relevanceColor = '#f59e0b';
    
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
            <span class="status" style="display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; background: ${getStatusColor(job.status).bg}; color: ${getStatusColor(job.status).text};">
                ${escapeHtml(job.status || 'Found')}
            </span>
        </td>
        <td>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                ${job.status === 'Found' ? `
                    <button onclick="applyToJob(${job.id})" class="btn btn-sm btn-primary">
                        <i class="fas fa-paper-plane"></i> Apply
                    </button>
                ` : ''}
                <a href="${escapeHtml(job.url || '#')}" target="_blank" class="btn btn-sm btn-secondary">
                    <i class="fas fa-external-link-alt"></i> Open
                </a>
                <button onclick="deleteJob(${job.id})" class="btn btn-sm btn-danger">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </td>
    `;
    
    return row;
}

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

async function loadStats() {
    try {
        const data = await API.getStats();
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

function updateStatDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.transition = 'transform 0.2s';
        element.style.transform = 'scale(1.1)';
        element.textContent = value;
        setTimeout(() => { element.style.transform = 'scale(1)'; }, 200);
    }
}

async function scrapeJobs() {
    if (!confirm('Start scraping fresh jobs? This may take a few minutes.')) return;
    showLoading(true, 'Scraping jobs from multiple sources...');
    
    try {
        const data = await API.scrapeJobs();
        if (data.success) {
            showSuccess('Found ' + data.jobs_found + ' new jobs!');
            await loadDashboard();
        } else {
            showError(data.error || 'Scraping failed');
        }
    } catch (error) {
        showError('Scraping failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function applyToJob(jobId) {
    state.currentJobId = jobId;
    showLoading(true, 'Generating personalized cover letter with AI...');
    
    try {
        const response = await fetch(`/api/apply/${jobId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        
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
        showError('Failed to generate cover letter: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function confirmApply() {
    if (!state.currentJobId) return;
    
    const coverLetter = document.getElementById('cover-letter-text')?.value;
    const recipientEmail = document.getElementById('recipient-email')?.value.trim();
    
    if (!coverLetter || !coverLetter.trim()) {
        showError('Cover letter cannot be empty');
        return;
    }
    
    const sendingEmail = recipientEmail && recipientEmail.length > 0;
    
    if (sendingEmail) {
        showLoading(true, 'Sending application via email...');
        try {
            const response = await fetch(`/api/apply/${state.currentJobId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    send_email: true,
                    recipient_email: recipientEmail,
                    cover_letter: coverLetter
                })
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            if (data.success && data.email_sent) {
                showSuccess('Application sent via email!');
                await updateJobStatus(state.currentJobId, 'Applied', coverLetter);
                closeModal();
                await loadDashboard();
            } else {
                showError(data.error || 'Failed to send email');
            }
        } catch (error) {
            showError('Failed to send email: ' + error.message);
        } finally {
            showLoading(false);
        }
    } else {
        showLoading(true, 'Tracking application...');
        try {
            await updateJobStatus(state.currentJobId, 'Applied', coverLetter);
            showSuccess('Application tracked');
            closeModal();
            await loadDashboard();
        } catch (error) {
            showError('Failed to track application: ' + error.message);
        } finally {
            showLoading(false);
        }
    }
}

async function updateJobStatus(jobId, status, coverLetter) {
    const response = await fetch(`/api/job/${jobId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, cover_letter: coverLetter })
    });
    
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
}

async function deleteJob(jobId) {
    if (!confirm('Delete this job?')) return;
    showLoading(true, 'Deleting job...');
    
    try {
        const response = await fetch(`/api/job/${jobId}`, { method: 'DELETE' });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('Job deleted');
            state.selectedJobs.delete(jobId);
            await loadDashboard();
        } else {
            showError(data.error || 'Delete failed');
        }
    } catch (error) {
        showError('Delete failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function filterJobs() {
    const status = document.getElementById('filter-status')?.value || 'all';
    const source = document.getElementById('filter-source')?.value || 'all';
    const sort = document.getElementById('sort-by')?.value || 'relevance';
    state.currentFilters = { status, source, sort };
    loadJobs(state.currentFilters);
}

function handleCheckboxChange(jobId, checked) {
    if (checked) {
        state.selectedJobs.add(jobId);
    } else {
        state.selectedJobs.delete(jobId);
    }
    updateBulkActionsBar();
    updateSelectAllCheckbox();
}

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

function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all');
    const allCheckboxes = document.querySelectorAll('.job-checkbox');
    const checkedCheckboxes = document.querySelectorAll('.job-checkbox:checked');
    
    if (selectAllCheckbox && allCheckboxes.length > 0) {
        selectAllCheckbox.checked = allCheckboxes.length === checkedCheckboxes.length;
        selectAllCheckbox.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < allCheckboxes.length;
    }
}

function updateBulkActionsBar() {
    const bar = document.getElementById('bulk-actions-bar');
    const count = document.getElementById('selected-count');
    
    if (bar && count) {
        if (state.selectedJobs.size > 0) {
            bar.classList.add('active');
            count.textContent = state.selectedJobs.size + ' job' + (state.selectedJobs.size > 1 ? 's' : '') + ' selected';
        } else {
            bar.classList.remove('active');
        }
    }
}

async function bulkDeleteJobs() {
    if (state.selectedJobs.size === 0) return;
    if (!confirm('Delete ' + state.selectedJobs.size + ' jobs?')) return;
    
    showLoading(true, 'Deleting jobs...');
    try {
        const deletePromises = Array.from(state.selectedJobs).map(jobId =>
            fetch(`/api/job/${jobId}`, { method: 'DELETE' })
                .then(res => res.json())
                .catch(err => ({ success: false, error: err.message }))
        );
        await Promise.all(deletePromises);
        showSuccess(state.selectedJobs.size + ' job(s) deleted');
        clearSelection();
        await loadDashboard();
    } catch (error) {
        showError('Failed to delete some jobs');
    } finally {
        showLoading(false);
    }
}

function clearSelection() {
    state.selectedJobs.clear();
    document.querySelectorAll('.job-checkbox').forEach(cb => cb.checked = false);
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
    updateBulkActionsBar();
}

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

async function extractJobFromUrl() {
    const urlInput = document.getElementById('job-url');
    const url = urlInput?.value;
    
    if (!url || !url.trim()) {
        showError('Please enter a job URL first');
        urlInput?.focus();
        return;
    }
    
    showLoading(true, 'Extracting job details...');
    try {
        const response = await fetch('/api/extract-job', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url.trim() })
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success && data.job) {
            document.getElementById('job-title').value = data.job.title || '';
            document.getElementById('job-company').value = data.job.company || '';
            document.getElementById('job-location').value = data.job.location || 'Kenya';
            document.getElementById('job-description').value = data.job.description || '';
            showSuccess('Job details extracted!');
        } else {
            showError('Could not extract job details. Please fill manually.');
        }
    } catch (error) {
        showError('Extraction failed. Please fill manually.');
    } finally {
        showLoading(false);
    }
}

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
    
    if (!jobData.title || !jobData.company || !jobData.url) {
        showError('Please fill in all required fields');
        return;
    }
    
    showLoading(true, 'Adding job...');
    try {
        const response = await fetch('/api/job', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobData)
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        if (data.success) {
            showSuccess('Job added successfully');
            closeAddJobModal();
            await loadDashboard();
        } else {
            showError(data.error || 'Failed to add job');
        }
    } catch (error) {
        showError('Failed to add job: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function exportJobs() {
    if (typeof API !== 'undefined' && API.exportJobs) {
        API.exportJobs();
    } else {
        window.location.href = '/api/export';
    }
}

function showLoading(show, message) {
    const loading = document.getElementById('loading');
    if (!loading) return;
    if (show) {
        const text = loading.querySelector('.loading-text');
        if (text) text.textContent = message || 'Loading...';
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

function showNotification(message, type) {
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