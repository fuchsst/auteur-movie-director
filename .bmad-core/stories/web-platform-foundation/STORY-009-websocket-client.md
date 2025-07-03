# Story: WebSocket Client

**Story ID**: STORY-009  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a frontend developer, I need a robust WebSocket client implementation that maintains a persistent connection to the backend, handles reconnection automatically, supports container restarts and distributed events, and dispatches real-time events to the UI components including Celery task progress.

## Acceptance Criteria

### Functional Requirements
- [ ] Establish WebSocket connection on app load
- [ ] Automatically reconnect on disconnection
- [ ] Subscribe to project-specific events
- [ ] Dispatch events to Svelte stores
- [ ] Handle connection state changes
- [ ] Process heartbeat messages
- [ ] Support Celery task progress events
- [ ] Handle distributed events via Redis pub/sub
- [ ] Persist connection state across container restarts

### Technical Requirements
- [ ] Implement exponential backoff for reconnection
- [ ] Queue messages during disconnection
- [ ] Type-safe message handling
- [ ] Integrate with Svelte stores
- [ ] Handle connection lifecycle events
- [ ] Support multiple event listeners
- [ ] Environment-based WebSocket URL configuration
- [ ] Container-aware reconnection logic
- [ ] Handle Docker networking (service names vs localhost)
- [ ] Support for typed events (structure changes, Git operations)
- [ ] Local storage for reconnection token persistence

### Connection States
- `connecting` - Initial connection attempt
- `connected` - Active connection
- `reconnecting` - Attempting to reconnect
- `disconnected` - No active connection
- `error` - Connection error occurred
- `suspended` - Container restart detected

## Implementation Notes

