# Story: Real-time Collaborative Editing

**Story ID**: STORY-061  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 10 (Large - increased from 8)  
**Priority**: Critical  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker working in a team, I want real-time collaborative editing on the Production Canvas so that multiple creators can work together on the same story structure simultaneously with instant updates, conflict resolution, and visual presence indicators.

## Acceptance Criteria

### Core Collaboration Features
- [ ] **Real-time synchronization** of canvas state via WebSocket
- [ ] **Multi-cursor support** showing other users' cursor positions
- [ ] **User presence indicators** with name tags and colors
- [ ] **Instant updates** for node creation, movement, and deletion
- [ ] **Conflict resolution** for simultaneous edits
- [ ] **Operational transformation** for consistent state across clients

### User Experience
- [ ] **Smooth cursor animation** following other users' movements
- [ ] **Visual user identification** with avatars and colors
- [ ] **Activity indicators** showing what others are doing
- [ ] **Selection highlights** showing what others have selected
- [ ] **Typing indicators** for text editing
- [ ] **Connection status** showing who's online/offline

### Data Synchronization
- [ ] **Delta synchronization** sending only changed data
- [ ] **State reconciliation** for dropped connections
- [ ] **Optimistic updates** for responsive UI
- [ ] **Rollback capability** for failed operations
- [ ] **Version tracking** for audit trail
- [ ] **Offline capability** with sync on reconnection

### Performance & Reliability
- [ ] **Sub-200ms latency** for real-time collaboration
- [ ] **Graceful degradation** when WebSocket fails
- [ ] **Reconnection handling** with state restoration
- [ ] **Bandwidth optimization** for large canvases
- [ ] **Memory management** for long sessions
- [ ] **Error recovery** for sync conflicts

## Implementation Notes

### Technical Architecture
```typescript
// WebSocket collaboration protocol
interface CollaborationMessage {
  type: 'cursor_move' | 'node_create' | 'node_update' | 'node_delete' | 'edge_create' | 'edge_delete';
  userId: string;
  sessionId: string;
  timestamp: number;
  data: any;
  version: number;
}

// Operational transformation
interface Operation {
  type: 'add_node' | 'remove_node' | 'move_node' | 'update_node' | 'add_edge' | 'remove_edge';
  nodeId?: string;
  edgeId?: string;
  data?: any;
  position?: { x: number; y: number };
  userId: string;
  timestamp: number;
}

// User presence state
interface UserPresence {
  userId: string;
  name: string;
  color: string;
  cursor: { x: number; y: number };
  selection: string[];
  isActive: boolean;
  lastActivity: number;
}

// Collaboration state manager
class CollaborationManager {
  private websocket: WebSocket;
  private localState: CanvasState;
  private remoteState: Map<string, CanvasState>;
  private operationQueue: Operation[];
  
  async initialize(projectId: string): Promise<void> {
    this.websocket = new WebSocket(`/ws/canvas/${projectId}`);
    this.setupWebSocketHandlers();
    await this.syncInitialState();
  }

  async sendOperation(operation: Operation): Promise<void> {
    // Apply optimistically locally
    this.applyOperation(operation);
    
    // Send to server
    this.websocket.send(JSON.stringify({
      type: 'operation',
      operation,
      version: this.localState.version
    }));
  }

  private handleRemoteOperation(message: CollaborationMessage): void {
    // Apply with operational transformation
    const transformed = this.transformOperation(message.operation, this.localState);
    this.applyOperation(transformed);
  }
}
```

### Cursor Management System
```typescript
class CursorManager {
  private cursors: Map<string, UserCursor> = new Map();
  private animationFrame: number;

  updateCursor(userId: string, position: { x: number; y: number }): void {
    const cursor = this.cursors.get(userId);
    if (cursor) {
      cursor.targetPosition = position;
      this.animateCursor(cursor);
    }
  }

  private animateCursor(cursor: UserCursor): void {
    const step = () => {
      const dx = cursor.targetPosition.x - cursor.currentPosition.x;
      const dy = cursor.targetPosition.y - cursor.currentPosition.y;
      
      if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
        cursor.currentPosition.x += dx * 0.1;
        cursor.currentPosition.y += dy * 0.1;
        
        this.renderCursor(cursor);
        this.animationFrame = requestAnimationFrame(step);
      }
    };
    
    step();
  }
}
```

### Conflict Resolution System
```typescript
class ConflictResolver {
  resolveConflict(local: Operation, remote: Operation): Operation {
    // Operational transformation logic
    if (local.type === 'move_node' && remote.type === 'move_node' 
        && local.nodeId === remote.nodeId) {
      
      // Last writer wins with timestamp
      if (local.timestamp > remote.timestamp) {
        return local;
      } else {
        return remote;
      }
    }
    
    // Different operations can be merged
    if (this.canMerge(local, remote)) {
      return this.mergeOperations(local, remote);
    }
    
    return remote; // Default to remote
  }

  private canMerge(local: Operation, remote: Operation): boolean {
    // Operations that don't conflict
    return local.type !== remote.type || 
           (local.type === 'update_node' && remote.type === 'update_node' && local.nodeId !== remote.nodeId);
  }
}
```

