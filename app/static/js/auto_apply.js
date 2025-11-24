const autoApplyState = {
    enabled: false,
    settings: {
        jobTitles: [],
        locations: [],
        jobTypes: [],
        maxApplicationsPerDay: 5,
        autoApplyTime: '09:00'
    }
};

document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
});

function toggleAutoApply() {
    autoApplyState.enabled = !autoApplyState.enabled;
    updateToggleUI();
    saveSettings();
}

function updateToggleUI() {
    const toggle = document.getElementById('toggle-auto-apply');
    const label = document.getElementById('toggle-label');
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    
    if (autoApplyState.enabled) {
        toggle?.classList.add('active');
        label.textContent = 'Enabled';
        dot?.classList.remove('inactive');
        dot?.classList.add('active');
        text.textContent = 'On';
    } else {
        toggle?.classList.remove('active');
        label.textContent = 'Disabled';
        dot?.classList.add('inactive');
        dot?.classList.remove('active');
        text.textContent = 'Off';
    }
}

function saveSettings() {
    const jobTitles = (document.getElementById('job-titles-input')?.value || '').split(',').map(t => t.trim()).filter(Boolean);
    const locations = (document.getElementById('locations-input')?.value || '').split(',').map(l => l.trim()).filter(Boolean);
    const jobTypes = (document.getElementById('job-types-input')?.value || '').split(',').map(t => t.trim()).filter(Boolean);
    const maxApps = parseInt(document.getElementById('max-applications')?.value || '5');
    const time = document.getElementById('auto-apply-time')?.value || '09:00';
    
    autoApplyState.settings = {
        jobTitles,
        locations,
        jobTypes,
        maxApplicationsPerDay: maxApps,
        autoApplyTime: time,
        enabled: autoApplyState.enabled
    };
    
    fetch('/api/auto-apply/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(autoApplyState.settings)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showSuccess('Settings saved successfully');
        } else {
            showError(data.error || 'Failed to save settings');
        }
    })
    .catch(err => showError('Failed to save settings: ' + err.message));
}

function loadSettings() {
    fetch('/api/auto-apply/settings')
        .then(res => res.json())
        .then(data => {
            if (data.success && data.settings) {
                autoApplyState.settings = data.settings;
                autoApplyState.enabled = data.settings.enabled || false;
                
                document.getElementById('job-titles-input').value = data.settings.jobTitles?.join(', ') || '';
                document.getElementById('locations-input').value = data.settings.locations?.join(', ') || '';
                document.getElementById('job-types-input').value = data.settings.jobTypes?.join(', ') || '';
                document.getElementById('max-applications').value = data.settings.maxApplicationsPerDay || 5;
                document.getElementById('auto-apply-time').value = data.settings.autoApplyTime || '09:00';
                
                updateToggleUI();
                loadLogs();
            }
        })
        .catch(err => console.error('Failed to load settings:', err));
}

function runAutoApply() {
    if (!confirm('Run auto-apply now?')) return;
    
    showLoading(true, 'Running auto-apply...');
    fetch('/api/auto-apply/run', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showSuccess('Auto-apply completed. ' + (data.applied_count || 0) + ' applications sent.');
                loadLogs();
            } else {
                showError(data.error || 'Auto-apply failed');
            }
        })
        .catch(err => showError('Auto-apply error: ' + err.message))
        .finally(() => showLoading(false));
}

function loadLogs() {
    fetch('/api/auto-apply/logs')
        .then(res => res.json())
        .then(data => {
            if (data.success && data.logs) {
                displayLogs(data.logs);
                document.getElementById('total-applied').textContent = data.logs.length;
            }
        })
        .catch(err => console.error('Failed to load logs:', err));
}

function displayLogs(logs) {
    const tbody = document.getElementById('logs-tbody');
    tbody.innerHTML = '';
    
    if (logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 20px; color: var(--text-secondary);">
                    No auto-apply logs yet
                </td>
            </tr>
        `;
        return;
    }
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(log.job_title || 'N/A')}</td>
            <td>${escapeHtml(log.company || 'N/A')}</td>
            <td>${escapeHtml(log.action || 'Applied')}</td>
            <td>${escapeHtml(log.recipient_email || 'N/A')}</td>
            <td>${new Date(log.timestamp).toLocaleDateString()}</td>
        `;
        tbody.appendChild(row);
    });
}

function closeEmailModal() {
    document.getElementById('manual-email-modal')?.classList.remove('active');
}

function submitManualEmail() {
    const email = document.getElementById('manual-email-input')?.value.trim();
    if (!email) {
        showError('Please enter an email address');
        return;
    }
    showSuccess('Email submitted');
    closeEmailModal();
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