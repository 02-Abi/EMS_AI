// Main JavaScript file for Enterprise EMS

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeFormValidation();
    initializeAutoDismissAlerts();
});

// Initialize tooltips
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

// Tooltip functions
function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = e.target.getAttribute('title');
    tooltip.style.position = 'absolute';
    tooltip.style.backgroundColor = '#333';
    tooltip.style.color = 'white';
    tooltip.style.padding = '5px 10px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '12px';
    tooltip.style.zIndex = '1000';
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.top = rect.top - 30 + 'px';
    tooltip.style.left = rect.left + 'px';
    
    document.body.appendChild(tooltip);
    e.target._tooltip = tooltip;
}

function hideTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        e.target._tooltip = null;
    }
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', validateForm);
    });
}

function validateForm(e) {
    const form = e.target;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            highlightField(input, 'This field is required');
            isValid = false;
        } else {
            removeHighlight(input);
        }
        
        // Email validation
        if (input.type === 'email' && input.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value)) {
                highlightField(input, 'Please enter a valid email address');
                isValid = false;
            }
        }
        
        // Number validation
        if (input.type === 'number' && input.value) {
            const min = parseFloat(input.getAttribute('min'));
            const max = parseFloat(input.getAttribute('max'));
            const value = parseFloat(input.value);
            
            if (!isNaN(min) && value < min) {
                highlightField(input, `Value must be at least ${min}`);
                isValid = false;
            }
            
            if (!isNaN(max) && value > max) {
                highlightField(input, `Value must be at most ${max}`);
                isValid = false;
            }
        }
    });
    
    if (!isValid) {
        e.preventDefault();
    }
}

function highlightField(field, message) {
    field.classList.add('error-field');
    
    // Check if error message already exists
    let errorMsg = field.parentNode.querySelector('.field-error');
    if (!errorMsg) {
        errorMsg = document.createElement('div');
        errorMsg.className = 'field-error';
        errorMsg.style.color = '#e74c3c';
        errorMsg.style.fontSize = '12px';
        errorMsg.style.marginTop = '5px';
        field.parentNode.appendChild(errorMsg);
    }
    
    errorMsg.textContent = message;
    
    field.addEventListener('input', function removeError() {
        field.classList.remove('error-field');
        if (errorMsg) {
            errorMsg.remove();
        }
        field.removeEventListener('input', removeError);
    });
}

function removeHighlight(field) {
    field.classList.remove('error-field');
    const errorMsg = field.parentNode.querySelector('.field-error');
    if (errorMsg) {
        errorMsg.remove();
    }
}

// Auto-dismiss alerts
function initializeAutoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.persistent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            fadeOut(alert);
        }, 5000);
    });
}

function fadeOut(element) {
    let opacity = 1;
    const timer = setInterval(() => {
        if (opacity <= 0.1) {
            clearInterval(timer);
            element.remove();
        }
        element.style.opacity = opacity;
        opacity -= opacity * 0.1;
    }, 50);
}

// AJAX functions
function fetchWithCSRF(url, options = {}) {
    const csrftoken = getCookie('csrftoken');
    
    const defaults = {
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        }
    };
    
    const mergedOptions = { ...defaults, ...options };
    
    return fetch(url, mergedOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Table sorting
function sortTable(table, column, type = 'string') {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const sortedRows = rows.sort((a, b) => {
        const aCol = a.children[column].textContent.trim();
        const bCol = b.children[column].textContent.trim();
        
        if (type === 'number') {
            return parseFloat(aCol) - parseFloat(bCol);
        } else if (type === 'date') {
            return new Date(aCol) - new Date(bCol);
        } else {
            return aCol.localeCompare(bCol);
        }
    });
    
    // Clear and append sorted rows
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }
    
    sortedRows.forEach(row => tbody.appendChild(row));
}

// Search functionality
function searchTable(input, table) {
    const filter = input.value.toUpperCase();
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toUpperCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

// Export to CSV
function exportToCSV(table, filename) {
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            let text = col.textContent.trim();
            text = text.replace(/"/g, '""');
            return `"${text}"`;
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    
    window.URL.revokeObjectURL(url);
}