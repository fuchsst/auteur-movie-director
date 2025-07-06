/**
 * WebSocket message types for real-time communication
 */

export interface WebSocketMessage {
  type: MessageType;
  payload: any;
  timestamp: string;
}

export enum MessageType {
  // Connection management
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  HEARTBEAT = 'heartbeat',

  // Task progress
  TASK_PROGRESS = 'task_progress',
  TASK_COMPLETE = 'task_complete',
  TASK_ERROR = 'task_error',

  // Node execution
  NODE_EXECUTING = 'node_executing',
  NODE_COMPLETE = 'node_complete',
  NODE_ERROR = 'node_error',

  // File system events
  FILE_CREATED = 'file_created',
  FILE_MODIFIED = 'file_modified',
  FILE_DELETED = 'file_deleted',

  // Git events
  GIT_STATUS_CHANGED = 'git_status_changed',
  GIT_COMMIT = 'git_commit',

  // Agent events (future)
  AGENT_STARTED = 'agent_started',
  AGENT_MESSAGE = 'agent_message',
  AGENT_COMPLETE = 'agent_complete'
}

export interface TaskProgressPayload {
  task_id: string;
  project_id: string;
  progress: number; // 0.0 to 1.0
  message: string;
  result?: any;
  error?: string;
}

export interface NodeExecutionPayload {
  node_id: string;
  status: 'executing' | 'complete' | 'error';
  message?: string;
  output?: any;
  error?: string;
}

export interface FileEventPayload {
  path: string;
  type: 'created' | 'modified' | 'deleted';
  size?: number;
  is_directory: boolean;
}

export interface GitEventPayload {
  project_id: string;
  branch: string;
  is_dirty: boolean;
  modified_count: number;
  untracked_count: number;
}

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  reconnectAttempts: number;
  lastHeartbeat: Date | null;
}
