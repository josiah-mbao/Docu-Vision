// Toast notification function (needed in auth.js)
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add("show");
  }, 100);
  
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => {
      document.body.removeChild(toast);
    }, 300);
  }, 3000);
}

// API Base URL
const API_BASE_URL = '/api';

// DOM Elements
const authContainer = document.getElementById('auth-container');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const logoutBtn = document.getElementById('logout-btn');
const userEmail = document.getElementById('user-email');
const mainContent = document.getElementById('main-content');

// Store token in localStorage
function storeToken(token) {
    localStorage.setItem('access_token', token);
}

// Get stored token
function getToken() {
    return localStorage.getItem('access_token');
}

// Remove token
function clearToken() {
    localStorage.removeItem('access_token');
}

// Check if user is authenticated
function isAuthenticated() {
    return !!getToken();
}

// Register new user
async function register(email, password) {
    const formData = new URLSearchParams();
    formData.append('email', email);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
    }
    
    return await response.json();
}

// Login user
async function login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
    }
    
    const data = await response.json();
    storeToken(data.access_token);
    return data;
}

// Logout user
function logout() {
    clearToken();
    window.location.href = '/';
}

// Get current user
async function getCurrentUser() {
    const token = getToken();
    if (!token) return null;
    
    const response = await fetch(`${API_BASE_URL}/auth/me/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    if (!response.ok) {
        clearToken();
        return null;
    }
    
    return await response.json();
}

// Auth header for authenticated requests
function authHeader() {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Update UI based on auth state
async function updateAuthUI() {
    if (isAuthenticated()) {
        const user = await getCurrentUser();
        if (user) {
            // Show authenticated UI
            document.querySelector('.auth-forms').style.display = 'none';
            document.querySelector('.user-info').style.display = 'flex';
            userEmail.textContent = user.email;
            mainContent.style.display = 'block';
        } else {
            // Invalid token, show login forms
            document.querySelector('.auth-forms').style.display = 'block';
            document.querySelector('.user-info').style.display = 'none';
            mainContent.style.display = 'none';
        }
    } else {
        // Show login forms
        document.querySelector('.auth-forms').style.display = 'block';
        document.querySelector('.user-info').style.display = 'none';
        mainContent.style.display = 'none';
    }
}

// Initialize auth state
async function initAuth() {
    if (isAuthenticated()) {
        await updateAuthUI();
    } else {
        updateAuthUI();
    }
}

// Event listeners
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        try {
            await login(email, password);
            await updateAuthUI();
            showToast('Login successful');
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        try {
            await register(email, password);
            showToast('Registration successful. Please login.');
            registerForm.reset();
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        logout();
    });
}

// Initialize auth when DOM is loaded
document.addEventListener('DOMContentLoaded', initAuth);

// Export functions
export {
    storeToken,
    getToken,
    clearToken,
    isAuthenticated,
    register,
    login,
    logout,
    getCurrentUser,
    authHeader,
    updateAuthUI
};