### Real-time Components
```svelte
<!-- CollaborativeCursor component -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { collaborationStore } from '$lib/stores/collaboration';
  
  export let userId: string;
  
  let cursor: UserCursor;
  let isVisible = true;
  
  onMount(() => {
    const unsubscribe = collaborationStore.subscribeToCursor(userId, (newCursor) => {
      cursor = newCursor;
    });
    
    return unsubscribe;
  });
</script>

{#if cursor && isVisible}
  <div class="collaborative-cursor" 
       style="transform: translate({cursor.x}px, {cursor.y}px); --user-color: {cursor.color};">
    <div class="cursor-icon">🖱️</div>
    <div class="user-label">{cursor.name}</div>
  </div>
{/if}

<style>
  .collaborative-cursor {
    position: absolute;
    pointer-events: none;
    z-index: 1000;
    transition: transform 0.1s ease-out;
  }
  
  .cursor-icon {
    color: var(--user-color);
    font-size: 16px;
  }
  
  .user-label {
    position: absolute;
    top: -25px;
    left: 15px;
    background: var(--user-color);
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    white-space: nowrap;
  }
</style>
```

### WebSocket Manager
```typescript
class WebSocketManager {
  private socket: WebSocket;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  async connect(projectId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(`/ws/canvas/${projectId}`);
      
      this.socket.onopen = () => {
        this.reconnectAttempts = 0;
        resolve();
      };
      
      this.socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };
      
      this.socket.onclose = () => {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++;
            this.connect(projectId);
          }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
        }
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
    });
  }

  send(message: CollaborationMessage): void {
    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
    }
  }
}
```

### User Presence Component
```svelte
<!-- UserPresenceIndicator component -->
<script lang="ts">
  import { collaborationStore } from '$lib/stores/collaboration';
  
  $: users = $collaborationStore.users;
  $: activeUsers = users.filter(u => u.isActive);
</script>

<div class="user-presence-bar">
  <div class="presence-list">
    {#each activeUsers as user}
      <div class="user-indicator" style="--user-color: {user.color};">
        <div class="user-avatar">{user.name.charAt(0).toUpperCase()}</div>
        <span class="user-name">{user.name}</span>
        <div class="activity-indicator {user.activity}"></div>
      </div>
    {/each}
  </div>
  
  <div class="connection-status">
    {#if $collaborationStore.isConnected}
      <span class="connected">● Connected ({activeUsers.length} users)</span>
    {:else}
      <span class="disconnected">○ Disconnected</span>
    {/if}
  </div>
</div>
```

### Performance Optimizations
```typescript
class PerformanceOptimizer {
  private batchOperations: Operation[] = [];
  private batchTimeout: NodeJS.Timeout;

  batchOperation(operation: Operation): void {
    this.batchOperations.push(operation);
    
    clearTimeout(this.batchTimeout);
    this.batchTimeout = setTimeout(() => {
      this.flushBatch();
    }, 50); // 50ms batch window
  }

  private flushBatch(): void {
    if (this.batchOperations.length > 0) {
      const batch = this.batchOperations.splice(0);
      this.sendBatch(batch);
    }
  }

  optimizePayload(operations: Operation[]): Operation[] {
    // Remove redundant operations
    const uniqueOps = operations.filter((op, index, self) => 
      index === self.findIndex(o => o.nodeId === op.nodeId && o.type === op.type)
    );
    
    return uniqueOps;
  }
}
```

### Testing Requirements

#### Unit Tests
- [ ] WebSocket message handling
- [ ] Operational transformation accuracy
- [ ] Cursor animation smoothness
- [ ] Conflict resolution logic
- [ ] Performance optimization effectiveness

#### Integration Tests
- [ ] Multi-user synchronization
- [ ] Reconnection handling
- [ ] State consistency across clients
- [ ] Conflict resolution under load
- [ ] Performance under simultaneous edits

#### E2E Tests
- [ ] Complete collaborative workflow
- [ ] Multi-user canvas editing
- [ ] Real-time cursor tracking
- [ ] Conflict resolution scenarios
- [ ] Connection recovery

### Dependencies
- **STORY-053**: Svelte Flow Integration (for canvas foundation)
- **STORY-054**: Node System Architecture (for node operations)
- **STORY-055-060**: All story structure implementations (for content)
- **EPIC-001**: WebSocket infrastructure from EPIC-001
- **EPIC-003**: WebSocket gateway from EPIC-003

### Definition of Done
- [ ] Real-time synchronization working with <200ms latency
- [ ] Multi-cursor support with smooth animation
- [ ] User presence indicators functional
- [ ] Conflict resolution handling simultaneous edits
- [ ] Reconnection handling with state restoration
- [ ] Performance optimization for large canvases
- [ ] Connection status and error handling
- [ ] Documentation with usage examples provided
- [ ] Ready for STORY-062 (Progressive Disclosure System) implementation