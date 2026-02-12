/**
 * API Client for SonarQube Visualizer
 */

const API_BASE = '/api';

/**
 * Fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        },
        ...options,
    };

    try {
        const response = await fetch(url, config);
        
        // Get response text first
        const text = await response.text();
        
        // Try to parse as JSON
        let data = null;
        if (text) {
            try {
                data = JSON.parse(text);
            } catch (e) {
                // Not JSON
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText} - ${text}`);
                }
                return null;
            }
        }

        if (!response.ok) {
            throw new Error(data?.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return data;
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// ==================== Connections ====================

export const connectionsAPI = {
    /**
     * List all connections
     */
    list: () => fetchAPI('/connections'),

    /**
     * Get a connection by ID
     */
    get: (id) => fetchAPI(`/connections/${id}`),

    /**
     * Create a new connection
     */
    create: (data) => fetchAPI('/connections', {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    /**
     * Update a connection
     */
    update: (id, data) => fetchAPI(`/connections/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
    }),

    /**
     * Delete a connection
     */
    delete: (id) => fetchAPI(`/connections/${id}`, {
        method: 'DELETE',
    }),

    /**
     * Test a connection
     */
    test: (id) => fetchAPI(`/connections/${id}/test`, {
        method: 'POST',
    }),
};

// ==================== Projects ====================

export const projectsAPI = {
    /**
     * List projects from a connection
     */
    list: (connectionId, query = {}) => {
        const params = new URLSearchParams();
        if (query.q) params.append('q', query.q);
        const queryString = params.toString();
        return fetchAPI(`/connections/${connectionId}/projects${queryString ? '?' + queryString : ''}`);
    },

    /**
     * List all cached projects
     */
    listAll: (query = {}) => {
        const params = new URLSearchParams();
        if (query.connectionId) params.append('connection_id', query.connectionId);
        if (query.search) params.append('search', query.search);
        const queryString = params.toString();
        return fetchAPI(`/projects${queryString ? '?' + queryString : ''}`);
    },

    /**
     * Get project details with metrics
     */
    get: (id) => fetchAPI(`/projects/${id}`),

    /**
     * Sync projects from SonarQube
     */
    sync: (connectionId) => fetchAPI(`/connections/${connectionId}/projects`, {
        method: 'POST',
    }),

    /**
     * Refresh project metrics
     */
    refresh: (id) => fetchAPI(`/projects/${id}/refresh`, {
        method: 'POST',
    }),
};

// ==================== Issues ====================

export const issuesAPI = {
    /**
     * List issues for a project
     */
    list: (projectId, filters = {}) => {
        const params = new URLSearchParams();
        if (filters.type) params.append('type', filters.type);
        if (filters.severity) params.append('severity', filters.severity);
        if (filters.status) params.append('status', filters.status);
        if (filters.page) params.append('page', filters.page);
        if (filters.pageSize) params.append('page_size', filters.pageSize);
        return fetchAPI(`/projects/${projectId}/issues?${params}`);
    },

    /**
     * Get issue details
     */
    get: (id) => fetchAPI(`/issues/${id}`),
};

// ==================== Trends ====================

export const trendsAPI = {
    /**
     * Get trends for a project
     */
    get: (projectId, options = {}) => {
        const params = new URLSearchParams();
        if (options.metrics) params.append('metrics', options.metrics);
        if (options.from) params.append('from', options.from);
        if (options.to) params.append('to', options.to);
        return fetchAPI(`/projects/${projectId}/trends?${params}`);
    },
};

// ==================== Health ====================

export const healthAPI = {
    /**
     * Check health status
     */
    check: () => fetchAPI('/health'),
};
