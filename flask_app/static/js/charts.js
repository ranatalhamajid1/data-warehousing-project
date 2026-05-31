/**
 * Enterprise Retail Analytics Engine — Chart.js Configuration
 * Defines chart defaults, color palettes, and reusable chart factory functions
 */

'use strict';

// ── Global Color Palette ────────────────────────────────────────────────────

const PALETTE = {
  primary:  '#6366f1',
  secondary:'#0ea5e9',
  accent:   '#f59e0b',
  success:  '#10b981',
  danger:   '#ef4444',
  warning:  '#f59e0b',
  info:     '#06b6d4',
  violet:   '#8b5cf6',
  pink:     '#ec4899',
  teal:     '#14b8a6',
};

const CATEGORY_COLORS = {
  'Electronics':   '#6366f1',
  'Clothing':      '#0ea5e9',
  'Home & Garden': '#10b981',
  'Sports':        '#f59e0b',
  'Books':         '#8b5cf6',
  'Toys':          '#ec4899',
  'Beauty':        '#14b8a6',
  'Food':          '#f97316',
  'Automotive':    '#ef4444',
  'Office':        '#84cc16',
};

const CHART_COLORS = Object.values(CATEGORY_COLORS);

// ── Chart.js Global Defaults ────────────────────────────────────────────────

function applyChartDefaults() {
  Chart.defaults.color = '#94a3b8';
  
  if (!Chart.defaults.font) {
    Chart.defaults.font = {};
  }
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 12;

  // Premium global elastic/3D bounce animations safely mutated
  if (!Chart.defaults.animation) {
    Chart.defaults.animation = {};
  }
  Chart.defaults.animation.duration = 1000;
  Chart.defaults.animation.easing = 'easeOutBack';

  // Premium active/hover elastic transition animations safely configured
  if (Chart.defaults.transitions && Chart.defaults.transitions.active) {
    if (!Chart.defaults.transitions.active.animation) {
      Chart.defaults.transitions.active.animation = {};
    }
    Chart.defaults.transitions.active.animation.duration = 400;
    Chart.defaults.transitions.active.animation.easing = 'easeOutBack';
  }

  // Doughnut default hover offset and glow borders safely mutated
  if (!Chart.defaults.datasets) {
    Chart.defaults.datasets = {};
  }
  if (!Chart.defaults.datasets.doughnut) {
    Chart.defaults.datasets.doughnut = {};
  }
  Chart.defaults.datasets.doughnut.hoverOffset = 16;
  Chart.defaults.datasets.doughnut.hoverBorderWidth = 3;
  Chart.defaults.datasets.doughnut.hoverBorderColor = '#ffffff';

  // Bar default highlights safely mutated
  if (!Chart.defaults.datasets.bar) {
    Chart.defaults.datasets.bar = {};
  }
  Chart.defaults.datasets.bar.hoverBorderWidth = 3;
  Chart.defaults.datasets.bar.hoverBorderColor = '#ffffff';
  Chart.defaults.datasets.bar.hoverBorderRadius = 8;

  // Line hover dynamic dot expansion safely mutated
  if (!Chart.defaults.datasets.line) {
    Chart.defaults.datasets.line = {};
  }
  Chart.defaults.datasets.line.pointHoverRadius = 8;
  Chart.defaults.datasets.line.pointHoverBorderWidth = 3;
  Chart.defaults.datasets.line.pointHoverBackgroundColor = '#ffffff';

  // Tooltip defaults safely mutated
  if (!Chart.defaults.plugins) {
    Chart.defaults.plugins = {};
  }
  if (!Chart.defaults.plugins.tooltip) {
    Chart.defaults.plugins.tooltip = {};
  }
  Chart.defaults.plugins.tooltip.backgroundColor = '#16161f';
  Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.08)';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.titleColor = '#f1f5f9';
  Chart.defaults.plugins.tooltip.bodyColor = '#94a3b8';
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
  Chart.defaults.plugins.tooltip.displayColors = true;
  Chart.defaults.plugins.tooltip.boxWidth = 10;
  Chart.defaults.plugins.tooltip.boxHeight = 10;

  // Legend labels safely mutated
  if (!Chart.defaults.plugins.legend) {
    Chart.defaults.plugins.legend = {};
  }
  if (!Chart.defaults.plugins.legend.labels) {
    Chart.defaults.plugins.legend.labels = {};
  }
  Chart.defaults.plugins.legend.labels.color = '#94a3b8';
  Chart.defaults.plugins.legend.labels.padding = 16;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
  if (!Chart.defaults.plugins.legend.labels.font) {
    Chart.defaults.plugins.legend.labels.font = {};
  }
  Chart.defaults.plugins.legend.labels.font.size = 12;
}

