class ZeroNetExportApp extends HTMLElement {
  set hass(value) {
    this._hass = value;
    this._render();
  }

  set panel(value) {
    this._panel = value;
    this._render();
  }

  connectedCallback() {
    this._render();
  }

  _zneStates() {
    if (!this._hass || !this._hass.states) {
      return [];
    }
    return Object.entries(this._hass.states)
      .filter(([entityId]) => entityId.includes("zero_net_export"))
      .sort(([left], [right]) => left.localeCompare(right));
  }

  _escape(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  _render() {
    const config = (this._panel && this._panel.config) || {};
    const states = this._zneStates();
    const title = this._escape(config.title || "Zero Net Export");
    const version = this._escape(config.version || "unknown");
    const planCount = Array.isArray(config.entries) ? config.entries.length : 0;
    const readyLabel = this._escape(this._hass ? "Connected to Home Assistant" : "Waiting for Home Assistant");

    this.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100vh;
          box-sizing: border-box;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          font-family: var(--paper-font-body1_-_font-family, Roboto, Arial, sans-serif);
        }

        .zne-app {
          max-width: 1200px;
          margin: 0 auto;
          padding: 24px;
        }

        .zne-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 16px;
          border-bottom: 1px solid var(--divider-color);
          padding-bottom: 16px;
        }

        h1 {
          margin: 0;
          font-size: 28px;
          line-height: 1.2;
          font-weight: 500;
        }

        .zne-meta {
          color: var(--secondary-text-color);
          margin-top: 6px;
          font-size: 14px;
        }

        .zne-status {
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          padding: 10px 12px;
          min-width: 180px;
          text-align: right;
          background: var(--card-background-color);
        }

        .zne-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 12px;
          margin-top: 20px;
        }

        .zne-section {
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          padding: 14px;
          background: var(--card-background-color);
          min-height: 92px;
        }

        .zne-section h2 {
          margin: 0 0 8px;
          font-size: 16px;
          line-height: 1.3;
          font-weight: 500;
        }

        .zne-section p {
          margin: 0;
          color: var(--secondary-text-color);
          font-size: 14px;
          line-height: 1.4;
        }

        @media (max-width: 640px) {
          .zne-app {
            padding: 16px;
          }

          .zne-header {
            display: block;
          }

          .zne-status {
            margin-top: 12px;
            text-align: left;
          }
        }
      </style>
      <main class="zne-app">
        <header class="zne-header">
          <div>
            <h1>${title}</h1>
            <div class="zne-meta">Version ${version} · ${planCount} plan${planCount === 1 ? "" : "s"}</div>
          </div>
          <div class="zne-status">
            <strong>${readyLabel}</strong>
            <div class="zne-meta">${states.length} Zero Net Export entities visible</div>
          </div>
        </header>
        <section class="zne-grid" aria-label="Zero Net Export application sections">
          <div class="zne-section">
            <h2>Overview</h2>
            <p>Backend readiness, install version, and plan status.</p>
          </div>
          <div class="zne-section">
            <h2>Sources</h2>
            <p>Mapped grid, solar, load, and battery source roles.</p>
          </div>
          <div class="zne-section">
            <h2>Managed Devices</h2>
            <p>Entry-scoped controllable loads and safety actions.</p>
          </div>
          <div class="zne-section">
            <h2>Controls</h2>
            <p>Enable state, target export, operating mode, and guardrails.</p>
          </div>
          <div class="zne-section">
            <h2>Runtime</h2>
            <p>Current decisions, action history, and controller state.</p>
          </div>
          <div class="zne-section">
            <h2>Diagnostics</h2>
            <p>Setup blockers, install evidence, and support summary.</p>
          </div>
        </section>
      </main>
    `;
  }
}

customElements.define("zero-net-export-app", ZeroNetExportApp);
