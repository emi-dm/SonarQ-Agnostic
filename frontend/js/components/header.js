/**
 * Header Component
 */

export function renderHeader() {
    return `
        <header class="header">
            <div class="header-left">
                <h1>SonarQube Visualizer</h1>
            </div>
            <div class="header-right">
                <select id="connection-select" class="select">
                    <option value="">Select Connection</option>
                </select>
                <button id="sync-projects-btn" class="btn btn-secondary">
                    Sync Projects
                </button>
            </div>
        </header>
    `;
}
