# Story: WebSocket Client

**Story ID**: STORY-009  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Small)  
**Priority**: High  

## Story Description
As a frontend developer, I need a robust WebSocket client implementation that maintains a persistent connection to the backend, handles reconnection automatically, and dispatches real-time events to the UI components.

## Acceptance Criteria

### Functional Requirements
- [ ] Establish WebSocket connection on app load
- [ ] Automatically reconnect on disconnection
- [ ] Subscribe to project-specific events
- [ ] Dispatch events to Svelte stores
- [ ] Handle connection state changes
- [ ] Process heartbeat messages

### Technical Requirements
- [ ] Implement exponential backoff for reconnection
- [ ] Queue messages during disconnection
- [ ] Type-safe message handling
- [ ] Integrate with Svelte stores
- [ ] Handle connection lifecycle events
- [ ] Support multiple event listeners

### Connection States
- `connecting` - Initial connection attempt
- `connected` - Active connection
- `reconnecting` - Attempting to reconnect
- `disconnected` - No active connection
- `error` - Connection error occurred

## Implementation Notes

### WebSocket Store
```typescript
// src/lib/stores/websocket.ts
import { writable, derived, get } from 'svelte/store';
import type { WSMessage } from '$types/websocket';

interface WebSocketState {
  status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected' | 'error';
  error?: string;
  reconnectAttempts: number;
}

// Store for connection state
export const wsState = writable<WebSocketState>({
  status: 'disconnected',
  reconnectAttempts: 0
});

// Store for received messages
export const wsMessages = writable<WSMessage[]>([]);

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private messageQueue: any[] = [];
  private subscriptions = new Set<string>();
  private listeners = new Map<string, Set<Function>>();
  
  constructor(private url: string) {}
  
  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    
    wsState.update(s => ({ ...s, status: 'connecting' }));
    
    try {
      this.ws = new WebSocket(this.url);
      this.setupEventHandlers();
    } catch (error) {
      this.handleError(error);
    }
  }
  
  private setupEventHandlers() {
    if (!this.ws) return;
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      wsState.update(s => ({ 
        status: 'connected', 
        reconnectAttempts: 0,
        error: undefined 
      }));
      
      // Send queued messages
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift();
        this.send(message);
      }
      
      // Resubscribe to projects
      this.subscriptions.forEach(projectId => {
        this.send({ type: 'subscribe', project_id: projectId });
      });
      
      // Start heartbeat
      this.startHeartbeat();
    };
    
    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSMessage;
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      wsState.update(s => ({ ...s, status: 'disconnected' }));
      this.stopHeartbeat();
      this.scheduleReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.handleError(error);
    };
  }
  
  private handleMessage(message: WSMessage) {
    // Store message
    wsMessages.update(messages => [...messages.slice(-100), message]);
    
    // Dispatch to listeners
    const listeners = this.listeners.get(message.type) || new Set();
    listeners.forEach(callback => callback(message));
    
    // Handle heartbeat
    if (message.type === 'system.heartbeat') {
      this.resetHeartbeat();
    }
  }
  
  private startHeartbeat() {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
      }
    }, 30000);
  }
  
  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
  
  private resetHeartbeat() {
    // Reset heartbeat timeout
  }
  
  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    
    const state = get(wsState);
    const delay = Math.min(1000 * Math.pow(2, state.reconnectAttempts), 30000);
    
    wsState.update(s => ({ 
      ...s, 
      status: 'reconnecting',
      reconnectAttempts: s.reconnectAttempts + 1 
    }));
    
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }
  
  private handleError(error: any) {
    wsState.update(s => ({ 
      ...s, 
      status: 'error',
      error: error.message || 'Connection failed'
    }));
  }
  
  send(data: any) {
    if (this.isConnected()) {
      this.ws!.send(JSON.stringify(data));
    } else {
      // Queue message for later
      this.messageQueue.push(data);
    }
  }
  
  subscribe(projectId: string) {
    this.subscriptions.add(projectId);
    this.send({ type: 'subscribe', project_id: projectId });
  }
  
  unsubscribe(projectId: string) {
    this.subscriptions.delete(projectId);
    this.send({ type: 'unsubscribe', project_id: projectId });
  }
  
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }
  
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
  
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Create singleton instance
let client: WebSocketClient | null = null;

export function setupWebSocket() {
  const wsUrl = import.meta.env.PUBLIC_WS_URL || 'ws://localhost:8000/ws';
  client = new WebSocketClient(wsUrl);
  client.connect();
  
  // Connect event handlers to stores
  client.on('project.created', (msg: WSMessage) => {
    // Update projects store
  });
  
  client.on('file.uploaded', (msg: WSMessage) => {
    // Update files store
  });
  
  return client;
}

export function getWebSocketClient(): WebSocketClient | null {
  return client;
}

// Derived store for connection status
export const isConnected = derived(wsState, $state => $state.status === 'connected');
```

