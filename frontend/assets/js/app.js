/* =============================================
   FortressVault - Main JavaScript File
   =============================================
   Contains: API Interceptor, JWT, Toast, Modal,
   Validation, Auto Logout
   ============================================= */

// ==============================
// Configuration
// ==============================
const API_BASE_URL = 'http://localhost:8000';
const TOKEN_KEY = 'fortressvault_token';
const USER_KEY = 'fortressvault_user';

// ==============================
// JWT Utilities
// ==============================
const jwtUtils = {
    setToken(token) {
        localStorage.setItem(TOKEN_KEY, token);
    },
    
    getToken() {
        return localStorage.getItem(TOKEN_KEY);
    },
    
    removeToken() {
        localStorage.removeItem(TOKEN_KEY);
    },
    
    setUser(user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
    },
    
    getUser() {
        const userStr = localStorage.getItem(USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    },
    
    removeUser() {
        localStorage.removeItem(USER_KEY);
    },
    
    decodeToken(token) {
        try {
            const payload = token.split('.')[1];
            return JSON.parse(atob(payload));
        } catch {
            return null;
        }
    },
    
    isTokenExpired(token) {
        const decoded = this.decodeToken(token);
        if (!decoded || !decoded.exp) return true;
        const now = Math.floor(Date.now() / 1000);
        return now >= decoded.exp;
    },
    
    logout() {
        this.removeToken();
        this.removeUser();
        window.location.href = 'login.html';
    }
};

// ==============================
// Toast Notifications
// ==============================
const toastUtils = {
    show(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) {
            const newContainer = document.createElement('div');
            newContainer.id = 'toast-container';
            newContainer.className = 'toast-container';
            document.body.appendChild(newContainer);
        }
        
        const toastContainer = document.getElementById('toast-container');
        const toastEl = document.createElement('div');
        const bgClass = {
            'success': 'text-bg-success',
            'error': 'text-bg-danger',
            'warning': 'text-bg-warning',
            'info': 'text-bg-info'
        }[type] || 'text-bg-info';
        
        toastEl.className = `toast align-items-center ${bgClass} border-0 mb-2`;
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();
        
        setTimeout(() => {
            if (toastEl.parentNode) {
                toastEl.remove();
            }
        }, 5500);
    }
};

// ==============================
// Loading Overlay
// ==============================
const loadingUtils = {
    show() {
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'spinner-overlay';
            overlay.innerHTML = `
                <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            `;
            document.body.appendChild(overlay);
        }
    },
    
    hide() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
};

// ==============================
// API Interceptor (Fetch Wrapper)
// ==============================
const api = {
    async fetch(endpoint, options = {}) {
        const token = jwtUtils.getToken();
        
        // Check token expiration
        if (token && jwtUtils.isTokenExpired(token)) {
            jwtUtils.logout();
            throw new Error('Token expired');
        }
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers
            });
            
            if (response.status === 401) {
                jwtUtils.logout();
                throw new Error('Unauthorized');
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'API Error');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    get(endpoint) {
        return this.fetch(endpoint, { method: 'GET' });
    },
    
    post(endpoint, data) {
        return this.fetch(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    put(endpoint, data) {
        return this.fetch(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    delete(endpoint) {
        return this.fetch(endpoint, { method: 'DELETE' });
    }
};

// ==============================
// Form Validation
// ==============================
const validationUtils = {
    required(value, fieldName) {
        if (!value || !value.trim()) {
            throw new Error(`${fieldName} is required`);
        }
        return true;
    },
    
    minLength(value, min, fieldName) {
        if (value.length < min) {
            throw new Error(`${fieldName} must be at least ${min} characters`);
        }
        return true;
    }
};

// ==============================
// Auto Logout Timer
// ==============================
let autoLogoutTimer;
const autoLogout = {
    init() {
        this.resetTimer();
        document.addEventListener('mousemove', () => this.resetTimer());
        document.addEventListener('keypress', () => this.resetTimer());
    },
    
    resetTimer() {
        clearTimeout(autoLogoutTimer);
        autoLogoutTimer = setTimeout(() => {
            jwtUtils.logout();
            toastUtils.show('Session expired. Please login again.', 'warning');
        }, 30 * 60 * 1000); // 30 minutes
    }
};

// ==============================
// Initialize
// ==============================
document.addEventListener('DOMContentLoaded', () => {
    const currentPage = window.location.pathname.split('/').pop();
    
    // Auto logout for authenticated pages
    const authPages = ['dashboard.html', 'vault.html', 'add-vault.html', 'audit-log.html', 'benchmark.html', 'profile.html'];
    if (authPages.includes(currentPage)) {
        const token = jwtUtils.getToken();
        if (!token) {
            jwtUtils.logout();
        } else {
            autoLogout.init();
        }
    }
});
