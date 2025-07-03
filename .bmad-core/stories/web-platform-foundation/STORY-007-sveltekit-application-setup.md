# Story: SvelteKit Application Setup

**Story ID**: STORY-007  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a frontend developer, I need to set up the SvelteKit application with TypeScript, proper project structure, and Docker-first development configuration so that we have a containerized foundation for building the user interface with hot module replacement support.

## Acceptance Criteria

### Functional Requirements
- [ ] SvelteKit app runs in Docker container with HMR support
- [ ] TypeScript is properly configured for container environment
- [ ] Hot module replacement works with volume mounts
- [ ] Basic routing structure is established
- [ ] Static assets are served correctly
- [ ] Environment variables load from .env and docker-compose
- [ ] Three-panel layout displays correctly
- [ ] Panels are resizable with drag handles
- [ ] Panel sizes persist to local storage
- [ ] Container networking allows backend API communication

### Technical Requirements
- [ ] Create multi-stage Dockerfile for frontend
- [ ] Configure Docker volumes for source code hot-reloading
- [ ] Set up Vite for container networking (0.0.0.0 binding)
- [ ] Configure environment variables for backend URL
- [ ] Integrate with docker-compose orchestration
- [ ] Use SvelteKit with TypeScript template
- [ ] Set up path aliases for clean imports
- [ ] Add CSS preprocessing (PostCSS/Tailwind)
- [ ] Configure API proxy for backend calls
- [ ] Set up basic error page (404, 500)
- [ ] Implement hierarchical type definitions
- [ ] Create layout component structure
- [ ] Add stores for UI state management

### Project Structure
```
frontend/
├── src/
│   ├── routes/              # Page components
│   │   ├── +layout.svelte   # Root layout with three-panel structure
│   │   ├── +page.svelte     # Main application page
│   │   ├── +error.svelte    # Error page
│   │   └── project/
│   │       └── [id]/        # Dynamic project route
│   │           └── +page.svelte
│   ├── lib/                 # Shared code
│   │   ├── components/      # UI components
│   │   │   ├── layout/      # Layout components
│   │   │   │   ├── ThreePanelLayout.svelte
│   │   │   │   ├── LeftPanel.svelte
│   │   │   │   ├── CenterPanel.svelte
│   │   │   │   └── RightPanel.svelte
│   │   │   ├── project/     # Project components
│   │   │   │   └── ProjectBrowser.svelte
│   │   │   ├── asset/       # Asset components
│   │   │   │   └── AssetBrowser.svelte
│   │   │   ├── properties/  # Properties panel
│   │   │   │   └── PropertiesInspector.svelte
│   │   │   └── progress/    # Progress components
│   │   │       └── ProgressArea.svelte
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
├── Dockerfile              # Multi-stage build config
├── .dockerignore           # Docker ignore patterns
├── svelte.config.js        # SvelteKit config
├── vite.config.ts          # Vite config
├── tsconfig.json           # TypeScript config
└── package.json            # Dependencies
```

## Implementation Notes

### Docker Configuration

#### Multi-Stage Dockerfile
```dockerfile
# frontend/Dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 3: Development
FROM node:20-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm ci
# Install development tools
RUN npm install -g concurrently

# Expose HMR port
EXPOSE 3000 24678

# Set host to 0.0.0.0 for container access
ENV HOST=0.0.0.0
ENV PORT=3000

# Volume mount points for hot-reloading
VOLUME ["/app/src", "/app/static"]

CMD ["npm", "run", "dev"]

# Stage 4: Production
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/build ./build
COPY package*.json ./

EXPOSE 3000
ENV NODE_ENV=production
CMD ["node", "build"]
```

#### Docker Ignore
```
# .dockerignore
node_modules
build
.svelte-kit
.env.local
.env.*.local
npm-debug.log*
.DS_Store
*.log
coverage
.vscode
```

