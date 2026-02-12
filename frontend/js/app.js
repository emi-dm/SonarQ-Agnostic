/**
 * Main Application for SonarQube Visualizer
 */

import { connectionsAPI, projectsAPI, issuesAPI, trendsAPI } from './api.js';
import { renderProjectCard, renderProjectDetail, renderConnectionsList } from './components/project-card.js';
import { renderMetricsPanel } from './components/metrics-panel.js';
import { renderIssueList } from './components/issue-list.js';
import { renderHeader } from './components/header.js';
import { showToast, showLoading, hideLoading } from './utils.js';

// ==================== State ====================

const state = {
    currentView: 'dashboard',
    connections: [],
    projects: [],
    selectedConnection: null,
    selectedProject: null,
};

// ==================== Navigation ====================

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            switchView(view);
        });
    });
}

function switchView(viewName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.toggle('active', view.id === `${viewName}-view`);
    });

    state.currentView = viewName;

    // Load view data
    if (viewName === 'connections') {
        loadConnections();
    } else if (viewName === 'dashboard') {
        loadConnections();
    }
}

// ==================== Connections ====================

async function loadConnections() {
    try {
        state.connections = await connectionsAPI.list();
        
        // Update connection select in header
        const select = document.getElementById('connection-select');
        select.innerHTML = '<option value="">Select Connection</option>';
        state.connections.forEach(conn => {
            const option = document.createElement('option');
            option.value = conn.id;
            option.textContent = conn.name;
            if (conn.is_default && !state.selectedConnection) {
                option.selected = true;
                state.selectedConnection = conn.id;
            }
            select.appendChild(option);
        });

        // Render connections list
        const connectionsList = document.getElementById('connections-list');
        connectionsList.innerHTML = renderConnectionsList(state.connections);

        // Load projects if connection selected
        if (state.selectedConnection) {
            await loadProjects(state.selectedConnection);
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function initConnectionModal() {
    const modal = document.getElementById('connection-modal');
    const form = document.getElementById('connection-form');
    const addBtn = document.getElementById('add-connection-btn');
    const closeBtn = modal.querySelector('.modal-close');
    const backdrop = modal.querySelector('.modal-backdrop');
    const testBtn = document.getElementById('test-connection-btn');

    // Open modal
    addBtn.addEventListener('click', () => {
        form.reset();
        document.getElementById('connection-id').value = '';
        document.getElementById('modal-title').textContent = 'Add Connection';
        document.getElementById('connection-test-result').classList.add('hidden');
        modal.classList.remove('hidden');
    });

    // Close modal
    const closeModal = () => modal.classList.add('hidden');
    closeBtn.addEventListener('click', closeModal);
    backdrop.addEventListener('click', closeModal);

    // Test connection
    testBtn.addEventListener('click', async () => {
        const url = document.getElementById('connection-url').value;
        const organization = document.getElementById('connection-organization').value;
        const token = document.getElementById('connection-token').value;
        const resultEl = document.getElementById('connection-test-result');

        if (!url || !token) {
            resultEl.textContent = 'Please enter URL and token';
            resultEl.className = 'alert alert-error';
            resultEl.classList.remove('hidden');
            return;
        }

        testBtn.disabled = true;
        testBtn.textContent = 'Testing...';

        try {
            // Create temp connection to test
            const tempConn = await connectionsAPI.create({ name: 'Temp', url, organization, token });
            const result = await connectionsAPI.test(tempConn.id);
            await connectionsAPI.delete(tempConn.id);

            if (result.success) {
                resultEl.textContent = `✓ Connected! SonarQube version: ${result.version}`;
                resultEl.className = 'alert alert-success';
            } else {
                resultEl.textContent = `✗ ${result.message}`;
                resultEl.className = 'alert alert-error';
            }
        } catch (error) {
            resultEl.textContent = `✗ ${error.message}`;
            resultEl.className = 'alert alert-error';
        } finally {
            testBtn.disabled = false;
            testBtn.textContent = 'Test Connection';
            resultEl.classList.remove('hidden');
        }
    });

    // Save connection
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const id = document.getElementById('connection-id').value;
        const data = {
            name: document.getElementById('connection-name').value,
            url: document.getElementById('connection-url').value,
            organization: document.getElementById('connection-organization').value,
            token: document.getElementById('connection-token').value,
            is_default: document.getElementById('connection-default').checked,
        };

        try {
            if (id) {
                await connectionsAPI.update(id, data);
                showToast('Connection updated', 'success');
            } else {
                await connectionsAPI.create(data);
                showToast('Connection created', 'success');
            }
            closeModal();
            await loadConnections();
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

function initConnectionActions() {
    document.getElementById('connections-list').addEventListener('click', async (e) => {
        const editBtn = e.target.closest('.btn-edit');
        const deleteBtn = e.target.closest('.btn-delete');
        const testBtn = e.target.closest('.btn-test');

        if (!editBtn && !deleteBtn && !testBtn) return;

        const id = editBtn?.dataset.id || deleteBtn?.dataset.id || testBtn?.dataset.id;

        if (editBtn) {
            const conn = state.connections.find(c => c.id === id);
            if (conn) {
                document.getElementById('connection-id').value = conn.id;
                document.getElementById('connection-name').value = conn.name;
                document.getElementById('connection-url').value = conn.url;
                document.getElementById('connection-organization').value = conn.organization || '';
                document.getElementById('connection-default').checked = conn.is_default;
                document.getElementById('modal-title').textContent = 'Edit Connection';
                document.getElementById('connection-test-result').classList.add('hidden');
                document.getElementById('connection-modal').classList.remove('hidden');
            }
        } else if (deleteBtn) {
            if (confirm('Are you sure you want to delete this connection?')) {
                try {
                    await connectionsAPI.delete(id);
                    showToast('Connection deleted', 'success');
                    await loadConnections();
                } catch (error) {
                    showToast(error.message, 'error');
                }
            }
        } else if (testBtn) {
            try {
                showLoading('Testing connection...');
                const result = await connectionsAPI.test(id);
                if (result.success) {
                    showToast(`Connected! Version: ${result.version}`, 'success');
                } else {
                    showToast(result.message, 'error');
                }
            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                hideLoading();
            }
        }
    });
}

// ==================== Projects ====================

async function loadProjects(connectionId) {
    if (!connectionId) {
        state.projects = [];
        renderProjectsGrid();
        return;
    }

    state.selectedConnection = connectionId;

    try {
        const data = await projectsAPI.listAll({ connectionId });
        state.projects = data;
        renderProjectsGrid();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function renderProjectsGrid() {
    const grid = document.getElementById('projects-grid');
    
    if (state.projects.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📂</div>
                <h3>No projects yet</h3>
                <p>Select a connection and click "Sync Projects" to fetch your SonarQube projects.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = state.projects.map(p => renderProjectCard(p)).join('');

    // Add click handlers
    grid.querySelectorAll('.project-card').forEach(card => {
        card.addEventListener('click', () => {
            const projectId = card.dataset.id;
            loadProjectDetail(projectId);
        });
    });
}

async function loadProjectDetail(projectId) {
    try {
        showLoading('Loading project...');
        const data = await projectsAPI.get(projectId);
        
        const detailEl = document.getElementById('project-detail');
        detailEl.classList.remove('hidden');
        detailEl.innerHTML = renderProjectDetail(data);

        // Add back button handler
        detailEl.querySelector('.back-btn').addEventListener('click', () => {
            detailEl.classList.add('hidden');
        });

        // Add refresh button handler
        detailEl.querySelector('#refresh-metrics-btn')?.addEventListener('click', async () => {
            try {
                showLoading('Refreshing metrics...');
                await projectsAPI.refresh(projectId);
                await loadProjectDetail(projectId);
                showToast('Metrics refreshed', 'success');
            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                hideLoading();
            }
        });

        // Load trends
        loadProjectTrends(projectId);

        // Load issues
        loadProjectIssues(projectId);

    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function loadProjectTrends(projectId) {
    try {
        const trends = await trendsAPI.get(projectId);
        
        const trendsEl = document.querySelector('.trends-section');
        if (trendsEl) {
            // Render chart
            const canvas = trendsEl.querySelector('#trends-chart');
            if (canvas) {
                renderTrendsChart(canvas, trends);
            }
        }
    } catch (error) {
        console.error('Error loading trends:', error);
    }
}

function renderTrendsChart(canvas, trends) {
    const datasets = [];
    const colors = {
        bugs: '#FF4444',
        vulnerabilities: '#FF8800',
        code_smells: '#FFCC00',
        coverage: '#28A745',
    };

    trends.metrics.forEach((metric, idx) => {
        if (metric.data_points.length > 0) {
            datasets.push({
                label: metric.metric,
                data: metric.data_points.map(dp => dp.value),
                borderColor: colors[metric.metric] || '#888888',
                backgroundColor: colors[metric.metric] || '#888888',
                tension: 0.3,
            });
        }
    });

    if (datasets.length === 0) return;

    const labels = trends.metrics[0]?.data_points.map(dp => dp.date) || [];

    new Chart(canvas, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                },
            },
        },
    });
}

async function loadProjectIssues(projectId, filters = {}) {
    try {
        const data = await issuesAPI.list(projectId, { ...filters, pageSize: 20 });
        
        const issuesEl = document.querySelector('.issues-section');
        if (issuesEl) {
            issuesEl.innerHTML = renderIssueList(data.issues, data.pagination);

            // Add filter handlers
            const typeFilter = issuesEl.querySelector('#filter-type');
            const severityFilter = issuesEl.querySelector('#filter-severity');

            typeFilter?.addEventListener('change', () => {
                loadProjectIssues(projectId, { 
                    ...filters, 
                    type: typeFilter.value || undefined 
                });
            });

            severityFilter?.addEventListener('change', () => {
                loadProjectIssues(projectId, { 
                    ...filters, 
                    severity: severityFilter.value || undefined 
                });
            });
        }
    } catch (error) {
        console.error('Error loading issues:', error);
    }
}

function initProjectSync() {
    const syncBtn = document.getElementById('sync-projects-btn');
    const connectionSelect = document.getElementById('connection-select');

    syncBtn.addEventListener('click', async () => {
        const connectionId = connectionSelect.value;
        if (!connectionId) {
            showToast('Please select a connection first', 'warning');
            return;
        }

        try {
            showLoading('Syncing projects...');
            await projectsAPI.sync(connectionId);
            await loadProjects(connectionId);
            showToast('Projects synced successfully', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            hideLoading();
        }
    });

    connectionSelect.addEventListener('change', () => {
        loadProjects(connectionSelect.value);
    });
}

// ==================== Initialization ====================

async function init() {
    console.log('Initializing SonarQube Visualizer...');

    // Check health
    try {
        const health = await fetch('/api/health').then(r => r.json());
        console.log('Health:', health);
    } catch (error) {
        console.error('Health check failed:', error);
    }

    // Initialize components
    initNavigation();
    initConnectionModal();
    initConnectionActions();
    initProjectSync();

    // Load initial data
    await loadConnections();
}

// Start app
document.addEventListener('DOMContentLoaded', init);
