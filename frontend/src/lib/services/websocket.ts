/**
 * WebSocket client service with automatic reconnection
 */

import { browser } from '$app/environment';
import { wsState } from '$lib/stores';
import { MessageType } from '$lib/types/websocket';
import type {
  WebSocketMessage,
  TaskProgressPayload,
  NodeExecutionPayload,
  FileEventPayload,
  GitEventPayload
} from '$lib/types/websocket';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private projectId: string | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private messageHandlers: Map<MessageType, Set<(payload: any) => void>> = new Map();

  constructor(url?: string) {
    this.url = url || import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  }

  /**
   * Connect to WebSocket for a specific project
   */
  connect(projectId: string) {
    if (!browser) return;

    this.projectId = projectId;
    this.disconnect();

    wsState.update((state) => ({ ...state, connecting: true, error: null }));

    try {
      const wsUrl = `${this.url}/${projectId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleError(error as Event);
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    wsState.update((state) => ({
      ...state,
      connected: false,
      connecting: false
    }));
  }

  /**
   * Send a message through WebSocket
   */
  send(type: MessageType, payload: any) {
    const message: WebSocketMessage = {
      type,
      payload,
      timestamp: new Date().toISOString()
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message if not connected
      this.messageQueue.push(message);
    }
  }

  /**
   * Register a message handler
   */
  on(type: MessageType, handler: (payload: any) => void) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(type);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen() {
    console.log('WebSocket connected');

    wsState.update((state) => ({
      ...state,
      connected: true,
      connecting: false,
      reconnectAttempts: 0
    }));

    // Reset reconnect delay
    this.reconnectDelay = 1000;

    // Start heartbeat
    this.startHeartbeat();

    // Send queued messages
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws?.send(JSON.stringify(message));
      }
    }
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent) {
    console.log('WebSocket closed:', event.code, event.reason);

    wsState.update((state) => ({
      ...state,
      connected: false,
      connecting: false
    }));

    // Stop heartbeat
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    // Attempt reconnection if not a normal closure
    if (event.code !== 1000 && this.projectId) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(event: Event) {
    console.error('WebSocket error:', event);

    wsState.update((state) => ({
      ...state,
      error: 'Connection error',
      connecting: false
    }));
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(event: MessageEvent) {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      // Handle heartbeat
      if (message.type === MessageType.HEARTBEAT) {
        wsState.update((state) => ({
          ...state,
          lastHeartbeat: new Date()
        }));
        return;
      }

      // Dispatch to registered handlers
      const handlers = this.messageHandlers.get(message.type);
      if (handlers) {
        handlers.forEach((handler) => handler(message.payload));
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Start heartbeat interval
   */
  private startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      this.send(MessageType.HEARTBEAT, {});
    }, 30000); // Send heartbeat every 30 seconds
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect() {
    if (this.reconnectTimer || !this.projectId) return;

    wsState.update((state) => ({
      ...state,
      reconnectAttempts: state.reconnectAttempts + 1
    }));

    console.log(`Reconnecting in ${this.reconnectDelay / 1000} seconds...`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.projectId) {
        this.connect(this.projectId);
      }
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
  }
}

// Create singleton instance
export const websocket = new WebSocketService();
