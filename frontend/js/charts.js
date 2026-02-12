/**
 * Charts Component - Chart.js wrappers for trends visualization
 */

import Chart from 'chart.js/auto';

export class TrendChart {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.chart = null;
        this.options = {
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
            ...options,
        };
    }

    /**
     * Render a line chart for trends
     */
    renderLineChart(data) {
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(this.canvas, {
            type: 'line',
            data: data,
            options: this.options,
        });

        return this.chart;
    }

    /**
     * Render a bar chart for comparisons
     */
    renderBarChart(data) {
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(this.canvas, {
            type: 'bar',
            data: data,
            options: this.options,
        });

        return this.chart;
    }

    /**
     * Update chart data
     */
    updateData(data) {
        if (this.chart) {
            this.chart.data = data;
            this.chart.update();
        }
    }

    /**
     * Destroy the chart
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

/**
 * Color palette matching SonarQube severity levels
 */
export const severityColors = {
    BLOCKER: '#FF4444',
    CRITICAL: '#FF8800',
    MAJOR: '#FFCC00',
    MINOR: '#4488FF',
    INFO: '#888888',
};

/**
 * Create datasets for metrics trends
 */
export function createTrendDatasets(trends) {
    const colors = {
        bugs: severityColors.BLOCKER,
        vulnerabilities: severityColors.CRITICAL,
        code_smells: severityColors.MAJOR,
        coverage: '#28A745',
    };

    const datasets = [];

    trends.forEach((metric) => {
        const color = colors[metric.metric] || '#888888';
        
        datasets.push({
            label: formatMetricLabel(metric.metric),
            data: metric.data_points.map((dp) => dp.value),
            borderColor: color,
            backgroundColor: color + '20',
            tension: 0.3,
            fill: metric.metric === 'coverage',
        });
    });

    return datasets;
}

/**
 * Format metric name for display
 */
function formatMetricLabel(metric) {
    const labels = {
        bugs: 'Bugs',
        vulnerabilities: 'Vulnerabilities',
        code_smells: 'Code Smells',
        coverage: 'Coverage %',
    };
    return labels[metric] || metric;
}

/**
 * Extract labels from trend data
 */
export function extractTrendLabels(trends) {
    if (!trends || trends.length === 0) return [];
    return trends[0].data_points.map((dp) => dp.date);
}
