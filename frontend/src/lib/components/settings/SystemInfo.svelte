<script lang="ts">
  import { onMount } from 'svelte';
  import { systemApi, type SystemInfo } from '$lib/api/system';

  let systemInfo: SystemInfo | null = null;
  let loading = true;
  let error: string | null = null;
  let copied = false;

  onMount(async () => {
    await loadSystemInfo();
  });

  async function loadSystemInfo() {
    try {
      loading = true;
      error = null;
      systemInfo = await systemApi.getSystemInfo();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load system information';
    } finally {
      loading = false;
    }
  }

  async function copyToClipboard() {
    if (!systemInfo) return;

    try {
      await navigator.clipboard.writeText(JSON.stringify(systemInfo, null, 2));
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }

  function refresh() {
    loadSystemInfo();
  }
</script>

<div class="system-info">
  <h2>System Information</h2>

  {#if loading}
    <p>Loading system information...</p>
  {:else if error}
    <div class="error">{error}</div>
  {:else if systemInfo}
    <div class="info-grid">
      <div class="info-item">
        <label>Application Version</label>
        <span class="value">{systemInfo.version || 'Unknown'}</span>
      </div>

      <div class="info-item">
        <label>Platform</label>
        <span class="value">{systemInfo.platform}</span>
      </div>

      <div class="info-item">
        <label>Python Version</label>
        <span class="value">{systemInfo.pythonVersion}</span>
      </div>

      <div class="info-item">
        <label>Node.js Version</label>
        <span class="value">{systemInfo.nodeVersion || 'Not detected'}</span>
      </div>

      <div class="info-item">
        <label>Git Version</label>
        <span class="value">{systemInfo.gitVersion || 'Not installed'}</span>
      </div>

      <div class="info-item">
        <label>Git LFS</label>
        <span
          class="value"
          class:installed={systemInfo.gitLFSInstalled}
          class:not-installed={!systemInfo.gitLFSInstalled}
        >
          {systemInfo.gitLFSInstalled ? '✓ Installed' : '✗ Not Installed'}
        </span>
      </div>

      <div class="info-item">
        <label>Docker Version</label>
        <span class="value">{systemInfo.dockerVersion || 'Not available'}</span>
      </div>

      <div class="info-item">
        <label>GPU Support</label>
        <span class="value">{systemInfo.gpuSupport ? '✓ Available' : 'Not detected'}</span>
      </div>

      <div class="info-item full-width">
        <label>Workspace Path</label>
        <code>{systemInfo.workspacePath}</code>
      </div>

      <div class="info-item full-width">
        <label>API Endpoint</label>
        <code>{systemInfo.apiEndpoint}</code>
      </div>
    </div>

    <div class="diagnostics">
      <h3>System Requirements</h3>
      <table class="requirements-table">
        <thead>
          <tr>
            <th>Component</th>
            <th>Status</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Git</td>
            <td>
              <span class="status" class:ok={systemInfo.gitVersion}>
                {systemInfo.gitVersion ? '✓' : '✗'}
              </span>
            </td>
            <td>{systemInfo.gitVersion || 'Required for version control'}</td>
          </tr>
          <tr>
            <td>Git LFS</td>
            <td>
              <span class="status" class:ok={systemInfo.gitLFSInstalled}>
                {systemInfo.gitLFSInstalled ? '✓' : '✗'}
              </span>
            </td>
            <td>{systemInfo.gitLFSInstalled ? 'Installed' : 'Required for large file storage'}</td>
          </tr>
          <tr>
            <td>Docker</td>
            <td>
              <span class="status" class:ok={systemInfo.dockerVersion}>
                {systemInfo.dockerVersion ? '✓' : '⚠'}
              </span>
            </td>
            <td>{systemInfo.dockerVersion || 'Optional for containerized models'}</td>
          </tr>
          <tr>
            <td>GPU</td>
            <td>
              <span class="status" class:ok={systemInfo.gpuSupport}>
                {systemInfo.gpuSupport ? '✓' : '⚠'}
              </span>
            </td>
            <td>{systemInfo.gpuSupport ? 'Available' : 'No GPU detected'}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="system-actions">
      <button class="btn-secondary" on:click={refresh}> Refresh </button>
      <button class="btn-secondary" on:click={copyToClipboard}>
        {copied ? 'Copied!' : 'Copy to Clipboard'}
      </button>
    </div>
  {/if}
</div>

<style>
  .system-info {
    max-width: 800px;
  }

  h2 {
    margin: 0 0 2rem 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  h3 {
    margin: 2rem 0 1rem 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .error {
    padding: 1rem;
    margin-bottom: 1rem;
    background: var(--color-error-bg);
    color: var(--color-error);
    border: 1px solid var(--color-error);
    border-radius: 4px;
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .info-item.full-width {
    grid-column: 1 / -1;
  }

  .info-item label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .info-item .value {
    font-size: 1rem;
    font-weight: 500;
  }

  .info-item code {
    padding: 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-family: var(--font-mono);
    font-size: 0.875rem;
    word-break: break-all;
  }

  .value.installed {
    color: var(--color-success);
  }

  .value.not-installed {
    color: var(--color-error);
  }

  .diagnostics {
    margin: 3rem 0 2rem 0;
  }

  .requirements-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
  }

  .requirements-table th,
  .requirements-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
  }

  .requirements-table th {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .requirements-table td {
    font-size: 0.875rem;
  }

  .status {
    display: inline-block;
    width: 1.5rem;
    height: 1.5rem;
    line-height: 1.5rem;
    text-align: center;
    border-radius: 50%;
    background: var(--bg-secondary);
    font-weight: bold;
  }

  .status.ok {
    background: var(--color-success-bg);
    color: var(--color-success);
  }

  .system-actions {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border-color);
  }

  .btn-secondary {
    padding: 0.5rem 1.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-secondary:hover {
    background: var(--bg-hover);
  }
</style>