### Docker Compose Integration
```yaml
# docker-compose.yml (frontend service)
frontend:
  build:
    context: ./frontend
    target: development
  ports:
    - "3000:3000"
    - "24678:24678"  # HMR websocket port
  volumes:
    - ./frontend/src:/app/src:delegated
    - ./frontend/static:/app/static:delegated
    - ./frontend/package.json:/app/package.json
    - ./frontend/svelte.config.js:/app/svelte.config.js
    - ./frontend/vite.config.ts:/app/vite.config.ts
    - ./frontend/tsconfig.json:/app/tsconfig.json
    - frontend_node_modules:/app/node_modules
  environment:
    - NODE_ENV=development
    - PUBLIC_API_URL=http://backend:8000
    - PUBLIC_WS_URL=ws://backend:8000/ws
    - BACKEND_URL=http://backend:8000
  depends_on:
    - backend
  networks:
    - auteur-network

volumes:
  frontend_node_modules:
```

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
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [sveltekit()],
    server: {
      port: parseInt(env.PORT || '3000'),
      host: env.HOST || '0.0.0.0', // Required for Docker container
      strictPort: true,
      hmr: {
        clientPort: 24678,
        port: 24678,
        protocol: 'ws',
        host: 'localhost' // HMR host for client
      },
      proxy: {
        '/api': {
          target: env.BACKEND_URL || 'http://backend:8000',
          changeOrigin: true,
          secure: false
        },
        '/ws': {
          target: (env.BACKEND_URL || 'http://backend:8000').replace('http', 'ws'),
          ws: true,
          changeOrigin: true
        }
      }
    },
    // Optimize for container environment
    optimizeDeps: {
      entries: ['src/**/*.{js,ts,svelte}']
    }
  };
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
  import ThreePanelLayout from '$components/layout/ThreePanelLayout.svelte';
  
  onMount(() => {
    // Initialize WebSocket connection
    setupWebSocket();
  });
</script>

<ThreePanelLayout>
  <slot />
</ThreePanelLayout>
```

### Three-Panel Layout Component
```svelte
<!-- src/lib/components/layout/ThreePanelLayout.svelte -->
<script lang="ts">
  import LeftPanel from './LeftPanel.svelte';
  import CenterPanel from './CenterPanel.svelte';
  import RightPanel from './RightPanel.svelte';
  import { panelSizes } from '$stores/layout';
  
  let leftPanelWidth = $panelSizes.left;
  let rightPanelWidth = $panelSizes.right;
  let isResizing = false;
  
  function handleLeftResize(e: MouseEvent) {
    if (!isResizing) return;
    leftPanelWidth = Math.max(200, Math.min(400, e.clientX));
    $panelSizes.left = leftPanelWidth;
  }
  
  function handleRightResize(e: MouseEvent) {
    if (!isResizing) return;
    rightPanelWidth = Math.max(250, Math.min(500, window.innerWidth - e.clientX));
    $panelSizes.right = rightPanelWidth;
  }
</script>

<div class="three-panel-layout">
  <LeftPanel width={leftPanelWidth} />
  
  <div 
    class="resize-handle left"
    on:mousedown={() => isResizing = true}
  />
  
  <CenterPanel>
    <slot />
  </CenterPanel>
  
  <div 
    class="resize-handle right"
    on:mousedown={() => isResizing = true}
  />
  
  <RightPanel width={rightPanelWidth} />
</div>

<svelte:window 
  on:mousemove={isResizing ? (e) => {
    handleLeftResize(e);
    handleRightResize(e);
  } : null}
  on:mouseup={() => isResizing = false}
/>

<style>
  .three-panel-layout {
    display: flex;
    height: 100vh;
    width: 100%;
    overflow: hidden;
  }
  
  .resize-handle {
    width: 4px;
    background: var(--border-color);
    cursor: col-resize;
    flex-shrink: 0;
  }
  
  .resize-handle:hover {
    background: var(--border-hover);
  }
</style>
```

### Environment Setup
```bash
# .env.example (local development)
PUBLIC_API_URL=http://localhost:8000
PUBLIC_WS_URL=ws://localhost:8000/ws
PUBLIC_APP_VERSION=1.0.0
HOST=0.0.0.0
PORT=3000

