/**
 * JobHunterPro - Dashboard Logic
 * Handles dashboard UI interactions and data display
 */

// Global state
let currentJobId = null;
let allJobs = [];

/**
 * Initialize dashboard
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized');
    loadDashboard();
});

/**
 * Load all dashboard data
 */
async function loadDashboard() {
    await Promise.all([
        loadJobs(),
        loadStats()
    ]);
}

/**
 * Load jobs from API
 */
async function loadJobs() {
    const statusFilter = document.getElementById('filter-status').value;
    const sourceFilter = document.getElementById('filter-source').value;
    const sortBy = document.getElementById('sort-by').value;

    showLoading(true);

    try {
        const data = await API.getJobs({
            status: statusFilter,
            source: sourceFilter,
            sort: sortBy
        });

        console.log(`Loaded ${data.jobs.length} jobs`);
        allJobs = data.jobs;
        displayJobs(data.jobs);
    } catch (error) {
        showError('Failed to load jobs. Please try again.');
    } finally {
        showLoading(false);
    }
}

/**
 * Display jobs in table
 */
function displayJobs(jobs) {
    const tbody = document.getElementById('jobs-tbody');
    tbody.innerHTML = '';

    if (jobs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <h3>No jobs found yet</h3>
                    <p>Click "Scrape Jobs" to start finding opportunities!</p>
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

/**
 * Create job table row
 */
function createJobRow(job) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            <div class="job-title">${escapeHtml(job.title)}</div>
            <div class="job-company">${escapeHtml(job.location || 'N/A')}</div>
        </td>
        <td>${escapeHtml(job.company)}</td>
        <td><span class="badge badge-found">${escapeHtml(job.source)}</span></td>
        <td>
            <div class="relevance-score">
                <span>${Math.round(job.relevance_score)}%</span>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${job.relevance_score}%"></div>
                </div>
            </div>
        </td>
        <td><span class="badge badge-${job.status.toLowerCase()}">${escapeHtml(job.status)}</span></td>
        <td>
            <div class="action-btns">
                ${job.status === 'Found' ? 
                    `<button class="btn btn-success btn-sm" onclick="applyToJob(${job.id})">
                        <i class="fas fa-paper-plane"></i> Apply
                    </button>` : 
                    `<button class="btn btn-info btn-sm" onclick="viewJobDetails(${job.id})">
                        <i class="fas fa-eye"></i> View
                    </button>`
                }
                <a href="${escapeHtml(job.url)}" target="_blank" class="btn btn-info btn-sm" title="Open job page">
                    <i class="fas fa-external-link-alt"></i>
                </a>
            </div>
        </td>
    `;
    return row;
}

/**
 * Load dashboard statistics
 */
async function loadStats() {
    try {
        const data = await API.getStats();
        updateStatsDisplay(data.stats);
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

/**
 * Update stats display
 */
function updateStatsDisplay(stats) {
    document.getElementById('stat-total').textContent = stats.total_jobs_found;
    document.getElementById('stat-applied').textContent = stats.jobs_applied;
    document.getElementById('stat-pending').textContent = stats.pending_applications;
    document.getElementById('stat-response').textContent = stats.response_rate + '%';
}

/**
 * Scrape jobs
 */
async function scrapeJobs() {
    if (!confirm('Start scraping job boards? This may take a few minutes.')) return;

    const btn = event.target.closest('button');
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping...';

    try {
        const data = await API.scrapeJobs();
        
        if (data.success) {
            showSuccess(`Found ${data.jobs_found} new jobs!`);
            await loadDashboard();
        } else {
            showError(data.error || 'Scraping failed');
        }
    } catch (error) {
        showError('Failed to scrape jobs. Please try again.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
    }
}

/**
 * Apply to job
 */
async function applyToJob(jobId) {
    currentJobId = jobId;

    try {
        const data = await API.applyToJob(jobId);

        if (data.success) {
            showCoverLetterModal(data.cover_letter, jobId);
        } else {
            showError(data.error || 'Failed to generate cover letter');
        }
    } catch (error) {
        showError('Failed to apply to job. Please try again.');
    }
}

/**
 * Show cover letter modal
 */
function showCoverLetterModal(coverLetter, jobId) {
    document.getElementById('cover-letter-text').textContent = coverLetter;
    document.getElementById('cover-letter-modal').classList.add('active');
    currentJobId = jobId;
}

/**
 * Confirm application
 */
async function confirmApply() {
    showSuccess('Application submitted successfully!');
    closeModal();
    await loadDashboard();
}

/**
 * View job details
 */
async function viewJobDetails(jobId) {
    try {
        const data = await API.getJobDetails(jobId);
        
        // Show job details in modal or navigate
        alert(`Job: ${data.job.title}\nCompany: ${data.job.company}\n\nOpening job page...`);
        window.open(data.job.url, '_blank');
    } catch (error) {
        showError('Failed to load job details');
    }
}

/**
 * Filter jobs
 */
function filterJobs() {
    loadJobs();
}

/**
 * Export jobs
 */
function exportJobs() {
    API.exportJobs();
}

/**
 * Close modal
 */
function closeModal() {
    document.getElementById('cover-letter-modal').classList.remove('active');
    currentJobId = null;
}

/**
 * Show loading state
 */
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.add('active');
    } else {
        loading.classList.remove('active');
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    alert(message); // Replace with toast notification
}

/**
 * Show error message
 */
function showError(message) {
    alert('Error: ' + message); // Replace with toast notification
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}