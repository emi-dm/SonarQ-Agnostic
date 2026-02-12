/**
 * Metrics Panel Component
 */

export function renderMetricsPanel(metrics) {
    if (!metrics) {
        return '<p>No metrics available</p>';
    }

    const cards = [
        { key: 'bugs', label: 'Bugs', color: 'blocker' },
        { key: 'vulnerabilities', label: 'Vulnerabilities', color: 'critical' },
        { key: 'code_smells', label: 'Code Smells', color: 'major' },
        { key: 'coverage', label: 'Coverage', color: 'success', suffix: '%' },
        { key: 'duplicated_lines_density', label: 'Duplicated', color: 'warning', suffix: '%' },
        { key: 'sqale_index', label: 'Tech Debt', color: 'info', suffix: ' min' },
    ];

    return `
        <div class="metrics-panel">
            ${cards.map(card => renderMetricCard(card, metrics)).join('')}
        </div>
    `;
}

function renderMetricCard(config, metrics) {
    const value = metrics[config.key];
    const displayValue = value != null ? value + (config.suffix || '') : '-';
    
    return `
        <div class="metric-card ${config.color}">
            <div class="metric-card-value">${displayValue}</div>
            <div class="metric-card-label">${config.label}</div>
        </div>
    `;
}
