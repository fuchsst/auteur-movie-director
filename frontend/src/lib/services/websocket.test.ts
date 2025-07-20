/**
 * Tests for WebSocket service
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocketService } from './websocket';
import { wsState } from '$lib/stores';
import { get } from 'svelte/store';
import { MessageType } from '$lib/types/websocket';

// Mock SvelteKit's browser check
vi.mock('$app/environment', () => ({
  browser: true
}));

// Mock WebSocket
class MockWebSocket {
  url: string;
  readyState: number = WebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => this.simulateOpen(), 0);
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: 1000 }));
    }
  }

  simulateOpen() {
    this.readyState = WebSocket.OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
  }

  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(
        new MessageEvent('message', {
          data: JSON.stringify(data)
        })
      );
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Replace global WebSocket with mock
(global as any).WebSocket = MockWebSocket;

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockWebSocket: MockWebSocket | null = null;
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    // Save original WebSocket
    originalWebSocket = global.WebSocket;

    // Replace WebSocket with our mock that captures instances
    (global as any).WebSocket = class extends MockWebSocket {
      constructor(url: string) {
        super(url);
        mockWebSocket = this;
      }
    };

    service = new WebSocketService('ws://localhost:8000/ws');
    vi.clearAllMocks();

    // Reset store state
    wsState.set({
      connected: false,
      connecting: false,
      error: null,
      reconnectAttempts: 0,
      lastHeartbeat: null
    });
  });

  afterEach(() => {
    service.disconnect();
    vi.clearAllTimers();
    mockWebSocket = null;
    // Restore original WebSocket
    global.WebSocket = originalWebSocket;
  });

  it('should connect to WebSocket', async () => {
    service.connect('test-project-id');

    // Should be connecting
    let state = get(wsState);
    expect(state.connecting).toBe(true);
    expect(state.connected).toBe(false);

    // Wait for connection
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Should be connected
    state = get(wsState);
    expect(state.connected).toBe(true);
    expect(state.connecting).toBe(false);
  });

  it('should handle incoming messages', async () => {
    const handler = vi.fn();
    service.on(MessageType.TASK_PROGRESS, handler);

    service.connect('test-project-id');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Mock WebSocket is already captured

    // Simulate incoming message
    const payload = {
      task_id: 'test-task',
      progress: 0.5,
      message: 'Processing...'
    };

    mockWebSocket?.simulateMessage({
      type: MessageType.TASK_PROGRESS,
      payload,
      timestamp: new Date().toISOString()
    });

    expect(handler).toHaveBeenCalledWith(payload);
  });

  it('should queue messages when disconnected', async () => {
    const sendSpy = vi.spyOn(MockWebSocket.prototype, 'send');

    // Send message before connecting
    service.send(MessageType.HEARTBEAT, {});

    // Should not send immediately
    expect(sendSpy).not.toHaveBeenCalled();

    // Connect
    service.connect('test-project-id');

    // Wait for connection and queue processing
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(sendSpy).toHaveBeenCalled();
  });

  it('should handle connection errors', async () => {
    service.connect('test-project-id');
    await new Promise((resolve) => setTimeout(resolve, 10));

    mockWebSocket?.simulateError();

    const state = get(wsState);
    expect(state.error).toBe('Connection error');
    expect(state.connected).toBe(false);
  });

  it('should reconnect with exponential backoff', async () => {
    vi.useFakeTimers();

    service.connect('test-project-id');
    await vi.advanceTimersByTimeAsync(10);

    // Simulate abnormal close
    if (mockWebSocket) {
      mockWebSocket.readyState = WebSocket.CLOSED;
      if (mockWebSocket.onclose) {
        mockWebSocket.onclose(new CloseEvent('close', { code: 1006 }));
      }
    }

    // Should schedule reconnect
    const state = get(wsState);
    expect(state.connected).toBe(false);
    expect(state.reconnectAttempts).toBe(1);

    // Advance time to trigger reconnect
    await vi.advanceTimersByTimeAsync(1000);

    vi.useRealTimers();
  });

  it('should handle heartbeat messages', async () => {
    service.connect('test-project-id');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Simulate heartbeat message
    mockWebSocket?.simulateMessage({
      type: MessageType.HEARTBEAT,
      payload: {},
      timestamp: new Date().toISOString()
    });

    const state = get(wsState);
    expect(state.lastHeartbeat).toBeInstanceOf(Date);
  });

  it('should unsubscribe handlers', async () => {
    const handler = vi.fn();
    const unsubscribe = service.on(MessageType.TASK_PROGRESS, handler);

    service.connect('test-project-id');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Unsubscribe
    unsubscribe();

    // Send message
    mockWebSocket?.simulateMessage({
      type: MessageType.TASK_PROGRESS,
      payload: {},
      timestamp: new Date().toISOString()
    });

    // Handler should not be called
    expect(handler).not.toHaveBeenCalled();
  });
});
