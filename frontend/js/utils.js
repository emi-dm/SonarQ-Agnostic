/**
 * Utility Functions
 */

// ==================== Toast Notifications ====================

export function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== Loading Overlay ====================

export function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    const messageEl = overlay.querySelector('p');
    messageEl.textContent = message;
    overlay.classList.remove('hidden');
}

export function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.add('hidden');
}

// ==================== Date Formatting ====================

export function formatDate(dateStr, options = {}) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    const defaultOptions = { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
    };
    
    return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

export function formatDateTime(dateStr) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

export function formatRelativeTime(dateStr) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return formatDate(dateStr);
}

// ==================== HTML Escaping ====================

export function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// ==================== Number Formatting ====================

export function formatNumber(num) {
    if (num == null) return '-';
    return new Intl.NumberFormat().format(num);
}

export function formatPercentage(value, decimals = 1) {
    if (value == null) return '-';
    return value.toFixed(decimals) + '%';
}

// ==================== Debounce ====================

export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
