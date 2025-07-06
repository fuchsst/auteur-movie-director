# Story: SvelteKit Application Setup

**Story ID**: STORY-007  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: ✅ Completed  
**Completion Date**: 2025-07-06  

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
- [ ] Define typed socket system foundation
- [ ] Create base node component structure
- [ ] Implement progressive disclosure pattern
- [ ] Add visual state management utilities
- [ ] Prepare component organization for nodes

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
│   │   │   ├── nodes/       # Node system components (future)
│   │   │   │   ├── base/    # Base node components
│   │   │   │   │   ├── Node.svelte
│   │   │   │   │   ├── NodeHeader.svelte
│   │   │   │   │   ├── NodeSocket.svelte
│   │   │   │   │   ├── NodePreview.svelte
│   │   │   │   │   └── NodeStateIndicator.svelte
│   │   │   │   ├── sockets/ # Socket components
│   │   │   │   │   ├── InputSocket.svelte
│   │   │   │   │   ├── OutputSocket.svelte
│   │   │   │   │   └── SocketTypeIndicator.svelte
│   │   │   │   └── types/   # Node type implementations
│   │   │   ├── project/     # Project components
│   │   │   │   └── ProjectBrowser.svelte
│   │   │   ├── asset/       # Asset components
│   │   │   │   └── AssetBrowser.svelte
│   │   │   ├── properties/  # Properties panel
│   │   │   │   ├── PropertiesInspector.svelte
│   │   │   │   └── NodePropertiesPanel.svelte
│   │   │   └── progress/    # Progress components
│   │   │       └── ProgressArea.svelte
│   │   ├── stores/          # Svelte stores
│   │   │   ├── layout.ts    # Panel size management
│   │   │   ├── project.ts   # Project state
│   │   │   ├── nodes.ts     # Node graph state (future)
│   │   │   └── websocket.ts # WebSocket connection
│   │   ├── types/           # TypeScript types
│   │   │   ├── index.ts     # General types
│   │   │   ├── nodes.ts     # Node system types
│   │   │   └── sockets.ts   # Socket data types
│   │   └── utils/           # Helper functions
│   │       └── nodeUtils.ts # Node-related utilities
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

### Node System Preparation
While this story focuses on SvelteKit setup, it includes foundational preparations for the future node-based canvas system:
- Type definitions for sockets and nodes establish the data model
- Component structure under `nodes/` provides organized locations for future implementation
- CSS variables define a consistent design system for node visuals
- State management patterns prepare for reactive node graph updates
- Progressive disclosure components enable clean node UI with on-node controls vs properties panel

These preparations ensure smooth integration when implementing the Production Canvas in later stories.

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

// Hierarchical project structure (aligned with filmmaking pipeline)
export interface Project {
  id: string;
  name: string;
  created: string;
  modified: string;
  quality: 'low' | 'standard' | 'high';
  narrative: {
    structure: 'three-act' | 'hero-journey' | 'beat-sheet' | 'story-circle';
    chapters: Chapter[];
    emotionalBeats?: EmotionalBeat[];
  };
  assets: {
    characters: Asset[];
    styles: Asset[];
    locations: Asset[];
    music: Asset[];
  };
  settings: ProjectSettings;
}

