/* ======================================
   UTILS.JS - Client-side Utility Functions
   Project Echo
   ====================================== */

const EchoUtils = {
    /**
     * Escape HTML to prevent XSS.
     * @param {string} str - Raw string.
     * @returns {string} Escaped string.
     */
    escapeHtml(str) {
        if (str === null || str === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    },

    /**
     * Format a number with comma separators.
     * @param {number|string} num - Number to format.
     * @returns {string} Formatted number.
     */
    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        return Number(num).toLocaleString('th-TH');
    },

    /**
     * Build an HTML table from columns and records.
     * @param {string[]} columns - Column names.
     * @param {Object[]} records - Array of row objects.
     * @returns {string} HTML table string.
     */
    buildTable(columns, records) {
        if (!columns.length || !records.length) {
            return '<div class="empty-state"><span class="material-symbols-rounded">inbox</span><p>ไม่มีข้อมูล</p></div>';
        }

        let html = '<table class="data-table"><thead><tr><th class="row-num">#</th>';
        columns.forEach(col => {
            html += `<th>${this.escapeHtml(col)}</th>`;
        });
        html += '</tr></thead><tbody>';

        records.forEach((row, i) => {
            html += `<tr><td class="row-num">${i + 1}</td>`;
            columns.forEach(col => {
                const val = row[col];
                html += `<td>${val !== null && val !== undefined ? this.escapeHtml(val) : '-'}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        return html;
    },

    /**
     * Validate a date string (YYYY-MM-DD).
     * @param {string} dateStr - Date string.
     * @returns {boolean} True if valid.
     */
    isValidDate(dateStr) {
        return /^\d{4}-\d{2}-\d{2}$/.test(dateStr) && !isNaN(Date.parse(dateStr));
    },

    /**
     * Debounce a function call.
     * @param {Function} fn - Function to debounce.
     * @param {number} delay - Delay in ms.
     * @returns {Function} Debounced function.
     */
    debounce(fn, delay = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },

    /**
     * Show a toast notification.
     * @param {string} message - Message text.
     * @param {string} type - Type: success, error, warning, info.
     * @param {number} duration - Duration in ms.
     */
    toast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type}`;
        toast.style.cssText = 'position:fixed;top:80px;right:20px;z-index:9999;min-width:280px;max-width:420px;animation:slideDown 0.3s ease;';
        toast.innerHTML = `<span class="alert-message">${this.escapeHtml(message)}</span><button class="alert-close" onclick="this.parentElement.remove()">&times;</button>`;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};
