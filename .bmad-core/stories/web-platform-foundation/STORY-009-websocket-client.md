# Story: WebSocket Client

**Story ID**: STORY-009  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a frontend developer, I need a robust WebSocket client implementation that maintains a persistent connection to the backend, handles reconnection automatically, supports container restarts and distributed events, and dispatches real-time events to the UI components including Celery task progress. The client must support production canvas node state management, tracking generation progress with granular step descriptions, updating visual states for nodes based on backend events, and coordinating multi-agent creative workflows for the filmmaking pipeline.

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
- [ ] Track node execution states (generating, completed, error)
- [ ] Handle granular progress updates with step descriptions
- [ ] Update node visual states (borders, spinners, thumbnails)
- [ ] Support start_generation message dispatch from nodes
- [ ] Manage takes gallery updates on task completion
- [ ] Handle multi-agent task coordination events
- [ ] Support composite prompt assembly notifications
- [ ] Track emotional beat associations with generations
- [ ] Update narrative structure progress (Chapter/Scene/Shot)

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

### Agent Event Types
- `agent.assigned` - Creative agent assigned to task
- `agent.progress` - Agent task progress update
- `agent.completed` - Agent finished task
- `agent.handoff` - Agent passing work to next agent
- `prompt.composite` - Composite prompt assembled
- `narrative.beat` - Emotional beat reached

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

// Store for node execution states
export const nodeStates = writable<Record<string, NodeState>>({});

// Store for active generations
export const activeGenerations = writable<Set<string>>(new Set());

// Store for agent activities
export const agentActivities = writable<Record<string, AgentActivity>>({});

// Store for narrative progress
export const narrativeProgress = writable<NarrativeProgress>({});

interface TaskProgress {
  task_id: string;
  state: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  progress: number;
  message?: string;
  result?: any;
  node_id?: string;
  step?: string;
  total_steps?: number;
  current_step?: number;
}

interface NodeState {
  node_id: string;
  status: 'idle' | 'generating' | 'completed' | 'error';
  progress?: number;
  message?: string;
  error?: string;
  output_path?: string;
  thumbnail?: string;
  takes?: Take[];
  current_take?: number;
  // Filmmaking pipeline additions
  scene_id?: string;  // S001 format
  shot_id?: string;   // P001 format
  emotional_beat?: string;  // Current emotional beat
  assigned_agent?: string;  // Current agent working on this
}

interface AgentActivity {
  agent_type: 'Producer' | 'Screenwriter' | 'CastingDirector' | 'ArtDirector' | 'Cinematographer' | 'SoundDesigner' | 'Editor';
  task_id: string;
  status: 'idle' | 'working' | 'completed';
  current_task?: string;
  progress?: number;
  vram_usage?: number;  // For Producer agent tracking
}

interface NarrativeProgress {
  current_chapter?: number;
  current_scene?: string;
  current_shot?: string;
  current_beat?: string;
  completed_beats: string[];
  structure_type: 'three-act' | 'hero-journey' | 'beat-sheet' | 'story-circle';
}

interface Take {
  id: string;
  path: string;
  thumbnail?: string;
  metadata?: any;
  created_at: string;
  // Filmmaking pipeline additions
  take_number: number;
  scene_id: string;
  shot_id: string;
  composite_prompt?: CompositePrompt;
  quality_preset: 'low' | 'standard' | 'high';
}

