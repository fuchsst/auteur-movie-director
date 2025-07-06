<script lang="ts">
  export let onClose: () => void;

  let activeTab = 'windows';
  const platforms = ['windows', 'macos', 'linux'] as const;
  type Platform = (typeof platforms)[number];
</script>

<div class="lfs-setup">
  <div class="header">
    <h2>Git LFS Setup Required</h2>
    <button class="close-btn" on:click={onClose} title="Close">×</button>
  </div>

  <p class="intro">
    Git Large File Storage (LFS) is required for managing media files efficiently. Without it, large
    files like videos, images, and AI models may slow down your repository.
  </p>

  <div class="setup-section">
    <h3>Installation Steps:</h3>

    <div class="platform-tabs">
      {#each platforms as platform}
        <button
          class="tab"
          class:active={activeTab === platform}
          on:click={() => (activeTab = platform)}
        >
          {platform === 'macos' ? 'macOS' : platform.charAt(0).toUpperCase() + platform.slice(1)}
        </button>
      {/each}
    </div>

    <div class="instructions">
      {#if activeTab === 'windows'}
        <div class="platform-content">
          <ol>
            <li>
              Download Git LFS from
              <a href="https://git-lfs.github.com/" target="_blank" rel="noopener">
                git-lfs.github.com
              </a>
            </li>
            <li>Run the installer (git-lfs-windows-*.exe)</li>
            <li>
              Open a terminal (Command Prompt or PowerShell) and run:
              <code>git lfs install</code>
            </li>
            <li>Restart the Auteur Movie Director application</li>
          </ol>
        </div>
      {:else if activeTab === 'macos'}
        <div class="platform-content">
          <ol>
            <li>
              Install via Homebrew:
              <code>brew install git-lfs</code>
            </li>
            <li>
              Run:
              <code>git lfs install</code>
            </li>
            <li>Restart the Auteur Movie Director application</li>
          </ol>
          <p class="alternative">
            Alternative: Download the installer from
            <a href="https://git-lfs.github.com/" target="_blank" rel="noopener">
              git-lfs.github.com
            </a>
          </p>
        </div>
      {:else if activeTab === 'linux'}
        <div class="platform-content">
          <ol>
            <li>
              Install via package manager:
              <ul>
                <li>
                  <strong>Ubuntu/Debian:</strong>
                  <code>sudo apt install git-lfs</code>
                </li>
                <li>
                  <strong>Fedora:</strong>
                  <code>sudo dnf install git-lfs</code>
                </li>
                <li>
                  <strong>Arch:</strong>
                  <code>sudo pacman -S git-lfs</code>
                </li>
              </ul>
            </li>
            <li>
              Run:
              <code>git lfs install</code>
            </li>
            <li>Restart the Auteur Movie Director application</li>
          </ol>
        </div>
      {/if}
    </div>
  </div>

  <div class="benefits">
    <h3>Why Git LFS?</h3>
    <ul>
      <li>Keeps your repository fast and responsive</li>
      <li>Handles large media files efficiently</li>
      <li>Reduces clone and fetch times</li>
      <li>Saves bandwidth with partial downloads</li>
    </ul>
  </div>

  <div class="actions">
    <button class="btn" on:click={onClose}>Skip for Now</button>
    <button class="btn btn-primary" on:click={() => window.location.reload()}>
      I've Installed Git LFS
    </button>
  </div>
</div>

<style>
  .lfs-setup {
    background: var(--bg-primary);
    border-radius: 8px;
    padding: 24px;
    max-width: 600px;
    margin: 0 auto;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  h2 {
    margin: 0;
    font-size: 24px;
    color: var(--text-primary);
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;
  }

  .close-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .intro {
    color: var(--text-secondary);
    margin-bottom: 24px;
    line-height: 1.6;
  }

  .setup-section {
    margin-bottom: 24px;
  }

  h3 {
    font-size: 18px;
    margin-bottom: 12px;
    color: var(--text-primary);
  }

  .platform-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
  }

  .tab {
    padding: 8px 16px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 14px;
    color: var(--text-secondary);
  }

  .tab:hover {
    background: var(--bg-hover);
    border-color: var(--border-hover);
  }

  .tab.active {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .instructions {
    background: var(--bg-secondary);
    border-radius: 4px;
    padding: 16px;
  }

  .platform-content ol {
    margin: 0;
    padding-left: 24px;
    line-height: 1.8;
  }

  .platform-content li {
    margin-bottom: 12px;
  }

  .platform-content ul {
    margin: 8px 0;
    padding-left: 24px;
  }

  .platform-content ul li {
    margin-bottom: 8px;
  }

  code {
    background: var(--bg-tertiary);
    padding: 4px 8px;
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 13px;
    color: var(--color-primary);
  }

  a {
    color: var(--color-primary);
    text-decoration: none;
  }

  a:hover {
    text-decoration: underline;
  }

  .alternative {
    margin-top: 12px;
    font-size: 13px;
    color: var(--text-secondary);
  }

  .benefits {
    background: var(--bg-tertiary-light);
    border-radius: 4px;
    padding: 16px;
    margin-bottom: 24px;
  }

  .benefits ul {
    margin: 0;
    padding-left: 24px;
    line-height: 1.8;
  }

  .benefits li {
    color: var(--text-secondary);
  }

  .actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .btn {
    padding: 8px 16px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    color: var(--text-primary);
  }

  .btn:hover {
    background: var(--bg-hover);
    border-color: var(--border-hover);
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
    border-color: var(--color-primary-hover);
  }
</style>
