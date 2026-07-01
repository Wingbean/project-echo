/* ======================================
   API.JS - API Client with CSRF Handling
   Project Echo
   ====================================== */

const EchoAPI = {
    /**
     * Get CSRF token from the page.
     * @returns {string} CSRF token value.
     */
    getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');

        const input = document.querySelector('input[name="csrf_token"]');
        if (input) return input.value;

        return '';
    },

    /**
     * Make a GET request.
     * @param {string} url - URL to fetch.
     * @param {Object} params - Optional query parameters.
     * @returns {Promise<Object>} JSON response.
     */
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;

        const response = await fetch(fullUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    },

    /**
     * Make a POST request with CSRF protection.
     * @param {string} url - URL to post to.
     * @param {Object} data - JSON body data.
     * @returns {Promise<Object>} JSON response.
     */
    async post(url, data = {}) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    },

    /**
     * Submit a form via AJAX with CSRF.
     * @param {HTMLFormElement} form - The form element.
     * @returns {Promise<Object>} JSON response.
     */
    async submitForm(form) {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: form.method || 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    },
};
