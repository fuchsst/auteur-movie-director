/**
 * WebSocket event handling stores
 */

import { writable, derived } from 'svelte/store';
import type { Writable, Readable } from 'svelte/store';
import { websocket } from '$lib/services/websocket';
import { MessageType } from '$lib/types/websocket';
import type {
  TaskProgressPayload,
  NodeExecutionPayload,
  FileEventPayload,
  GitEventPayload
} from '$lib/types/websocket';

// Task progress tracking
export interface TaskProgress {
  [taskId: string]: TaskProgressPayload;
}

export const taskProgress: Writable<TaskProgress> = writable({});

// Node execution states
export interface NodeStates {
  [nodeId: string]: NodeExecutionPayload;
}

export const nodeStates: Writable<NodeStates> = writable({});

// Recent file events
export const fileEvents: Writable<FileEventPayload[]> = writable([]);

// Git status updates
export const gitEvents: Writable<GitEventPayload | null> = writable(null);

// Initialize WebSocket event handlers
export function initializeWebSocketHandlers() {
  // Task progress handler
  websocket.on(MessageType.TASK_PROGRESS, (payload: TaskProgressPayload) => {
    taskProgress.update((tasks) => ({
      ...tasks,
      [payload.task_id]: payload
    }));
  });

  // Task complete handler
  websocket.on(MessageType.TASK_COMPLETE, (payload: TaskProgressPayload) => {
    taskProgress.update((tasks) => ({
      ...tasks,
      [payload.task_id]: { ...payload, progress: 1.0 }
    }));

    // Remove completed task after 5 seconds
    setTimeout(() => {
      taskProgress.update((tasks) => {
        const { [payload.task_id]: _, ...rest } = tasks;
        return rest;
      });
    }, 5000);
  });

  // Task error handler
  websocket.on(MessageType.TASK_ERROR, (payload: TaskProgressPayload) => {
    taskProgress.update((tasks) => ({
      ...tasks,
      [payload.task_id]: { ...payload, progress: -1 }
    }));
  });

  // Node execution handlers
  websocket.on(MessageType.NODE_EXECUTING, (payload: NodeExecutionPayload) => {
    nodeStates.update((nodes) => ({
      ...nodes,
      [payload.node_id]: payload
    }));
  });

  websocket.on(MessageType.NODE_COMPLETE, (payload: NodeExecutionPayload) => {
    nodeStates.update((nodes) => ({
      ...nodes,
      [payload.node_id]: payload
    }));
  });

  websocket.on(MessageType.NODE_ERROR, (payload: NodeExecutionPayload) => {
    nodeStates.update((nodes) => ({
      ...nodes,
      [payload.node_id]: payload
    }));
  });

  // File event handlers
  websocket.on(MessageType.FILE_CREATED, (payload: FileEventPayload) => {
    fileEvents.update((events) => [payload, ...events].slice(0, 50)); // Keep last 50
  });

  websocket.on(MessageType.FILE_MODIFIED, (payload: FileEventPayload) => {
    fileEvents.update((events) => [payload, ...events].slice(0, 50));
  });

  websocket.on(MessageType.FILE_DELETED, (payload: FileEventPayload) => {
    fileEvents.update((events) => [payload, ...events].slice(0, 50));
  });

  // Git event handler
  websocket.on(MessageType.GIT_STATUS_CHANGED, (payload: GitEventPayload) => {
    gitEvents.set(payload);
  });
}

// Derived stores for easier access
export const activeTasks: Readable<TaskProgressPayload[]> = derived(taskProgress, ($taskProgress) =>
  Object.values($taskProgress)
);

export const executingNodes: Readable<string[]> = derived(nodeStates, ($nodeStates) =>
  Object.entries($nodeStates)
    .filter(([_, state]) => state.status === 'executing')
    .map(([id, _]) => id)
);

// Helper functions
export function clearTaskProgress(taskId: string) {
  taskProgress.update((tasks) => {
    const { [taskId]: _, ...rest } = tasks;
    return rest;
  });
}

export function clearNodeState(nodeId: string) {
  nodeStates.update((nodes) => {
    const { [nodeId]: _, ...rest } = nodes;
    return rest;
  });
}

export function clearFileEvents() {
  fileEvents.set([]);
}
