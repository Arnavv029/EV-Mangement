/* HapticEV — Central API Client
 * All HTTP calls to the Django backend go through this file.
 * Handles: JWT injection, 401 redirect, JSON parsing, error extraction.
 */
(function () {
  const API_BASE = 'http://localhost:8000/api';

  // ── Auth token helpers ────────────────────────────────────────────────────
  const auth = {
    getToken:    ()  => localStorage.getItem('hev_access'),
    getRefresh:  ()  => localStorage.getItem('hev_refresh'),
    getUser:     ()  => { try { return JSON.parse(localStorage.getItem('hev_user') || 'null'); } catch { return null; } },
    setSession:  (tokens, user) => {
      localStorage.setItem('hev_access',  tokens.access);
      localStorage.setItem('hev_refresh', tokens.refresh);
      localStorage.setItem('hev_user',    JSON.stringify(user));
    },
    clearSession: () => {
      localStorage.removeItem('hev_access');
      localStorage.removeItem('hev_refresh');
      localStorage.removeItem('hev_user');
    },
    isLoggedIn:  () => !!localStorage.getItem('hev_access'),
  };

  // ── Core fetch wrapper ────────────────────────────────────────────────────
  async function apiFetch(endpoint, options = {}) {
    const token   = auth.getToken();
    const headers = { ...options.headers };
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

    if (res.status === 401) {
      auth.clearSession();
      // Redirect to login (works from both /pages/ subdirectory and root)
      const isInPages = location.pathname.includes('/pages/');
      location.href = isInPages ? 'login.html' : '/pages/login.html';
      return null;
    }
    return res;
  }

  // ── Convenience helpers ───────────────────────────────────────────────────
  async function apiGet(endpoint) {
    return apiFetch(endpoint, { method: 'GET' });
  }

  async function apiPost(endpoint, body, isFormData = false) {
    return apiFetch(endpoint, {
      method: 'POST',
      body: isFormData ? body : JSON.stringify(body),
    });
  }

  async function apiPatch(endpoint, body) {
    return apiFetch(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  // ── Auth guard ────────────────────────────────────────────────────────────
  // Call at top of every protected page.
  // ownerOnly=true redirects non-owners back to home.
  function requireAuth(ownerOnly = false) {
    const user  = auth.getUser();
    const token = auth.getToken();
    if (!token || !user) {
      location.href = 'login.html';
      return null;
    }
    if (ownerOnly && user.role !== 'owner') {
      location.href = 'home.html';
      return null;
    }
    if (!ownerOnly && user.role === 'owner') {
      // Owner accidentally opened a user page — redirect to dashboard
      // (don't do this for neutral pages like history)
    }
    return user;
  }

  // ── Expose globally ───────────────────────────────────────────────────────
  window.API = { auth, apiFetch, apiGet, apiPost, apiPatch, requireAuth };
})();
