/**
 * Function Runner API Client
 * 
 * Main export file for the function runner client library
 */

// Main client
export { FunctionRunnerClient } from './client';

// Types
export type {
  // Core types
  FunctionTemplate,
  ResourceRequirements,
  QualityPreset,
  QualityLevel,
  Example,
  
  // Task types
  TaskSubmission,
  BatchTaskSubmission,
  SubmitTaskOptions,
  BatchOptions,
  TaskStatus,
  TaskProgress,
  TaskResult,
  TaskOutput,
  TaskHandle,
  
  // Batch types
  BatchHandle,
  BatchProgress,
  BatchResult,
  
  // Response types
  TaskSubmitResponse,
  BatchSubmitResponse,
  ListTemplatesOptions,
  
  // Upload types
  UploadOptions,
  UploadProgress,
  UploadResult,
  
  // Configuration
  FunctionRunnerConfig,
  CacheConfig,
  RetryConfig,
  
  // Other types
  RequestConfig,
  WebSocketClient,
  OfflineRequest
} from './types';

// Error class
export { FunctionRunnerError } from './types';

// Type guards
export { isTaskResult, isTaskProgress, isUploadProgress } from './types';

// Sub-modules (if needed directly)
export { FileUploadClient, ResumableUpload } from './upload';
export { TaskHandleImpl } from './taskHandle';
export { BatchHandleImpl } from './batchHandle';
export { RequestQueue } from './requestQueue';
export { RetryStrategy } from './retryStrategy';
export { ResponseCache } from './cache';
export { OfflineQueue } from './offline';

// Helper function to create client with websocket
import type { WebSocketClient } from './types';
import { websocket } from '$lib/stores/websocket';
import { get } from 'svelte/store';

/**
 * Create a function runner client with default configuration
 */
export function createFunctionRunnerClient(
  baseUrl: string = '',
  config?: Partial<FunctionRunnerConfig>
): FunctionRunnerClient {
  // Get websocket client from store
  const wsClient = get(websocket);
  
  // Create minimal websocket adapter
  const wsAdapter: WebSocketClient = {
    subscribe: (channel: string, handler: (message: any) => void) => {
      // Subscribe to websocket messages
      const unsubscribe = websocket.subscribe((ws) => {
        if (!ws.socket) return;
        
        const messageHandler = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            if (data.channel === channel) {
              handler(data);
            }
          } catch (error) {
            console.error('Failed to parse websocket message:', error);
          }
        };
        
        ws.socket.addEventListener('message', messageHandler);
        
        // Return unsubscribe function
        return () => {
          ws.socket?.removeEventListener('message', messageHandler);
        };
      });
      
      return unsubscribe;
    },
    
    send: (message: any) => {
      const ws = get(websocket);
      ws.send(message);
    },
    
    isConnected: () => {
      const ws = get(websocket);
      return ws.isConnected;
    }
  };
  
  return new FunctionRunnerClient({
    baseUrl,
    wsClient: wsAdapter,
    ...config
  });
}