/**
 * Job Hunter - API Handler
 * Handles all API calls to the Flask backend
 */
const API = {
    /**
     * Fetch all jobs with filters
     */
    async getJobs(filters = {}) {
        const { status = 'all', source = 'all', sort = 'relevance' } = filters;
        const url = `/api/jobs?status=${status}&source=${source}&sort=${sort}`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching jobs:', error);
            throw error;
        }
    },

    /**
     * Get single job details
     */
    async getJobDetails(jobId) {
        try {
            const response = await fetch(`/api/job/${jobId}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching job details:', error);
            throw error;
        }
    },

    /**
     * Trigger job scraping
     */
    async scrapeJobs() {
        try {
            const response = await fetch('/api/scrape', { method: 'POST' });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error scraping jobs:', error);
            throw error;
        }
    },

    /**
     * Apply to a job
     */
    async applyToJob(jobId) {
        try {
            const response = await fetch(`/api/apply/${jobId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error applying to job:', error);
            throw error;
        }
    },

    /**
     * Update job status
     */
    async updateJobStatus(jobId, status, coverLetter = null) {
        try {
            const body = { status };
            if (coverLetter) {
                body.cover_letter = coverLetter;
            }
            
            const response = await fetch(`/api/job/${jobId}/status`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error updating job status:', error);
            throw error;
        }
    },

    /**
     * Get dashboard statistics
     */
    async getStats() {
        try {
            const response = await fetch('/api/stats');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching stats:', error);
            throw error;
        }
    },

    /**
     * Export jobs to Excel
     */
    async exportJobs(status = 'all') {
        window.location.href = `/api/export?status=${status}`;
    },

    /**
     * Bulk apply to multiple jobs
     */
    async bulkApply(jobIds) {
        try {
            const response = await fetch('/api/bulk-apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_ids: jobIds })
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error bulk applying:', error);
            throw error;
        }
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API;
}