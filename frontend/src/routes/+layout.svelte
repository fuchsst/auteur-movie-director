<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { currentProject } from '$lib/stores';
  import { websocket } from '$lib/services/websocket';
  import { initializeWebSocketHandlers } from '$lib/stores/websocket';
  import TaskProgress from '$lib/components/common/TaskProgress.svelte';

  // Initialize theme and environment
  onMount(() => {
    if (browser) {
      // Set dark theme by default
      document.documentElement.classList.add('dark');

      // Initialize WebSocket handlers
      initializeWebSocketHandlers();

      // Connect WebSocket when project is selected
      const unsubscribe = currentProject.subscribe(($project) => {
        if ($project) {
          websocket.connect($project.id);
        } else {
          websocket.disconnect();
        }
      });

      // Log environment info in development
      if (import.meta.env.DEV) {
        console.log('Auteur Movie Director Frontend', {
          api: import.meta.env.VITE_API_URL,
          ws: import.meta.env.VITE_WS_URL
        });
      }

      return () => {
        unsubscribe();
        websocket.disconnect();
      };
    }
  });
</script>

<slot />

<!-- Global components -->
<TaskProgress />
