import { writable, derived } from 'svelte/store';
import { get } from 'svelte/store';

export interface CollaborationUser {
  userId: string;
  userName: string;
  joinedAt: string;
  lastActivity: string;
  color: string;
}

export interface CursorPosition {
  x: number;
  y: number;
  color: string;
  lastUpdate: string;
}

export interface CollaborationState {
  isConnected: boolean;
  connectionId: string | null;
  projectId: string | null;
  userId: string | null;
  users: CollaborationUser[];
  cursors: Record<string, CursorPosition>;
  messages: CollaborationMessage[];
  selections: Record<string, string[]>;
  error: string | null;
}

export interface CollaborationMessage {
  id: string;
  type: 'canvas_update' | 'cursor_move' | 'selection' | 'chat' | 'user_joined' | 'user_left';
  userId: string;
  userName: string;
  timestamp: string;
  data: any;
}

export interface CanvasUpdateMessage {
  type: 'canvas_update';
  update: {
    action: 'add' | 'remove' | 'update' | 'move';
    nodes?: any[];
    edges?: any[];
    viewport?: any;
  };
}

class CollaborationService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  public store = writable<CollaborationState>({
    isConnected: false,
    connectionId: null,
    projectId: null,
    userId: null,
    users: [],
    cursors: {},
    messages: [],
    selections: {},
    error: null
  });

  public userCount = derived(this.store, $store => $store.users.length);
  public isActive = derived(this.store, $store => $store.isConnected && $store.projectId !== null);

  async connect(projectId: string): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `ws://localhost:8000/api/v1/collaboration/ws/${projectId}`;
    this.ws = new WebSocket(wsUrl);

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Connection timeout'));
      }, 5000);

      this.ws!.onopen = () => {
        clearTimeout(timeout);
        this.handleConnectionOpen();
        resolve();
      };

      this.ws!.onmessage = (event) => {
        this.handleMessage(JSON.parse(event.data));
      };

      this.ws!.onclose = (event) => {
        this.handleConnectionClose(event);
      };

      this.ws!.onerror = (error) => {
        clearTimeout(timeout);
        this.handleConnectionError(error);
        reject(error);
      };
    });
  }

  disconnect(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.store.update(state => ({
      ...state,
      isConnected: false,
      connectionId: null,
      projectId: null,
      users: [],
      cursors: {},
      messages: [],
      selections: {}
    }));
  }

  sendCanvasUpdate(update: CanvasUpdateMessage['update']): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const message: CanvasUpdateMessage = {
      type: 'canvas_update',
      update
    };

    this.ws.send(JSON.stringify(message));
  }

  sendCursorMove(position: { x: number; y: number }): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.ws.send(JSON.stringify({
      type: 'cursor_move',
      position
    }));
  }

  sendSelection(selection: string[]): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.ws.send(JSON.stringify({
      type: 'selection',
      selection
    }));
  }

  sendChat(message: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.ws.send(JSON.stringify({
      type: 'chat',
      message
    }));
  }

  private handleConnectionOpen(): void {
    this.store.update(state => ({ ...state, isConnected: true, error: null }));
    this.startHeartbeat();
    this.reconnectAttempts = 0;
  }

  private handleConnectionClose(event: CloseEvent): void {
    this.store.update(state => ({
      ...state,
      isConnected: false,
      connectionId: null,
      error: `Connection closed: ${event.reason || 'Unknown reason'}`
    }));

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    this.attemptReconnect();
  }

  private handleConnectionError(error: Event): void {
    this.store.update(state => ({
      ...state,
      isConnected: false,
      error: 'Connection failed'
    }));
  }

  private handleMessage(message: any): void {
    switch (message.type) {
      case 'init':
        this.handleInit(message);
        break;
      case 'user_joined':
        this.handleUserJoined(message);
        break;
      case 'user_left':
        this.handleUserLeft(message);
        break;
      case 'cursor_move':
        this.handleCursorMove(message);
        break;
      case 'selection':
        this.handleSelection(message);
        break;
      case 'canvas_update':
        this.handleCanvasUpdate(message);
        break;
      case 'chat':
        this.handleChat(message);
        break;
    }
  }

  private handleInit(message: any): void {
    this.store.update(state => ({
      ...state,
      userId: message.user_id,
      users: message.users || [],
      cursors: message.cursor_positions || {},
      error: null
    }));
  }

  private handleUserJoined(message: any): void {
    this.store.update(state => {
      const existingUser = state.users.find(u => u.userId === message.user.user_id);
      if (!existingUser) {
        return {
          ...state,
          users: [...state.users, {
            userId: message.user.user_id,
            userName: message.user.user_name,
            joinedAt: message.user.joined_at,
            lastActivity: message.user.joined_at,
            color: this.generateUserColor(message.user.user_id)
          }]
        };
      }
      return state;
    });
  }

  private handleUserLeft(message: any): void {
    this.store.update(state => ({
      ...state,
      users: state.users.filter(u => u.userId !== message.user_id),
      cursors: { ...state.cursors },
      selections: { ...state.selections }
    }));
    
    // Remove user's cursor and selection
    this.store.update(state => {
      const newCursors = { ...state.cursors };
      delete newCursors[message.user_id];
      
      const newSelections = { ...state.selections };
      delete newSelections[message.user_id];
      
      return {
        ...state,
        cursors: newCursors,
        selections: newSelections
      };
    });
  }

  private handleCursorMove(message: any): void {
    this.store.update(state => ({
      ...state,
      cursors: {
        ...state.cursors,
        [message.user_id]: {
          ...message.position,
          color: message.user_id === state.userId ? '#3b82f6' : this.generateUserColor(message.user_id),
          lastUpdate: message.timestamp
        }
      }
    }));
  }

  private handleSelection(message: any): void {
    this.store.update(state => ({
      ...state,
      selections: {
        ...state.selections,
        [message.user_id]: message.selection
      }
    }));
  }

  private handleCanvasUpdate(message: any): void {
    // This would integrate with canvas store updates
    console.log('Received canvas update:', message);
  }

  private handleChat(message: any): void {
    const collaborationMessage: CollaborationMessage = {
      id: `${Date.now()}-${Math.random()}`,
      type: 'chat',
      userId: message.user_id,
      userName: message.user_name,
      timestamp: message.timestamp,
      data: { message: message.message }
    };

    this.store.update(state => ({
      ...state,
      messages: [...state.messages, collaborationMessage]
    }));
  }

  private generateUserColor(userId: string): string {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
      '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD',
      '#00D2D3', '#FF9F43', '#10AC84', '#EE5A24'
    ];

    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = userId.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  private async attemptReconnect(): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.store.update(state => ({
        ...state,
        error: 'Max reconnection attempts reached'
      }));
      return;
    }

    this.reconnectAttempts++;
    
    setTimeout(() => {
      const currentState = get(this.store);
      if (currentState.projectId) {
        this.connect(currentState.projectId).catch(() => {
          // Already handled by attemptReconnect
        });
      }
    }, this.reconnectDelay * this.reconnectAttempts);
  }
}

export const collaborationService = new CollaborationService();