/**
 * Task handle implementation for progress tracking
 */

import type {
  TaskHandle,
  TaskResult,
  TaskStatus,
  TaskProgress,
  WebSocketClient
} from './types';
import type { FunctionRunnerClient } from './client';

export class TaskHandleImpl implements TaskHandle {
  private disposed = false;
  private unsubscribe?: () => void;
  private completePromise?: Promise<TaskResult>;
  private completeResolve?: (result: TaskResult) => void;
  private completeReject?: (error: Error) => void;
  
  constructor(
    public readonly taskId: string,
    private client: FunctionRunnerClient,
    private wsClient: WebSocketClient,
    private onProgress?: (progress: TaskProgress) => void,
    private onComplete?: (result: TaskResult) => void,
    private onError?: (error: Error) => void
  ) {
    this.subscribeToUpdates();
    this.setupCompletionPromise();
  }
  
  private setupCompletionPromise() {
    this.completePromise = new Promise<TaskResult>((resolve, reject) => {
      this.completeResolve = resolve;
      this.completeReject = reject;
    });
  }
  
  private subscribeToUpdates() {
    // Subscribe to WebSocket updates for this task
    this.unsubscribe = this.wsClient.subscribe(
      `task.${this.taskId}`,
      (message) => {
        if (this.disposed) return;
        
        switch (message.type) {
          case 'task.progress':
            this.handleProgress(message.data);
            break;
          case 'task.completed':
            this.handleComplete(message.data);
            break;
          case 'task.failed':
            this.handleError(new Error(message.data.error || 'Task failed'));
            break;
          case 'task.cancelled':
            this.handleError(new Error('Task cancelled'));
            break;
        }
      }
    );
  }
  
  private handleProgress(data: any) {
    const progress: TaskProgress = {
      taskId: this.taskId,
      stage: data.stage || 'processing',
      progress: data.progress || 0,
      message: data.message,
      eta: data.eta ? new Date(data.eta) : undefined,
      metadata: data.metadata
    };
    
    this.onProgress?.(progress);
  }
  
  private async handleComplete(data: any) {
    try {
      // Fetch full result
      const result = await this.client.getTaskResult(this.taskId);
      
      this.onComplete?.(result);
      this.completeResolve?.(result);
    } catch (error) {
      this.handleError(error as Error);
    } finally {
      this.dispose();
    }
  }
  
  private handleError(error: Error) {
    this.onError?.(error);
    this.completeReject?.(error);
    this.dispose();
  }
  
  /**
   * Wait for task completion
   */
  async wait(timeoutMs?: number): Promise<TaskResult> {
    if (!this.completePromise) {
      throw new Error('Task handle already disposed');
    }
    
    if (!timeoutMs) {
      return this.completePromise;
    }
    
    // Race with timeout
    return Promise.race([
      this.completePromise,
      new Promise<TaskResult>((_, reject) => {
        setTimeout(() => reject(new Error('Task timeout')), timeoutMs);
      })
    ]);
  }
  
  /**
   * Cancel the task
   */
  async cancel(): Promise<void> {
    if (this.disposed) {
      throw new Error('Task handle already disposed');
    }
    
    try {
      await this.client.cancelTask(this.taskId);
    } finally {
      this.dispose();
    }
  }
  
  /**
   * Get current status
   */
  async getStatus(): Promise<TaskStatus> {
    if (this.disposed) {
      throw new Error('Task handle already disposed');
    }
    
    return this.client.getTaskStatus(this.taskId);
  }
  
  /**
   * Clean up resources
   */
  dispose() {
    if (!this.disposed) {
      this.disposed = true;
      this.unsubscribe?.();
      this.onProgress = undefined;
      this.onComplete = undefined;
      this.onError = undefined;
      
      // Reject promise if not resolved
      if (this.completeReject) {
        this.completeReject(new Error('Task handle disposed'));
      }
    }
  }
}