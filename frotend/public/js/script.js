/* HapticEV — Shared utilities
 * Pure utility functions only — NO hardcoded mock data.
 * All station / booking / user data comes from the real Django API (api.js).
 */
(function () {

  // ── Toast notification ─────────────────────────────────────────────────────
  window.toast = function (msg) {
    let t = document.getElementById('hev-toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'hev-toast';
      t.className = 'toast';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._t);
    t._t = setTimeout(() => t.classList.remove('show'), 2400);
  };

  // ── Generic chip / tab toggle ─────────────────────────────────────────────
  document.addEventListener('click', e => {
    const chip = e.target.closest('[data-toggle="chip"]');
    if (chip) {
      chip.parentElement
        .querySelectorAll('.chip,.tab-line,.tabs button')
        .forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
    }

    // History tab filter
    const tab = e.target.closest('[data-history-tab]');
    if (tab) {
      document.querySelectorAll('[data-history-tab]').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const f = tab.dataset.historyTab;
      document.querySelectorAll('[data-status]').forEach(c => {
        c.style.display = (f === 'all' || c.dataset.status === f) ? '' : 'none';
      });
    }
  });

})();
