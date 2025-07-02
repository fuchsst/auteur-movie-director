# Story: SvelteKit Application Setup

**Story ID**: STORY-007  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 2 (Small)  
**Priority**: High  

## Story Description
As a frontend developer, I need to set up the SvelteKit application with TypeScript, proper project structure, and development configuration so that we have a solid foundation for building the user interface.

## Acceptance Criteria

### Functional Requirements
- [ ] SvelteKit app runs with `npm run dev`
- [ ] TypeScript is properly configured
- [ ] Hot module replacement works during development
- [ ] Basic routing structure is established
- [ ] Static assets are served correctly
- [ ] Environment variables load from .env

### Technical Requirements
- [ ] Use SvelteKit with TypeScript template
- [ ] Configure Vite for optimal development
- [ ] Set up path aliases for clean imports
- [ ] Add CSS preprocessing (PostCSS/Tailwind)
- [ ] Configure API proxy for backend calls
- [ ] Set up basic error page (404, 500)

### Project Structure
```
frontend/
├── src/
│   ├── routes/              # Page components
│   │   ├── +layout.svelte   # Root layout
│   │   ├── +page.svelte     # Home/Gallery page
│   │   ├── +error.svelte    # Error page
│   │   └── project/
│   │       └── [id]/        # Dynamic project route
│   │           └── +page.svelte
│   ├── lib/                 # Shared code
│   │   ├── components/      # UI components
│   │   ├── stores/          # Svelte stores
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # Helper functions
│   ├── app.html            # HTML template
│   ├── app.css             # Global styles
│   └── app.d.ts            # App type definitions
├── static/                  # Static assets
│   ├── favicon.png
│   └── fonts/
├── tests/                   # Test files
├── svelte.config.js        # SvelteKit config
├── vite.config.ts          # Vite config
├── tsconfig.json           # TypeScript config
└── package.json            # Dependencies
```

## Implementation Notes

### SvelteKit Configuration
```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  
  kit: {
    adapter: adapter({
      out: 'build',
      precompress: false
    }),
    alias: {
      $components: 'src/lib/components',
      $stores: 'src/lib/stores',
      $types: 'src/lib/types',
      $utils: 'src/lib/utils'
    }
  }
};
```

### Vite Configuration
```typescript
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
});
```

### TypeScript Configuration
```json
// tsconfig.json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "strict": true,
    "moduleResolution": "bundler",
    "paths": {
      "$lib": ["./src/lib"],
      "$lib/*": ["./src/lib/*"]
    }
  }
}
```

### Root Layout
```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { setupWebSocket } from '$lib/stores/websocket';
  
  onMount(() => {
    // Initialize WebSocket connection
    setupWebSocket();
  });
</script>

<div class="app">
  <header>
    <h1>Generative Media Studio</h1>
    <nav>
      <a href="/">Projects</a>
      <a href="/settings">Settings</a>
    </nav>
  </header>
  
  <main>
    <slot />
  </main>
  
  <footer>
    <p>&copy; 2025 Generative Media Studio</p>
  </footer>
</div>

<style>
  .app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }
  
  main {
    flex: 1;
    padding: 2rem;
  }
</style>
```

### Environment Setup
```bash
# .env.example
PUBLIC_API_URL=http://localhost:8000
PUBLIC_WS_URL=ws://localhost:8000/ws
PUBLIC_APP_VERSION=1.0.0
```

### Type Definitions
```typescript
// src/lib/types/index.ts
export interface Project {
  id: string;
  name: string;
  created: string;
  modified: string;
  quality: 'draft' | 'standard' | 'premium';
  sizeBytes: number;
  fileCount: number;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  requestId: string;
  timestamp: string;
}
```

## Dependencies
- SvelteKit framework
- TypeScript
- Vite build tool
- PostCSS for styling
- @sveltejs/adapter-node for deployment

## Testing Criteria
- [ ] Development server starts successfully
- [ ] TypeScript compilation has no errors
- [ ] Hot reload updates changes instantly
- [ ] API proxy forwards requests correctly
- [ ] Static assets load properly
- [ ] Environment variables are accessible

## Definition of Done
- [ ] SvelteKit project created and configured
- [ ] TypeScript properly set up with strict mode
- [ ] Development proxy configured for API calls
- [ ] Basic layout and routing implemented
- [ ] Path aliases working for clean imports
- [ ] README updated with frontend setup instructions

## Story Links
- **Depends On**: STORY-001-development-environment-setup
- **Blocks**: STORY-008-project-gallery-view, STORY-009-websocket-client
- **Related PRD**: PRD-001-web-platform-foundation