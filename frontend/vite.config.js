import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    // Configure for container environment
    strictPort: true,
    hmr: {
      clientPort: 3000,
      host: 'localhost'
    }
  },
  // Optimize for development in containers
  optimizeDeps: {
    exclude: ['@sveltejs/kit', 'svelte']
  },
  // Environment variable prefix
  envPrefix: ['VITE_', 'PUBLIC_']
});
