<script>
  import { onMount } from 'svelte';

  let connected = false;
  let backendStatus = 'checking...';

  onMount(async () => {
    // Check backend connection
    try {
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        connected = true;
        backendStatus = 'Connected';
      } else {
        backendStatus = 'Backend not responding';
      }
    } catch {
      backendStatus = 'Backend not running';
    }
  });
</script>

<main>
  <h1>Auteur Movie Director</h1>
  <p>Welcome to the director-centric AI-powered film production platform</p>

  <div class="status">
    <h2>System Status</h2>
    <p>Backend: <span class:connected>{backendStatus}</span></p>
  </div>

  <div class="getting-started">
    <h2>Getting Started</h2>
    <ol>
      <li>Ensure the backend is running: <code>npm run dev:backend</code></li>
      <li>Create a new project in the workspace</li>
      <li>Start building your film!</li>
    </ol>
  </div>
</main>

<style>
  main {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    font-family:
      system-ui,
      -apple-system,
      sans-serif;
  }

  h1 {
    color: #333;
    margin-bottom: 1rem;
  }

  .status {
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 8px;
    margin: 2rem 0;
  }

  .status span {
    font-weight: bold;
    color: #999;
  }

  .status span.connected {
    color: #4caf50;
  }

  .getting-started {
    margin-top: 2rem;
  }

  code {
    background: #f0f0f0;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
  }

  ol {
    line-height: 1.8;
  }
</style>