export interface EmotionalBeat {
  id: string;
  beat: string;  // e.g., "Catalyst", "All Is Lost"
  sceneId: string;
  keywords: string[];  // Mood keywords for prompting
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

// Asset types (aligned with generative pipeline)
export interface Asset {
  id: string;
  name: string;
  category: AssetCategory;
  path: string;
  preview?: string;
  metadata: Record<string, any>;
  // For composite prompts
  triggerWord?: string;  // For LoRA models
  keywords?: string[];   // For style assets
}

export type AssetCategory = 'characters' | 'styles' | 'locations' | 'music';

// Creative documents
export interface CreativeDocument {
  id: string;
  type: CreativeDocType;
  name: string;
  path: string;
  content?: string;
  metadata: Record<string, any>;
}

export type CreativeDocType = 'treatment' | 'screenplay' | 'beat-sheet' | 'shot-list';

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

### Socket Type Definitions
```typescript
// src/lib/types/sockets.ts

// Core socket data types
export enum SocketDataType {
  // Basic types
  String = 'string',
  Number = 'number',
  Boolean = 'boolean',
  
  // Media types
  Image = 'image',
  Video = 'video',
  Audio = 'audio',
  
  // Asset types
  Character = 'character',
  Style = 'style',
  Location = 'location',
  
  // Structured types
  Prompt = 'prompt',
  Config = 'config',
  Seed = 'seed',
  
  // Special types
  Any = 'any',
  Trigger = 'trigger'
}

// Socket type configuration
export interface SocketTypeConfig {
  type: SocketDataType;
  label: string;
  color: string;
  icon?: string;
  validator?: (value: any) => boolean;
}

// Socket type registry
export const SOCKET_TYPES: Record<SocketDataType, SocketTypeConfig> = {
  [SocketDataType.String]: {
    type: SocketDataType.String,
    label: 'Text',
    color: '#4ade80', // green
  },
  [SocketDataType.Number]: {
    type: SocketDataType.Number,
    label: 'Number',
    color: '#60a5fa', // blue
  },
  [SocketDataType.Boolean]: {
    type: SocketDataType.Boolean,
    label: 'Boolean',
    color: '#f87171', // red
  },
  [SocketDataType.Image]: {
    type: SocketDataType.Image,
    label: 'Image',
    color: '#c084fc', // purple
  },
  [SocketDataType.Video]: {
    type: SocketDataType.Video,
    label: 'Video',
    color: '#f472b6', // pink
  },
  [SocketDataType.Audio]: {
    type: SocketDataType.Audio,
    label: 'Audio',
    color: '#fb923c', // orange
  },
  [SocketDataType.Character]: {
    type: SocketDataType.Character,
    label: 'Character',
    color: '#fbbf24', // amber
  },
  [SocketDataType.Style]: {
    type: SocketDataType.Style,
    label: 'Style',
    color: '#a78bfa', // violet
  },
  [SocketDataType.Location]: {
    type: SocketDataType.Location,
    label: 'Location',
    color: '#2dd4bf', // teal
  },
  [SocketDataType.Prompt]: {
    type: SocketDataType.Prompt,
    label: 'Prompt',
    color: '#4ade80', // green
  },
  [SocketDataType.Config]: {
    type: SocketDataType.Config,
    label: 'Config',
    color: '#94a3b8', // slate
  },
  [SocketDataType.Seed]: {
    type: SocketDataType.Seed,
    label: 'Seed',
    color: '#60a5fa', // blue
  },
  [SocketDataType.Any]: {
    type: SocketDataType.Any,
    label: 'Any',
    color: '#e5e7eb', // gray
  },
  [SocketDataType.Trigger]: {
    type: SocketDataType.Trigger,
    label: 'Trigger',
    color: '#facc15', // yellow
  }
};

// Socket connection state
export interface SocketConnection {
  fromNodeId: string;
  fromSocketId: string;
  toNodeId: string;
  toSocketId: string;
}
```

### Node Type Definitions
```typescript
// src/lib/types/nodes.ts

import type { SocketDataType } from './sockets';

// Base node interface
export interface BaseNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
  state: NodeState;
}

// Node execution state
export enum NodeState {
  Idle = 'idle',
  Running = 'running',
  Success = 'success',
  Error = 'error',
  Warning = 'warning'
}

// Node socket definition
export interface NodeSocket {
  id: string;
  name: string;
  type: SocketDataType;
  multiple?: boolean; // Can accept multiple connections
  required?: boolean;
  defaultValue?: any;
}

// Node definition
export interface NodeDefinition {
  type: string;
  category: string;
  label: string;
  description?: string;
  icon?: string;
  inputs: NodeSocket[];
  outputs: NodeSocket[];
  properties?: NodeProperty[];
  previewable?: boolean;
}

// Node property for properties panel
export interface NodeProperty {
  key: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'slider' | 'color';
  defaultValue?: any;
  options?: Array<{ label: string; value: any }>; // For select
  min?: number; // For number/slider
  max?: number; // For number/slider
  step?: number; // For slider
}

// Node instance in the graph
export interface NodeInstance extends BaseNode {
  definition: NodeDefinition;
  inputs: Record<string, any>; // Socket id -> value
  outputs: Record<string, any>; // Socket id -> value
  properties: Record<string, any>; // Property key -> value
  preview?: {
    type: 'image' | 'video' | 'text';
    data: any;
  };
}

// Node graph state
export interface NodeGraph {
  nodes: Record<string, NodeInstance>;
  connections: SocketConnection[];
  selectedNodeId?: string;
}
```

### Progressive Disclosure Pattern Components
```svelte
<!-- src/lib/components/nodes/base/Node.svelte -->
<script lang="ts">
  import type { NodeInstance } from '$types/nodes';
  import NodeHeader from './NodeHeader.svelte';
  import NodeSocket from './NodeSocket.svelte';
  import NodePreview from './NodePreview.svelte';
  import NodeStateIndicator from './NodeStateIndicator.svelte';
  
  export let node: NodeInstance;
  export let selected = false;
  
  $: stateClass = `node-${node.state}`;
  $: borderColor = getBorderColor(node.state);
  
  function getBorderColor(state: string) {
    switch (state) {
      case 'running': return 'var(--color-primary)';
      case 'success': return 'var(--color-success)';
      case 'error': return 'var(--color-error)';
      case 'warning': return 'var(--color-warning)';
      default: return 'var(--border-color)';
    }
  }
</script>

<div 
  class="node {stateClass}"
  class:selected
  style="--border-color: {borderColor}"
>
  <NodeHeader {node} />
  
  <div class="node-body">
    <div class="sockets inputs">
      {#each node.definition.inputs as socket}
        <NodeSocket 
          {socket} 
          value={node.inputs[socket.id]}
          direction="input"
        />
      {/each}
    </div>
    
    {#if node.previewable && node.preview}
      <NodePreview preview={node.preview} />
    {/if}
    
    <div class="sockets outputs">
      {#each node.definition.outputs as socket}
        <NodeSocket 
          {socket}
          value={node.outputs[socket.id]}
          direction="output"
        />
      {/each}
    </div>
  </div>
  
  <NodeStateIndicator state={node.state} />
</div>

<style>
  .node {
    position: absolute;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 8px;
    min-width: 200px;
    transition: border-color 0.2s;
  }
  
  .node.selected {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 1px var(--color-primary);
  }
  
  .node-body {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .sockets {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .node-running {
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
  }
</style>
```

### Global CSS Variables for Node System
```css
/* src/app.css - Node system design tokens */
:root {
  /* Color system for socket types */
  --socket-string: #4ade80;
  --socket-number: #60a5fa;
  --socket-boolean: #f87171;
  --socket-image: #c084fc;
  --socket-video: #f472b6;
  --socket-audio: #fb923c;
  --socket-character: #fbbf24;
  --socket-style: #a78bfa;
  --socket-location: #2dd4bf;
  --socket-any: #e5e7eb;
  --socket-trigger: #facc15;
  
  /* Node state colors */
  --node-idle: var(--border-color);
  --node-running: var(--color-primary);
  --node-success: var(--color-success);
  --node-error: var(--color-error);
  --node-warning: var(--color-warning);
  
  /* Node UI tokens */
  --node-bg: var(--bg-secondary);
  --node-header-bg: var(--bg-tertiary);
  --node-border-width: 2px;
  --node-border-radius: 8px;
  --node-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  --node-shadow-selected: 0 0 0 2px var(--color-primary);
  
  /* Socket sizes */
  --socket-size: 12px;
  --socket-border-width: 2px;
  
  /* Animation durations */
  --transition-fast: 150ms;
  --transition-normal: 250ms;
  --transition-slow: 400ms;
}

/* Dark theme overrides */
[data-theme="dark"] {
  --node-bg: var(--bg-secondary);
  --node-shadow: 0 2px 16px rgba(0, 0, 0, 0.3);
}
```

### Node State Management Store
```typescript
// src/lib/stores/nodes.ts
import { writable, derived } from 'svelte/store';
import type { NodeGraph, NodeInstance, SocketConnection } from '$types/nodes';

// Node graph state
export const nodeGraph = writable<NodeGraph>({
  nodes: {},
  connections: [],
  selectedNodeId: undefined
});

// Derived stores for specific queries
export const selectedNode = derived(
  nodeGraph,
  $graph => $graph.selectedNodeId ? $graph.nodes[$graph.selectedNodeId] : null
);

export const runningNodes = derived(
  nodeGraph,
  $graph => Object.values($graph.nodes).filter(node => node.state === 'running')
);

// Node operations
export function addNode(node: NodeInstance) {
  nodeGraph.update(graph => ({
    ...graph,
    nodes: { ...graph.nodes, [node.id]: node }
  }));
}

export function updateNodeState(nodeId: string, state: NodeState) {
  nodeGraph.update(graph => ({
    ...graph,
    nodes: {
      ...graph.nodes,
      [nodeId]: { ...graph.nodes[nodeId], state }
    }
  }));
}

export function connectNodes(connection: SocketConnection) {
  nodeGraph.update(graph => ({
    ...graph,
    connections: [...graph.connections, connection]
  }));
}

export function selectNode(nodeId: string | undefined) {
  nodeGraph.update(graph => ({
    ...graph,
    selectedNodeId: nodeId
  }));
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
- [ ] Socket type definitions compile without errors
- [ ] Node type definitions are properly typed
- [ ] CSS variables load correctly for theming
- [ ] Store subscriptions work as expected
- [ ] Component structure supports future node implementation

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
- [ ] Socket and node type system defined
- [ ] Base node component structure prepared
- [ ] Progressive disclosure pattern implemented
- [ ] Node state management store created
- [ ] CSS design tokens for nodes established
- [ ] README updated with Docker setup instructions

## Story Links
- **Depends On**: STORY-001-development-environment-setup
- **Blocks**: STORY-008-project-gallery-view, STORY-009-websocket-client
- **Related PRD**: PRD-001-web-platform-foundation

## Implementation Status

✅ **Completed Features:**
- Multi-stage Dockerfile for frontend with development and production targets
- Docker Compose integration with proper networking configuration
- SvelteKit app with TypeScript template and strict mode enabled
- Hot Module Replacement (HMR) working with Docker volume mounts
- Environment variable configuration for backend URL and WebSocket connections
- Three-panel layout components with resizable panels
- Basic routing structure with dynamic project routes
- Vite configuration for container networking (0.0.0.0 binding)
- Path aliases configured for clean imports (@components, @stores, @types, @utils)
- Type definitions for project hierarchy and filmmaking pipeline
- Socket and node type definitions for future canvas implementation
- Base node component structure and progressive disclosure patterns
- Node state management stores with WebSocket integration hooks
- CSS design tokens for node visual system
- Panel size persistence to local storage

### Implementation Notes:
- Successfully configured Docker container with HMR support on port 24678
- TypeScript strict mode enabled with comprehensive type definitions
- Three-panel layout implemented with drag-to-resize functionality
- Component structure prepared for future node-based canvas system
- Hierarchical project structure aligned with filmmaking pipeline (Chapter → Scene → Shot → Take)
- Socket type system established with color coding and validation
- Node state management prepared for real-time updates via WebSocket
- CSS variables defined for consistent theming across node components