### WebSocket Store with Container Support
```typescript
// src/lib/stores/websocket.ts
import { writable, derived, get } from 'svelte/store';
import type { WSMessage } from '$types/websocket';
import { browser } from '$app/environment';

interface WebSocketState {
  status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected' | 'error' | 'suspended';
  error?: string;
  reconnectAttempts: number;
  sessionId?: string;
  lastHeartbeat?: number;
}

// Store for connection state
export const wsState = writable<WebSocketState>({
  status: 'disconnected',
  reconnectAttempts: 0
});

// Store for received messages
export const wsMessages = writable<WSMessage[]>([]);

// Store for Celery task progress
export const taskProgress = writable<Record<string, TaskProgress>>({});

interface TaskProgress {
  task_id: string;
  state: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  progress: number;
  message?: string;
  result?: any;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private messageQueue: any[] = [];
  private subscriptions = new Set<string>();
  private listeners = new Map<string, Set<Function>>();
  private sessionId: string | null = null;
  private containerCheckInterval: number | null = null;
  
  constructor(private baseUrl?: string) {}
  
  private getWebSocketUrl(): string {
    // Environment-based URL configuration
    if (this.baseUrl) return this.baseUrl;
    
    if (browser) {
      // Check for Docker environment
      const isDocker = window.location.hostname.includes('docker') || 
                      window.location.hostname === 'backend';
      
      if (isDocker) {
        // Use Docker service name
        return `ws://backend:8000/ws`;
      }
      
      // Use environment variable or default
      const wsUrl = import.meta.env.PUBLIC_WS_URL;
      if (wsUrl) return wsUrl;
      
      // Construct from current location
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const port = import.meta.env.PUBLIC_BACKEND_PORT || '8000';
      return `${protocol}//${host}:${port}/ws`;
    }
    
    return 'ws://localhost:8000/ws';
  }
  
  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    
    // Load session from local storage
    this.loadSession();
    
    wsState.update(s => ({ ...s, status: 'connecting' }));
    
    const url = this.getWebSocketUrl();
    
    try {
      this.ws = new WebSocket(url);
      this.setupEventHandlers();
      this.startContainerCheck();
    } catch (error) {
      this.handleError(error);
    }
  }
  
  private setupEventHandlers() {
    if (!this.ws) return;
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      
      // Generate or restore session ID
      if (!this.sessionId) {
        this.sessionId = this.generateSessionId();
      }
      
      wsState.update(s => ({ 
        status: 'connected', 
        reconnectAttempts: 0,
        error: undefined,
        sessionId: this.sessionId,
        lastHeartbeat: Date.now()
      }));
      
      // Send session info
      this.send({ 
        type: 'session.init', 
        session_id: this.sessionId,
        reconnect: this.hasStoredSession()
      });
      
      // Send queued messages
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift();
        this.send(message);
      }
      
      // Resubscribe to projects
      this.subscriptions.forEach(projectId => {
        this.send({ type: 'subscribe', project_id: projectId });
      });
      
      // Save session
      this.saveSession();
      
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
    
    // Handle specific message types
    switch (message.type) {
      case 'system.heartbeat':
        this.resetHeartbeat();
        wsState.update(s => ({ ...s, lastHeartbeat: Date.now() }));
        break;
        
      case 'task.progress':
        // Update Celery task progress
        const taskMsg = message as TaskProgressMessage;
        taskProgress.update(tasks => ({
          ...tasks,
          [taskMsg.task_id]: {
            task_id: taskMsg.task_id,
            state: taskMsg.state,
            progress: taskMsg.progress || 0,
            message: taskMsg.message,
            result: taskMsg.result
          }
        }));
        break;
        
      case 'structure.changed':
      case 'git.commit':
      case 'git.push':
        // These are distributed events from Redis
        console.log('Distributed event received:', message.type);
        break;
    }
    
    // Dispatch to listeners
    const listeners = this.listeners.get(message.type) || new Set();
    listeners.forEach(callback => callback(message));
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
    
    // Check if this is a container restart
    if (this.isContainerRestart()) {
      wsState.update(s => ({ ...s, status: 'suspended' }));
      // Shorter delay for container restarts
      const delay = 2000;
      this.reconnectTimer = window.setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, delay);
      return;
    }
    
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
    
    if (this.containerCheckInterval) {
      clearInterval(this.containerCheckInterval);
      this.containerCheckInterval = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.clearSession();
  }
  
  // Container awareness methods
  private startContainerCheck() {
    if (!browser) return;
    
    this.containerCheckInterval = window.setInterval(() => {
      const state = get(wsState);
      if (state.lastHeartbeat && Date.now() - state.lastHeartbeat > 60000) {
        // No heartbeat for 60 seconds, might be container restart
        console.log('Possible container restart detected');
        this.scheduleReconnect();
      }
    }, 10000);
  }
  
  private isContainerRestart(): boolean {
    const state = get(wsState);
    return state.lastHeartbeat ? Date.now() - state.lastHeartbeat > 60000 : false;
  }
  
  // Session persistence methods
  private generateSessionId(): string {
    return `ws-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
  
  private saveSession() {
    if (!browser) return;
    
    const sessionData = {
      sessionId: this.sessionId,
      subscriptions: Array.from(this.subscriptions),
      timestamp: Date.now()
    };
    
    localStorage.setItem('ws-session', JSON.stringify(sessionData));
  }
  
  private loadSession() {
    if (!browser) return;
    
    const stored = localStorage.getItem('ws-session');
    if (!stored) return;
    
    try {
      const sessionData = JSON.parse(stored);
      
      // Check if session is still valid (less than 24 hours old)
      if (Date.now() - sessionData.timestamp < 86400000) {
        this.sessionId = sessionData.sessionId;
        sessionData.subscriptions.forEach((sub: string) => {
          this.subscriptions.add(sub);
        });
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  }
  
  private hasStoredSession(): boolean {
    if (!browser) return false;
    return localStorage.getItem('ws-session') !== null;
  }
  
  private clearSession() {
    if (!browser) return;
    localStorage.removeItem('ws-session');
  }
}

// Create singleton instance
let client: WebSocketClient | null = null;

export function setupWebSocket(baseUrl?: string) {
  client = new WebSocketClient(baseUrl);
  client.connect();
  
  // Connect event handlers to stores
  client.on('project.created', (msg: WSMessage) => {
    // Update projects store
  });
  
  client.on('file.uploaded', (msg: WSMessage) => {
    // Update files store
  });
  
  // Handle distributed events
  client.on('structure.changed', (msg: WSMessage) => {
    // Refresh file structure
    console.log('Project structure changed:', msg);
  });
  
  client.on('git.commit', (msg: WSMessage) => {
    // Update Git status
    console.log('Git commit detected:', msg);
  });
  
  // Handle Celery task updates
  client.on('task.progress', (msg: TaskProgressMessage) => {
    // Progress is automatically updated in taskProgress store
    console.log(`Task ${msg.task_id}: ${msg.progress}%`);
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

export interface SessionEvent extends WSMessage {
  type: 'session.init' | 'session.restored';
  session_id: string;
  reconnect: boolean;
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

export interface TaskProgressMessage extends WSMessage {
  type: 'task.progress';
  task_id: string;
  state: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  progress?: number;
  message?: string;
  result?: any;
}

export interface StructureEvent extends WSMessage {
  type: 'structure.changed';
  project_id: string;
  changes: {
    added: string[];
    modified: string[];
    deleted: string[];
  };
}

export interface GitEvent extends WSMessage {
  type: 'git.commit' | 'git.push' | 'git.pull';
  project_id: string;
  ref?: string;
  message?: string;
  author?: string;
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
    error: 'error',
    suspended: 'warning'
  }[$wsState.status];
  
  $: statusIcon = {
    connecting: '⟳',
    connected: '●',
    reconnecting: '⟳',
    disconnected: '○',
    error: '⚠',
    suspended: '⏸'
  }[$wsState.status];
</script>

<div class="connection-status {statusClass}">
  <span class="indicator">{statusIcon}</span>
  <span class="text">
    {#if $wsState.status === 'connected'}
      Connected
      {#if $wsState.sessionId}
        <span class="session-id" title="Session ID: {$wsState.sessionId}">●</span>
      {/if}
    {:else if $wsState.status === 'connecting'}
      Connecting...
    {:else if $wsState.status === 'reconnecting'}
      Reconnecting... (Attempt {$wsState.reconnectAttempts})
    {:else if $wsState.status === 'suspended'}
      Container Restart Detected - Reconnecting...
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

### Integration Examples

#### Basic WebSocket Usage
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

#### Celery Task Progress Tracking
```svelte
<!-- src/lib/components/TaskProgress.svelte -->
<script lang="ts">
  import { taskProgress } from '$stores/websocket';
  
  export let taskId: string;
  
  $: task = $taskProgress[taskId];
  $: progressPercent = task?.progress || 0;
  $: isComplete = task?.state === 'SUCCESS';
  $: isFailed = task?.state === 'FAILURE';
</script>

{#if task}
  <div class="task-progress">
    <div class="task-header">
      <span class="task-id">{taskId}</span>
      <span class="task-state" class:success={isComplete} class:error={isFailed}>
        {task.state}
      </span>
    </div>
    
    {#if task.message}
      <div class="task-message">{task.message}</div>
    {/if}
    
    <div class="progress-bar">
      <div class="progress-fill" style="width: {progressPercent}%"></div>
    </div>
    
    {#if isComplete && task.result}
      <div class="task-result">
        Result: {JSON.stringify(task.result)}
      </div>
    {/if}
  </div>
{/if}

<style>
  .task-progress {
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
  }
  
  .progress-bar {
    height: 20px;
    background: #f0f0f0;
    border-radius: 10px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s ease;
  }
  
  .task-state.success { color: green; }
  .task-state.error { color: red; }
</style>
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
- [ ] Container restart detection works
- [ ] Session persistence across restarts
- [ ] Environment-based URL configuration
- [ ] Celery task progress updates received
- [ ] Distributed events from Redis handled
- [ ] Docker networking support verified

## Definition of Done
- [ ] WebSocket client implemented with all features
- [ ] Automatic reconnection with backoff working
- [ ] Message queuing during disconnection
- [ ] Integration with Svelte stores complete
- [ ] Connection status component created
- [ ] TypeScript types fully defined
- [ ] Container-aware reconnection logic implemented
- [ ] Session persistence via localStorage working
- [ ] Support for Celery task progress events
- [ ] Handling of distributed Redis events
- [ ] Docker networking compatibility verified
- [ ] All connection states properly handled

## Story Links
- **Depends On**: STORY-005-websocket-service, STORY-007-sveltekit-application-setup
- **Enhances**: All real-time UI updates
- **Related PRD**: PRD-001-web-platform-foundation