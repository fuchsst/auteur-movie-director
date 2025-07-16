/**
 * Offline queue support for function runner
 */

import type { OfflineRequest, RequestConfig } from './types';
import type { FunctionRunnerClient } from './client';

export class OfflineQueue {
  private queue: OfflineRequest[] = [];
  private db?: IDBDatabase;
  private readonly dbName = 'fnrunner-offline';
  private readonly storeName = 'requests';
  private processing = false;
  
  /**
   * Initialize offline queue
   */
  async initialize() {
    this.db = await this.openDatabase();
    await this.loadQueue();
  }
  
  /**
   * Open IndexedDB database
   */
  private async openDatabase(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: 'id' });
          store.createIndex('timestamp', 'timestamp');
        }
      };
    });
  }
  
  /**
   * Load queued requests from database
   */
  private async loadQueue() {
    if (!this.db) return;
    
    const tx = this.db.transaction(this.storeName, 'readonly');
    const store = tx.objectStore(this.storeName);
    
    return new Promise<void>((resolve) => {
      const request = store.getAll();
      
      request.onsuccess = () => {
        this.queue = request.result || [];
        resolve();
      };
      
      request.onerror = () => {
        console.error('Failed to load offline queue');
        resolve();
      };
    });
  }
  
  /**
   * Save queue to database
   */
  private async saveQueue() {
    if (!this.db) return;
    
    const tx = this.db.transaction(this.storeName, 'readwrite');
    const store = tx.objectStore(this.storeName);
    
    // Clear existing
    await new Promise<void>((resolve, reject) => {
      const clearRequest = store.clear();
      clearRequest.onsuccess = () => resolve();
      clearRequest.onerror = () => reject(clearRequest.error);
    });
    
    // Add all requests
    for (const request of this.queue) {
      store.add(request);
    }
    
    return new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }
  
  /**
   * Enqueue a request for later processing
   */
  async enqueue<T>(config: RequestConfig): Promise<T> {
    const request: OfflineRequest = {
      id: `${Date.now()}-${Math.random()}`,
      type: this.getRequestType(config),
      data: config,
      timestamp: Date.now(),
      callbackId: `callback-${Date.now()}`
    };
    
    this.queue.push(request);
    await this.saveQueue();
    
    // Return a promise that will be resolved when online
    return new Promise((resolve, reject) => {
      // Store callback for later resolution
      const handler = (event: MessageEvent) => {
        if (
          event.data.type === 'offline-request-complete' &&
          event.data.callbackId === request.callbackId
        ) {
          window.removeEventListener('message', handler);
          
          if (event.data.error) {
            reject(new Error(event.data.error));
          } else {
            resolve(event.data.result);
          }
        }
      };
      
      window.addEventListener('message', handler);
      
      // Also try to process immediately if online
      if (navigator.onLine && !this.processing) {
        this.processNext();
      }
    });
  }
  
  /**
   * Process queued requests
   */
  async process(client: FunctionRunnerClient) {
    if (this.processing) return;
    
    this.processing = true;
    
    try {
      while (this.queue.length > 0 && navigator.onLine) {
        const request = this.queue[0];
        
        try {
          const result = await this.executeRequest(client, request);
          
          // Remove from queue
          this.queue.shift();
          await this.saveQueue();
          
          // Notify original caller if possible
          if (request.callbackId) {
            window.postMessage({
              type: 'offline-request-complete',
              callbackId: request.callbackId,
              result
            }, '*');
          }
        } catch (error) {
          // Check if error is retryable
          if (this.isRetryableError(error)) {
            // Keep in queue and try again later
            console.log('Request failed, will retry later:', error);
            break;
          } else {
            // Remove failed request and notify
            this.queue.shift();
            await this.saveQueue();
            
            if (request.callbackId) {
              window.postMessage({
                type: 'offline-request-complete',
                callbackId: request.callbackId,
                error: (error as Error).message
              }, '*');
            }
          }
        }
      }
    } finally {
      this.processing = false;
    }
  }
  
  /**
   * Process next request in queue
   */
  private async processNext() {
    // This is called internally and doesn't use the client parameter
    // In a real implementation, we'd need access to the client instance
    console.log('Processing offline queue...');
  }
  
  /**
   * Execute a queued request
   */
  private async executeRequest(
    client: FunctionRunnerClient,
    request: OfflineRequest
  ): Promise<any> {
    const config = request.data as RequestConfig;
    return client.request(config);
  }
  
  /**
   * Determine request type from config
   */
  private getRequestType(config: RequestConfig): OfflineRequest['type'] {
    if (config.path.includes('/tasks') && config.method === 'POST') {
      return 'submitTask';
    } else if (config.path.includes('/cancel')) {
      return 'cancelTask';
    } else {
      return 'getStatus';
    }
  }
  
  /**
   * Check if error is retryable
   */
  private isRetryableError(error: any): boolean {
    // Network errors are retryable
    if (error.name === 'NetworkError' || error.code === 'NETWORK_ERROR') {
      return true;
    }
    
    // Server errors might be temporary
    if (error.status >= 500) {
      return true;
    }
    
    return false;
  }
  
  /**
   * Get queue statistics
   */
  getStats() {
    const now = Date.now();
    const oldestRequest = this.queue[0];
    const oldestAge = oldestRequest ? now - oldestRequest.timestamp : 0;
    
    return {
      queued: this.queue.length,
      oldestAge,
      processing: this.processing
    };
  }
  
  /**
   * Clear the queue
   */
  async clear() {
    this.queue = [];
    await this.saveQueue();
    
    // Notify all pending callbacks
    for (const request of this.queue) {
      if (request.callbackId) {
        window.postMessage({
          type: 'offline-request-complete',
          callbackId: request.callbackId,
          error: 'Offline queue cleared'
        }, '*');
      }
    }
  }
}