// ── Grid Options ────────────────────────────────────────────────────────────

const GRID_OPTS = {
  color: 'rgba(255,255,255,0.05)',
  drawBorder: false,
};

const TICK_OPTS = {
  color: '#64748b',
  font: { size: 11 },
};

// ── Gradient Helper ─────────────────────────────────────────────────────────

function makeGradient(ctx, colorTop, colorBottom = 'transparent', height = 300) {
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, colorTop);
  gradient.addColorStop(1, colorBottom);
  return gradient;
}

// ── Revenue Line Chart ───────────────────────────────────────────────────────

function createRevenueChart(canvasId, labels, revenueData, marginData = null) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');

  const revenueGradient = makeGradient(
    ctx, 'rgba(99,102,241,0.35)', 'rgba(99,102,241,0.01)', canvas.height || 300
  );
  const marginGradient = makeGradient(
    ctx, 'rgba(16,185,129,0.25)', 'rgba(16,185,129,0.01)', canvas.height || 300
  );

  const datasets = [
    {
      label: 'Revenue ($)',
      data: revenueData,
      borderColor: PALETTE.primary,
      backgroundColor: revenueGradient,
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 10,
      pointHoverBackgroundColor: '#ffffff',
      pointHoverBorderColor: PALETTE.primary,
      pointHoverBorderWidth: 4,
    }
  ];

  if (marginData) {
    datasets.push({
      label: 'Margin ($)',
      data: marginData,
      borderColor: PALETTE.success,
      backgroundColor: marginGradient,
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 10,
      pointHoverBackgroundColor: '#ffffff',
      pointHoverBorderColor: PALETTE.success,
      pointHoverBorderWidth: 4,
    });
  }

  return new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { grid: GRID_OPTS, ticks: { ...TICK_OPTS, maxTicksLimit: 12 } },
        y: {
          grid: GRID_OPTS,
          ticks: {
            ...TICK_OPTS,
            callback: v => '$' + (v >= 1000 ? (v/1000).toFixed(0) + 'k' : v),
          }
        },
      },
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: ctx => `${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString(undefined, {maximumFractionDigits:0})}`,
          }
        }
      }
    }
  });
}

// ── Donut / Pie Chart ────────────────────────────────────────────────────────

function createDonutChart(canvasId, labels, values, title = '') {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');

  const colors = labels.map(l => CATEGORY_COLORS[l] || CHART_COLORS[labels.indexOf(l) % CHART_COLORS.length]);

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors.map(c => c + 'cc'),
        borderColor: colors,
        borderWidth: 2,
        hoverOffset: 20,
        hoverBorderWidth: 4,
        hoverBorderColor: '#ffffff',
        hoverBackgroundColor: colors,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      animation: {
        animateScale: true,
        animateRotate: true,
        duration: 1000,
        easing: 'easeOutBack'
      },
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 12 } },
        tooltip: {
          callbacks: {
            label: ctx => {
              const total = ctx.dataset.data.reduce((a,b) => a+b, 0);
              const pct = ((ctx.raw / total) * 100).toFixed(1);
              return ` ${ctx.label}: $${Number(ctx.raw).toLocaleString()} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

// ── Horizontal Bar Chart ─────────────────────────────────────────────────────

function createHBarChart(canvasId, labels, values, valueLabel = 'Revenue', color = PALETTE.primary) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');

  const colors = labels.map((_, i) => {
    const intensity = 1 - (i / labels.length * 0.5);
    return `rgba(99,102,241,${intensity})`;
  });

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: valueLabel,
        data: values,
        backgroundColor: colors,
        borderColor: colors.map(c => c.replace(/[\d.]+\)$/, '1)')),
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
        hoverBorderWidth: 4,
        hoverBorderColor: '#ffffff',
        hoverBorderRadius: 8,
        hoverBackgroundColor: colors.map(c => c.replace(/[\d.]+\)$/, '1)')),
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: GRID_OPTS,
          ticks: {
            ...TICK_OPTS,
            callback: v => '$' + (v >= 1000 ? (v/1000).toFixed(0) + 'k' : v),
          }
        },
        y: { grid: { display: false }, ticks: TICK_OPTS },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString(undefined,{maximumFractionDigits:0})}`,
          }
        }
      }
    }
  });
}