# .env.docker (container development)
PUBLIC_API_URL=http://backend:8000
PUBLIC_WS_URL=ws://backend:8000/ws
PUBLIC_APP_VERSION=1.0.0
BACKEND_URL=http://backend:8000
HOST=0.0.0.0
PORT=3000
```

### Package.json Scripts
```json
{
  "name": "auteur-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite dev",
    "dev:docker": "docker-compose up frontend",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
    "lint": "eslint .",
    "format": "prettier --write ."
  },
  "type": "module",
  "dependencies": {
    "@sveltejs/adapter-node": "^2.0.0",
    "svelte": "^4.2.0"
  },
  "devDependencies": {
    "@sveltejs/kit": "^2.0.0",
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "@types/node": "^20.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

### Type Definitions
```typescript
// src/lib/types/index.ts

// Hierarchical project structure
export interface Project {
  id: string;
  name: string;
  created: string;
  modified: string;
  quality: 'low' | 'standard' | 'high';
  chapters: Chapter[];
  settings: ProjectSettings;
}

export interface Chapter {
  id: string;
  name: string;
  order: number;
  scenes: Scene[];
}

export interface Scene {
  id: string;
  name: string;
  order: number;
  shots: Shot[];
}

export interface Shot {
  id: string;
  name: string;
  order: number;
  takes: Take[];
  activeTakeId?: string;
}

export interface Take {
  id: string;
  number: number;
  filePath: string;
  thumbnail?: string;
  metadata: TakeMetadata;
}

export interface TakeMetadata {
  prompt: string;
  seed?: number;
  quality: string;
  generatedAt: string;
}

// Asset types
export interface Asset {
  id: string;
  name: string;
  category: AssetCategory;
  preview?: string;
  metadata: Record<string, any>;
}

export type AssetCategory = 'locations' | 'characters' | 'music' | 'styles';

// UI state types
export interface PanelSizes {
  left: number;
  right: number;
}

export interface ProjectSettings {
  fps: number;
  resolution: [number, number];
  colorSpace: string;
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

## Container Development Workflow

### Local Development with Docker
```bash
# Start the frontend container with HMR
docker-compose up frontend

# Or run with npm script
npm run dev:docker

# View logs
docker-compose logs -f frontend

# Rebuild after dependency changes
docker-compose build frontend

# Access the application
# http://localhost:3000
```

### Troubleshooting HMR in Docker
1. Ensure volumes are properly mounted
2. Check that Vite is binding to 0.0.0.0
3. Verify HMR port (24678) is exposed
4. Use delegated mount option for better performance on macOS

### Environment Variable Priority
1. Docker Compose environment section
2. .env.docker file
3. .env file
4. Default values in code

## Dependencies
- SvelteKit framework
- TypeScript
- Vite build tool
- PostCSS for styling
- @sveltejs/adapter-node for deployment
- Docker with multi-stage build support
- Docker Compose for orchestration

## Testing Criteria
- [ ] Docker container builds successfully
- [ ] Development server starts in container
- [ ] HMR works with volume-mounted source files
- [ ] TypeScript compilation has no errors
- [ ] Container can communicate with backend service
- [ ] Environment variables load from docker-compose
- [ ] Static assets load properly in container
- [ ] API proxy forwards requests to backend container
- [ ] No port conflicts with host system

## Definition of Done
- [ ] Multi-stage Dockerfile created and tested
- [ ] Docker Compose service configured
- [ ] SvelteKit project runs in containerized environment
- [ ] TypeScript properly set up with strict mode
- [ ] Vite configured for container networking
- [ ] HMR working with Docker volumes
- [ ] Environment variables properly configured
- [ ] Basic layout and routing implemented
- [ ] Path aliases working for clean imports
- [ ] README updated with Docker setup instructions

## Story Links
- **Depends On**: STORY-001-development-environment-setup
- **Blocks**: STORY-008-project-gallery-view, STORY-009-websocket-client
- **Related PRD**: PRD-001-web-platform-foundation