interface CompositePrompt {
  base_prompt: string;
  character_refs: string[];  // Character asset IDs
  style_refs: string[];      // Style asset IDs
  location_ref?: string;     // Location asset ID
  emotional_keywords: string[];  // From emotional beat
  agent_notes?: Record<string, string>;  // Notes from each agent
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
            result: taskMsg.result,
            node_id: taskMsg.node_id,
            step: taskMsg.step,
            total_steps: taskMsg.total_steps,
            current_step: taskMsg.current_step
          }
        }));
        
        // Update node state if node_id is present
        if (taskMsg.node_id) {
          this.updateNodeState(taskMsg);
        }
        break;
        
      case 'node.state_changed':
        const nodeMsg = message as NodeStateMessage;
        nodeStates.update(states => ({
          ...states,
          [nodeMsg.node_id]: {
            node_id: nodeMsg.node_id,
            status: nodeMsg.status,
            progress: nodeMsg.progress,
            message: nodeMsg.message,
            error: nodeMsg.error,
            output_path: nodeMsg.output_path,
            thumbnail: nodeMsg.thumbnail,
            takes: nodeMsg.takes,
            current_take: nodeMsg.current_take
          }
        }));
        
        // Update active generations
        if (nodeMsg.status === 'generating') {
          activeGenerations.update(s => s.add(nodeMsg.node_id));
        } else {
          activeGenerations.update(s => {
            s.delete(nodeMsg.node_id);
            return new Set(s);
          });
        }
        break;
        
      case 'generation.started':
        const genStartMsg = message as GenerationStartedMessage;
        activeGenerations.update(s => s.add(genStartMsg.node_id));
        nodeStates.update(states => ({
          ...states,
          [genStartMsg.node_id]: {
            ...states[genStartMsg.node_id],
            status: 'generating',
            progress: 0,
            message: 'Starting generation...'
          }
        }));
        break;
        
      case 'generation.completed':
        const genCompleteMsg = message as GenerationCompletedMessage;
        activeGenerations.update(s => {
          s.delete(genCompleteMsg.node_id);
          return new Set(s);
        });
        nodeStates.update(states => ({
          ...states,
          [genCompleteMsg.node_id]: {
            ...states[genCompleteMsg.node_id],
            status: 'completed',
            progress: 100,
            message: 'Generation complete',
            output_path: genCompleteMsg.output_path,
            thumbnail: genCompleteMsg.thumbnail,
            takes: genCompleteMsg.takes
          }
        }));
        break;
        
      case 'generation.error':
        const genErrorMsg = message as GenerationErrorMessage;
        activeGenerations.update(s => {
          s.delete(genErrorMsg.node_id);
          return new Set(s);
        });
        nodeStates.update(states => ({
          ...states,
          [genErrorMsg.node_id]: {
            ...states[genErrorMsg.node_id],
            status: 'error',
            error: genErrorMsg.error,
            message: genErrorMsg.message
          }
        }));
        break;
        
      // Agent coordination events
      case 'agent.assigned':
        const agentAssignMsg = message as AgentAssignedMessage;
        agentActivities.update(activities => ({
          ...activities,
          [agentAssignMsg.agent_type]: {
            agent_type: agentAssignMsg.agent_type,
            task_id: agentAssignMsg.task_id,
            status: 'working',
            current_task: agentAssignMsg.task_description,
            progress: 0
          }
        }));
        break;
        
      case 'agent.progress':
        const agentProgressMsg = message as AgentProgressMessage;
        agentActivities.update(activities => ({
          ...activities,
          [agentProgressMsg.agent_type]: {
            ...activities[agentProgressMsg.agent_type],
            progress: agentProgressMsg.progress,
            current_task: agentProgressMsg.current_step,
            vram_usage: agentProgressMsg.vram_usage
          }
        }));
        break;
        
      case 'agent.completed':
        const agentCompleteMsg = message as AgentCompletedMessage;
        agentActivities.update(activities => ({
          ...activities,
          [agentCompleteMsg.agent_type]: {
            ...activities[agentCompleteMsg.agent_type],
            status: 'completed',
            progress: 100
          }
        }));
        break;
        
      case 'prompt.composite':
        const promptMsg = message as CompositePromptMessage;
        // Update node with composite prompt info
        if (promptMsg.node_id) {
          nodeStates.update(states => ({
            ...states,
            [promptMsg.node_id]: {
              ...states[promptMsg.node_id],
              composite_prompt: promptMsg.composite_prompt
            }
          }));
        }
        break;
        
      case 'narrative.beat':
        const beatMsg = message as NarrativeBeatMessage;
        narrativeProgress.update(progress => ({
          ...progress,
          current_beat: beatMsg.beat_name,
          current_scene: beatMsg.scene_id,
          completed_beats: [...(progress.completed_beats || []), beatMsg.beat_name]
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
  
  // Node-specific methods
  private updateNodeState(taskMsg: TaskProgressMessage) {
    if (!taskMsg.node_id) return;
    
    nodeStates.update(states => {
      const currentState = states[taskMsg.node_id] || {
        node_id: taskMsg.node_id,
        status: 'idle'
      };
      
      // Map task state to node status
      let status: NodeState['status'] = currentState.status;
      if (taskMsg.state === 'STARTED' || taskMsg.state === 'PROGRESS') {
        status = 'generating';
      } else if (taskMsg.state === 'SUCCESS') {
        status = 'completed';
      } else if (taskMsg.state === 'FAILURE') {
        status = 'error';
      }
      
      return {
        ...states,
        [taskMsg.node_id]: {
          ...currentState,
          status,
          progress: taskMsg.progress || 0,
          message: taskMsg.step || taskMsg.message
        }
      };
    });
  }
  
  // Send generation request with filmmaking context
  startGeneration(
    nodeId: string, 
    params: any,
    context?: {
      scene_id?: string;
      shot_id?: string;
      emotional_beat?: string;
      character_refs?: string[];
      style_refs?: string[];
      location_ref?: string;
    }
  ) {
    this.send({
      type: 'start_generation',
      node_id: nodeId,
      params,
      context,
      timestamp: new Date().toISOString()
    });
  }
  
  // Cancel generation
  cancelGeneration(nodeId: string) {
    this.send({
      type: 'cancel_generation',
      node_id: nodeId,
      timestamp: new Date().toISOString()
    });
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
  node_id?: string;
  step?: string;
  total_steps?: number;
  current_step?: number;
}

export interface NodeStateMessage extends WSMessage {
  type: 'node.state_changed';
  node_id: string;
  status: 'idle' | 'generating' | 'completed' | 'error';
  progress?: number;
  message?: string;
  error?: string;
  output_path?: string;
  thumbnail?: string;
  takes?: any[];
  current_take?: number;
}

export interface GenerationStartedMessage extends WSMessage {
  type: 'generation.started';
  node_id: string;
  task_id: string;
}

export interface GenerationCompletedMessage extends WSMessage {
  type: 'generation.completed';
  node_id: string;
  task_id: string;
  output_path: string;
  thumbnail?: string;
  takes?: any[];
}

export interface GenerationErrorMessage extends WSMessage {
  type: 'generation.error';
  node_id: string;
  task_id: string;
  error: string;
  message?: string;
}

export interface StartGenerationMessage extends WSMessage {
  type: 'start_generation';
  node_id: string;
  params: any;
  context?: {
    scene_id?: string;
    shot_id?: string;
    emotional_beat?: string;
    character_refs?: string[];
    style_refs?: string[];
    location_ref?: string;
  };
}

// Agent coordination messages
export interface AgentAssignedMessage extends WSMessage {
  type: 'agent.assigned';
  agent_type: string;
  task_id: string;
  task_description: string;
  estimated_duration?: number;
}

export interface AgentProgressMessage extends WSMessage {
  type: 'agent.progress';
  agent_type: string;
  task_id: string;
  progress: number;
  current_step?: string;
  vram_usage?: number;  // For Producer agent
}

export interface AgentCompletedMessage extends WSMessage {
  type: 'agent.completed';
  agent_type: string;
  task_id: string;
  output?: any;
  handoff_to?: string;  // Next agent in pipeline
}

export interface CompositePromptMessage extends WSMessage {
  type: 'prompt.composite';
  node_id?: string;
  composite_prompt: {
    base_prompt: string;
    character_refs: string[];
    style_refs: string[];
    location_ref?: string;
    emotional_keywords: string[];
    agent_notes: Record<string, string>;
  };
}

export interface NarrativeBeatMessage extends WSMessage {
  type: 'narrative.beat';
  beat_name: string;
  scene_id: string;
  keywords: string[];
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
    
    {#if task.step}
      <div class="task-step">
        Step {task.current_step || 1} of {task.total_steps || 1}: {task.step}
      </div>
    {/if}
    
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
  
  .task-step {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
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

#### Node State Visual Management
```svelte
<!-- src/lib/components/canvas/NodeStateVisuals.svelte -->
<script lang="ts">
  import { nodeStates, activeGenerations } from '$stores/websocket';
  import { fade, scale } from 'svelte/transition';
  
  export let nodeId: string;
  
  $: nodeState = $nodeStates[nodeId] || { status: 'idle' };
  $: isGenerating = $activeGenerations.has(nodeId);
  $: borderClass = {
    idle: 'border-gray-300',
    generating: 'border-blue-500 animate-pulse',
    completed: 'border-green-500',
    error: 'border-red-500'
  }[nodeState.status];
</script>

<div class="node-container {borderClass}" class:generating={isGenerating}>
  <slot />
  
  {#if isGenerating}
    <div class="spinner-overlay" transition:fade>
      <div class="spinner" />
      {#if nodeState.progress}
        <div class="progress-text">{nodeState.progress}%</div>
      {/if}
      {#if nodeState.message}
        <div class="status-message">{nodeState.message}</div>
      {/if}
    </div>
  {/if}
  
  {#if nodeState.status === 'error'}
    <div class="error-indicator" transition:scale>
      <span class="error-icon">⚠️</span>
      {#if nodeState.error}
        <span class="error-text">{nodeState.error}</span>
      {/if}
    </div>
  {/if}
  
  {#if nodeState.status === 'completed' && nodeState.thumbnail}
    <div class="thumbnail-preview" transition:fade>
      <img src={nodeState.thumbnail} alt="Generated output" />
    </div>
  {/if}
</div>

<style>
  .node-container {
    position: relative;
    border-width: 2px;
    border-style: solid;
    transition: border-color 0.3s ease;
  }
  
  .node-container.generating {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
  }
  
  .spinner-overlay {
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 10;
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .progress-text {
    margin-top: 1rem;
    font-size: 1.25rem;
    font-weight: bold;
    color: #3b82f6;
  }
  
  .status-message {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: #6b7280;
    text-align: center;
    padding: 0 1rem;
  }
  
  .error-indicator {
    position: absolute;
    top: -10px;
    right: -10px;
    background: white;
    border-radius: 50%;
    padding: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .thumbnail-preview {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    overflow: hidden;
  }
  
  .thumbnail-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
</style>
```

#### Integration with Text-to-Image Node
```svelte
<!-- Example integration in a Text-to-Image node component -->
<script lang="ts">
  import { getWebSocketClient, nodeStates } from '$stores/websocket';
  import NodeStateVisuals from './NodeStateVisuals.svelte';
  import TakesGallery from './TakesGallery.svelte';
  
  export let nodeId: string;
  export let nodeData: any;
  
  $: nodeState = $nodeStates[nodeId];
  $: canGenerate = nodeState?.status !== 'generating';
  
  function handleGenerate() {
    const client = getWebSocketClient();
    if (client && canGenerate) {
      // Include filmmaking context
      const context = {
        scene_id: nodeData.scene_id,
        shot_id: nodeData.shot_id,
        emotional_beat: nodeData.emotional_beat,
        character_refs: nodeData.selected_characters || [],
        style_refs: nodeData.selected_styles || [],
        location_ref: nodeData.selected_location
      };
      
      client.startGeneration(nodeId, {
        prompt: nodeData.prompt,
        negative_prompt: nodeData.negativePrompt,
        width: nodeData.width,
        height: nodeData.height,
        steps: nodeData.steps,
        cfg_scale: nodeData.cfgScale,
        seed: nodeData.seed
      }, context);
    }
  }
  
  function handleCancel() {
    const client = getWebSocketClient();
    if (client) {
      client.cancelGeneration(nodeId);
    }
  }
</script>

<NodeStateVisuals {nodeId}>
  <div class="text-to-image-node">
    <div class="node-header">
      <h3>Text to Image</h3>
    </div>
    
    <div class="node-content">
      <!-- Node controls here -->
      
      <div class="actions">
        {#if nodeState?.status === 'generating'}
          <button on:click={handleCancel} class="cancel-btn">
            Cancel Generation
          </button>
        {:else}
          <button 
            on:click={handleGenerate} 
            disabled={!canGenerate}
            class="generate-btn"
          >
            Generate
          </button>
        {/if}
      </div>
      
      {#if nodeState?.takes && nodeState.takes.length > 0}
        <TakesGallery 
          takes={nodeState.takes} 
          currentTake={nodeState.current_take}
          on:select={(e) => handleTakeSelect(e.detail)}
        />
      {/if}
    </div>
  </div>
</NodeStateVisuals>
```

#### Agent Activity Monitor
```svelte
<!-- src/lib/components/AgentActivityMonitor.svelte -->
<script lang="ts">
  import { agentActivities, narrativeProgress } from '$stores/websocket';
  
  const agentIcons = {
    Producer: '🎬',
    Screenwriter: '✍️',
    CastingDirector: '👥',
    ArtDirector: '🎨',
    Cinematographer: '📹',
    SoundDesigner: '🎵',
    Editor: '✂️'
  };
</script>

<div class="agent-monitor">
  <div class="narrative-status">
    {#if $narrativeProgress.current_beat}
      <div class="current-beat">
        <span class="label">Current Beat:</span>
        <span class="value">{$narrativeProgress.current_beat}</span>
      </div>
    {/if}
    {#if $narrativeProgress.current_scene}
      <div class="current-scene">
        <span class="label">Scene:</span>
        <span class="value">{$narrativeProgress.current_scene}</span>
      </div>
    {/if}
  </div>
  
  <div class="agent-grid">
    {#each Object.entries($agentActivities) as [agentType, activity]}
      <div class="agent-card" class:active={activity.status === 'working'}>
        <div class="agent-header">
          <span class="agent-icon">{agentIcons[agentType]}</span>
          <span class="agent-name">{agentType}</span>
        </div>
        
        {#if activity.status === 'working'}
          <div class="agent-task">
            {activity.current_task}
          </div>
          <div class="agent-progress">
            <div class="progress-bar">
              <div class="progress-fill" style="width: {activity.progress || 0}%"></div>
            </div>
          </div>
          {#if activity.vram_usage}
            <div class="vram-usage">
              VRAM: {activity.vram_usage}GB
            </div>
          {/if}
        {:else if activity.status === 'completed'}
          <div class="agent-status completed">✓ Completed</div>
        {:else}
          <div class="agent-status idle">Idle</div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .agent-monitor {
    padding: 1rem;
    background: var(--bg-secondary);
    border-radius: 8px;
  }
  
  .narrative-status {
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border-radius: 4px;
  }
  
  .current-beat, .current-scene {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
  }
  
  .label {
    font-weight: 600;
    color: var(--text-secondary);
  }
  
  .agent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  .agent-card {
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    transition: all 0.3s ease;
  }
  
  .agent-card.active {
    border-color: var(--primary-color);
    box-shadow: 0 0 10px rgba(var(--primary-rgb), 0.2);
  }
  
  .agent-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .agent-icon {
    font-size: 1.5rem;
  }
  
  .agent-name {
    font-weight: 600;
  }
  
  .agent-task {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
  }
  
  .progress-bar {
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s ease;
  }
  
  .vram-usage {
    font-size: 0.75rem;
    color: var(--text-tertiary);
    margin-top: 0.25rem;
  }
  
  .agent-status {
    font-size: 0.875rem;
  }
  
  .agent-status.completed {
    color: var(--color-success);
  }
  
  .agent-status.idle {
    color: var(--text-secondary);
  }
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
- [ ] Node state changes update visual borders correctly
- [ ] Progress tracking shows granular step descriptions
- [ ] Generation spinner displays during processing
- [ ] Error states show appropriate visual indicators
- [ ] Thumbnails update on task completion
- [ ] Takes gallery refreshes with new outputs
- [ ] start_generation messages dispatch successfully
- [ ] Cancel generation functionality works

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
- [ ] Node state management stores implemented
- [ ] Visual state components (borders, spinners) created
- [ ] Progress tracking with step descriptions working
- [ ] Generation start/cancel methods implemented
- [ ] Takes gallery integration complete
- [ ] Error handling with visual feedback
- [ ] Thumbnail updates on completion

## Story Links
- **Depends On**: STORY-005-websocket-service, STORY-007-sveltekit-application-setup
- **Enhances**: All real-time UI updates
- **Related PRD**: PRD-001-web-platform-foundation