// ── Vertical Bar Chart ───────────────────────────────────────────────────────

function createVBarChart(canvasId, labels, datasets) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');

  datasets.forEach(d => {
    d.hoverBorderWidth = 4;
    d.hoverBorderColor = '#ffffff';
    d.hoverBorderRadius = 8;
    if (d.backgroundColor) {
      if (typeof d.backgroundColor === 'string' && d.backgroundColor.startsWith('rgba')) {
        d.hoverBackgroundColor = d.backgroundColor.replace(/[\d.]+\)$/, '1)');
      } else if (Array.isArray(d.backgroundColor)) {
        d.hoverBackgroundColor = d.backgroundColor.map(c => typeof c === 'string' && c.startsWith('rgba') ? c.replace(/[\d.]+\)$/, '1)') : c);
      } else {
        d.hoverBackgroundColor = d.backgroundColor;
      }
    }
  });

  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 1000,
        easing: 'easeOutBack'
      },
      scales: {
        x: { grid: { display: false }, ticks: TICK_OPTS, stacked: false },
        y: {
          grid: GRID_OPTS,
          ticks: {
            ...TICK_OPTS,
            callback: v => '$' + (v >= 1000 ? (v/1000).toFixed(0) + 'k' : v),
          }
        },
      },
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString()}`,
          }
        }
      }
    }
  });
}

// ── Radar Chart ──────────────────────────────────────────────────────────────

function createRadarChart(canvasId, labels, datasets) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext('2d');

  return new Chart(ctx, {
    type: 'radar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          angleLines: { color: 'rgba(255,255,255,0.06)' },
          pointLabels: { color: '#94a3b8', font: { size: 11 } },
          ticks: { color: '#64748b', backdropColor: 'transparent', font: { size: 10 } },
        }
      },
      plugins: { legend: { position: 'bottom' } }
    }
  });
}

// ── Number Counter Animation ─────────────────────────────────────────────────

function animateCounter(element, target, duration = 1500, prefix = '', suffix = '') {
  const start = 0;
  const startTime = performance.now();
  const formatNum = n => {
    if (n >= 1_000_000) return prefix + (n / 1_000_000).toFixed(2) + 'M' + suffix;
    if (n >= 1_000)     return prefix + (n / 1_000).toFixed(1)     + 'K' + suffix;
    return prefix + Math.round(n).toLocaleString() + suffix;
  };
  const update = (currentTime) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(eased * target);
    element.textContent = formatNum(current);
    if (progress < 1) requestAnimationFrame(update);
    else element.textContent = formatNum(target);
  };
  requestAnimationFrame(update);
}

// ── Initialize All KPI Counters ──────────────────────────────────────────────

function initKpiCounters() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    animateCounter(el, target, 1400, prefix, suffix);
  });
}

// ── SQL Syntax Highlighter ───────────────────────────────────────────────────

function highlightSQL(sql) {
  const keywords = ['SELECT','FROM','WHERE','JOIN','LEFT','RIGHT','INNER','OUTER',
                    'ON','GROUP','BY','ORDER','HAVING','LIMIT','WITH','AS','AND',
                    'OR','NOT','IN','IS','NULL','CASE','WHEN','THEN','ELSE','END',
                    'COUNT','SUM','AVG','MIN','MAX','ROUND','DISTINCT','UNION',
                    'ALL','TOP','PARTITION','OVER','RANK','ROW_NUMBER','DATEADD',
                    'DATEDIFF','COALESCE','IFF','NULLIF','CONCAT'];
  let highlighted = sql
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  keywords.forEach(kw => {
    const re = new RegExp(`\\b${kw}\\b`, 'g');
    highlighted = highlighted.replace(re, `<span class="sql-keyword">${kw}</span>`);
  });
  // Highlight table names (RETAIL_DW.SCHEMA.TABLE pattern)
  highlighted = highlighted.replace(
    /RETAIL_DW\.\w+\.\w+/g,
    m => `<span class="sql-table">${m}</span>`
  );
  // Highlight numbers
  highlighted = highlighted.replace(
    /\b(\d+(?:\.\d+)?)\b/g,
    `<span class="sql-number">$1</span>`
  );
  return highlighted;
}

// ── Toast Notifications ──────────────────────────────────────────────────────

function showToast(message, type = 'info', duration = 3500) {
  const toast = document.createElement('div');
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  toast.style.cssText = `
    position:fixed; bottom:24px; right:24px; z-index:9999;
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius-sm); padding:12px 16px;
    display:flex; align-items:center; gap:10px;
    font-size:13px; color:var(--text-primary);
    box-shadow:var(--shadow-lg);
    animation:slideUp .3s ease;
    max-width:360px;
  `;
  toast.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'fadeOut .3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Dynamic Theme Adaptations for Charts ────────────────────────────────────

function updateChartsForTheme(theme) {
  setTimeout(() => {
    const styles = getComputedStyle(document.documentElement);
    const textPrimary = styles.getPropertyValue('--text-primary').trim() || '#f8fafc';
    const textSecondary = styles.getPropertyValue('--text-secondary').trim() || '#cbd5e1';
    const textMuted = styles.getPropertyValue('--text-muted').trim() || '#64748b';
    
    // Choose grid color & tooltip background based on theme
    const gridColor = theme === 'light' ? 'rgba(15, 23, 42, 0.06)' : 'rgba(255, 255, 255, 0.05)';
    const tooltipBg = theme === 'light' ? '#0f172a' : (theme === 'night' ? '#000000' : '#1e293b');
    const tooltipBorder = theme === 'light' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)';

    // 1. Update Chart.js global defaults
    Chart.defaults.color = textMuted;
    if (Chart.defaults.plugins && Chart.defaults.plugins.legend && Chart.defaults.plugins.legend.labels) {
      Chart.defaults.plugins.legend.labels.color = textMuted;
    }
    if (Chart.defaults.plugins && Chart.defaults.plugins.tooltip) {
      Chart.defaults.plugins.tooltip.backgroundColor = tooltipBg;
      Chart.defaults.plugins.tooltip.borderColor = tooltipBorder;
      Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
      Chart.defaults.plugins.tooltip.bodyColor = textSecondary;
    }

    // 2. Loop through all active chart instances and update them
    if (typeof Chart.instances !== 'undefined') {
      Object.values(Chart.instances).forEach(chart => {
        // Update legend labels
        if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
          chart.options.plugins.legend.labels.color = textSecondary;
        }
        
        // Update tooltips
        if (chart.options.plugins && chart.options.plugins.tooltip) {
          chart.options.plugins.tooltip.backgroundColor = tooltipBg;
          chart.options.plugins.tooltip.borderColor = tooltipBorder;
          chart.options.plugins.tooltip.bodyColor = textSecondary;
        }

        // Update scales (x, y, r)
        if (chart.options.scales) {
          Object.values(chart.options.scales).forEach(scale => {
            if (scale.grid) {
              scale.grid.color = gridColor;
            }
            if (scale.ticks) {
              scale.ticks.color = textMuted;
            }
            // Radar scales
            if (scale.angleLines) {
              scale.angleLines.color = gridColor;
            }
            if (scale.pointLabels) {
              scale.pointLabels.color = textSecondary;
            }
          });
        }

        chart.update('none'); // Update without animation triggers for performance
      });
    }
  }, 50);
}

// ── DOMContentLoaded ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  applyChartDefaults();
  initKpiCounters();
  const currentTheme = localStorage.getItem('theme') || 'light';
  updateChartsForTheme(currentTheme);
});

