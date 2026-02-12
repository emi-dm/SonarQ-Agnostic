/**
 * Issue List Component
 */

export function renderIssueList(issues, pagination) {
    if (!issues || issues.length === 0) {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <h3>No issues found</h3>
                <p>Great job! This project has no issues matching the current filters.</p>
            </div>
        `;
    }

    return `
        <div class="issues-list">
            ${issues.map(renderIssueItem).join('')}
        </div>
        ${renderPagination(pagination)}
    `;
}

function renderIssueItem(issue) {
    const severityClass = issue.severity.toLowerCase();
    
    return `
        <div class="issue-item" data-id="${issue.id}">
            <div class="issue-severity ${severityClass}"></div>
            <div class="issue-content">
                <div class="issue-message">${escapeHtml(issue.message || 'No message')}</div>
                <div class="issue-meta">
                    <span class="issue-type">${issue.type}</span>
                    <span class="issue-status">${issue.status}</span>
                    ${issue.component ? `<span class="issue-location">${escapeHtml(issue.component)}${issue.line ? ':' + issue.line : ''}</span>` : ''}
                    ${issue.effort ? `<span class="issue-effort">${issue.effort} min</span>` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderPagination(pagination) {
    if (!pagination || pagination.total_pages <= 1) return '';

    const { page, page_size, total, total_pages } = pagination;
    const pages = [];

    // Build page numbers
    let start = Math.max(1, page - 2);
    let end = Math.min(total_pages, page + 2);

    if (end - start < 4) {
        if (start === 1) {
            end = Math.min(5, total_pages);
        } else {
            start = Math.max(1, total_pages - 4);
        }
    }

    for (let i = start; i <= end; i++) {
        pages.push(i);
    }

    return `
        <div class="pagination">
            <button ${page === 1 ? 'disabled' : ''} data-page="${page - 1}">← Prev</button>
            ${start > 1 ? '<span>...</span>' : ''}
            ${pages.map(p => `
                <button ${p === page ? 'disabled' : ''} data-page="${p}">${p}</button>
            `).join('')}
            ${end < total_pages ? '<span>...</span>' : ''}
            <button ${page === total_pages ? 'disabled' : ''} data-page="${page + 1}">Next →</button>
            <span class="pagination-info">${total} issues</span>
        </div>
    `;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