### WebSocket Types
```typescript
// src/lib/types/websocket.ts
export interface WSMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

export interface ProjectEvent extends WSMessage {
  type: 'project.created' | 'project.updated' | 'project.deleted';
  project_id: string;
  data: any;
}

export interface FileEvent extends WSMessage {
  type: 'file.uploaded' | 'file.deleted';
  project_id: string;
  file: {
    name: string;
    path: string;
    size: number;
    asset_type: string;
  };
}

export interface ProcessEvent extends WSMessage {
  type: 'process.started' | 'process.progress' | 'process.completed';
  project_id: string;
  process_id: string;
  progress?: number;
  message?: string;
}
```

### Connection Status Component
```svelte
<!-- src/lib/components/ConnectionStatus.svelte -->
<script lang="ts">
  import { wsState } from '$stores/websocket';
  
  $: statusClass = {
    connecting: 'warning',
    connected: 'success',
    reconnecting: 'warning',
    disconnected: 'error',
    error: 'error'
  }[$wsState.status];
</script>

<div class="connection-status {statusClass}">
  <span class="indicator"></span>
  <span class="text">
    {#if $wsState.status === 'connected'}
      Connected
    {:else if $wsState.status === 'connecting'}
      Connecting...
    {:else if $wsState.status === 'reconnecting'}
      Reconnecting... (Attempt {$wsState.reconnectAttempts})
    {:else if $wsState.status === 'error'}
      Connection Error: {$wsState.error}
    {:else}
      Disconnected
    {/if}
  </span>
</div>

<style>
  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.875rem;
  }
  
  .indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
  }
  
  .success { color: var(--color-success); }
  .warning { color: var(--color-warning); }
  .error { color: var(--color-error); }
</style>
```

### Integration Example
```svelte
<!-- Using WebSocket in a component -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { getWebSocketClient } from '$stores/websocket';
  
  export let projectId: string;
  
  let unsubscribe: Function;
  
  onMount(() => {
    const client = getWebSocketClient();
    if (client) {
      // Subscribe to project updates
      client.subscribe(projectId);
      
      // Listen for file uploads
      unsubscribe = client.on('file.uploaded', (event) => {
        if (event.project_id === projectId) {
          console.log('File uploaded:', event.file);
          // Update UI
        }
      });
    }
  });
  
  onDestroy(() => {
    const client = getWebSocketClient();
    if (client) {
      client.unsubscribe(projectId);
    }
    unsubscribe?.();
  });
</script>
```

## Dependencies
- WebSocket service backend (STORY-005)
- SvelteKit application (STORY-007)
- TypeScript types defined

## Testing Criteria
- [ ] Connection establishes successfully
- [ ] Reconnection works with exponential backoff
- [ ] Messages are queued during disconnection
- [ ] Subscriptions persist across reconnections
- [ ] Event listeners fire correctly
- [ ] Connection status updates properly

## Definition of Done
- [ ] WebSocket client implemented with all features
- [ ] Automatic reconnection with backoff working
- [ ] Message queuing during disconnection
- [ ] Integration with Svelte stores complete
- [ ] Connection status component created
- [ ] TypeScript types fully defined

## Story Links
- **Depends On**: STORY-005-websocket-service, STORY-007-sveltekit-application-setup
- **Enhances**: All real-time UI updates
- **Related PRD**: PRD-001-web-platform-foundation