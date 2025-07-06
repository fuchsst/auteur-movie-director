import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  // Consult https://kit.svelte.dev/docs/integrations#preprocessors
  // for more information about preprocessors
  preprocess: vitePreprocess(),

  kit: {
    // Use Node adapter for Docker deployment
    adapter: adapter({
      // Build for production
      out: 'build',
      precompress: false,
      envPrefix: ''
    }),

    // Configure for container environment
    csrf: {
      checkOrigin: false // Allow cross-origin in development
    },

    // Path aliases
    alias: {
      $components: './src/lib/components',
      $stores: './src/lib/stores',
      $types: './src/lib/types',
      $utils: './src/lib/utils',
      $api: './src/lib/api'
    }
  }
};

export default config;
