/**
 * Project Card Component
 */

export function renderProjectCard(project) {
    const metrics = project.metrics || {};
    
    // Determine coverage class
    let coverageClass = 'coverage-good';
    if (metrics.coverage !== null && metrics.coverage !== undefined) {
        if (metrics.coverage < 50) coverageClass = 'coverage-critical';
        else if (metrics.coverage < 70) coverageClass = 'coverage-low';
    }

    // Determine staleness
    const isStale = project.staleness?.is_stale;
    const stalenessClass = isStale ? 'stale' : 'fresh';
    const stalenessText = isStale ? '⚠ Stale' : '✓ Fresh';

    return `
        <div class="project-card" data-id="${project.id}">
            <div class="project-card-header">
                <div>
                    <h3 class="project-card-title">${escapeHtml(project.name)}</h3>
                    <span class="project-card-key">${escapeHtml(project.sonar_key)}</span>
                </div>
            </div>
            
            <div class="project-card-meta">
                <span>${escapeHtml(project.visibility)}</span>
                ${project.last_analysis_date ? `<span>• ${formatDate(project.last_analysis_date)}</span>` : ''}
            </div>

            <div class="project-card-metrics">
                <div class="metric severity-blocker">
                    <div class="metric-value">${metrics.bugs ?? '-'}</div>
                    <div class="metric-label">Bugs</div>
                </div>
                <div class="metric severity-critical">
                    <div class="metric-value">${metrics.vulnerabilities ?? '-'}</div>
                    <div class="metric-label">Vulns</div>
                </div>
                <div class="metric severity-major">
                    <div class="metric-value">${metrics.code_smells ?? '-'}</div>
                    <div class="metric-label">Smells</div>
                </div>
                <div class="metric ${coverageClass}">
                    <div class="metric-value">${metrics.coverage != null ? metrics.coverage + '%' : '-'}</div>
                    <div class="metric-label">Coverage</div>
                </div>
            </div>

            <div class="project-card-footer">
                <span class="staleness-indicator ${stalenessClass}">${stalenessText}</span>
                ${metrics.alert_status ? `<span class="quality-gate ${metrics.alert_status.toLowerCase()}">${metrics.alert_status}</span>` : ''}
            </div>
        </div>
    `;
}

export function renderProjectDetail(data) {
    const project = data.project;
    const metrics = data.metrics || {};
    const staleness = data.staleness || {};

    return `
        <button class="back-btn">← Back to projects</button>
        
        <div class="project-detail-header">
            <div>
                <h2 class="project-detail-title">${escapeHtml(project.name)}</h2>
                <span class="project-detail-key">${escapeHtml(project.sonar_key)}</span>
            </div>
            <div class="detail-actions">
                <button id="refresh-metrics-btn" class="btn btn-secondary">
                    ↻ Refresh
                </button>
            </div>
        </div>

        <div class="metrics-panel">
            ${renderMetricCard('bugs', 'Bugs', metrics.bugs)}
            ${renderMetricCard('vulnerabilities', 'Vulnerabilities', metrics.vulnerabilities)}
            ${renderMetricCard('code-smells', 'Code Smells', metrics.code_smells)}
            ${renderMetricCard('coverage', 'Coverage', metrics.coverage, '%')}
            ${renderMetricCard('duplicated', 'Duplicated Lines', metrics.duplicated_lines_density, '%')}
            ${renderMetricCard('debt', 'Tech Debt', metrics.sqale_index, 'min')}
        </div>

        <div class="trends-section">
            <h3>Trends</h3>
            <div class="trends-chart">
                <canvas id="trends-chart"></canvas>
            </div>
        </div>

        <div class="issues-section">
            <h3>Recent Issues</h3>
            <div class="issues-filters">
                <div class="filter-group">
                    <label for="filter-type">Type:</label>
                    <select id="filter-type">
                        <option value="">All</option>
                        <option value="BUG">Bug</option>
                        <option value="VULNERABILITY">Vulnerability</option>
                        <option value="CODE_SMELL">Code Smell</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-severity">Severity:</label>
                    <select id="filter-severity">
                        <option value="">All</option>
                        <option value="BLOCKER">Blocker</option>
                        <option value="CRITICAL">Critical</option>
                        <option value="MAJOR">Major</option>
                        <option value="MINOR">Minor</option>
                        <option value="INFO">Info</option>
                    </select>
                </div>
            </div>
            <div class="issues-list">
                <div class="empty-state">
                    <p>Loading issues...</p>
                </div>
            </div>
        </div>
    `;
}

function renderMetricCard(className, label, value, suffix = '') {
    const displayValue = value != null ? value + suffix : '-';
    return `
        <div class="metric-card ${className}">
            <div class="metric-card-value">${displayValue}</div>
            <div class="metric-card-label">${label}</div>
        </div>
    `;
}

export function renderConnectionsList(connections) {
    if (connections.length === 0) {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">🔗</div>
                <h3>No connections</h3>
                <p>Add a SonarQube connection to get started.</p>
            </div>
        `;
    }

    return connections.map(conn => `
        <div class="connection-card" data-id="${conn.id}">
            <div class="connection-info">
                <h3>${escapeHtml(conn.name)}</h3>
                <p>${escapeHtml(conn.url)}</p>
                ${conn.is_default ? '<span class="badge">Default</span>' : ''}
            </div>
            <div class="connection-actions">
                <button class="btn btn-secondary btn-sm btn-test" data-id="${conn.id}">Test</button>
                <button class="btn btn-secondary btn-sm btn-edit" data-id="${conn.id}">Edit</button>
                <button class="btn btn-danger btn-sm btn-delete" data-id="${conn.id}">Delete</button>
            </div>
        </div>
    `).join('');
}

// ==================== Utilities ====================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
    });
}
