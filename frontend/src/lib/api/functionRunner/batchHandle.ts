/**
 * Batch handle implementation for managing multiple tasks
 */

import type {
  BatchHandle,
  BatchProgress,
  BatchResult,
  TaskHandle,
  TaskStatus,
  TaskResult
} from './types';
import type { FunctionRunnerClient } from './client';

export class BatchHandleImpl implements BatchHandle {
  private disposed = false;
  private completePromise?: Promise<BatchResult>;
  private completeResolve?: (result: BatchResult) => void;
  private completeReject?: (error: Error) => void;
  private taskStatuses: Map<string, TaskStatus> = new Map();
  private taskResults: Map<string, TaskResult> = new Map();
  private taskErrors: Map<string, Error> = new Map();
  
  constructor(
    public readonly batchId: string,
    public readonly taskHandles: Map<string, TaskHandle>,
    private client: FunctionRunnerClient,
    private onBatchProgress?: (progress: BatchProgress) => void,
    private onBatchComplete?: (result: BatchResult) => void,
    private onBatchError?: (error: Error) => void
  ) {
    this.setupCompletionPromise();
    this.monitorTasks();
  }
  
  private setupCompletionPromise() {
    this.completePromise = new Promise<BatchResult>((resolve, reject) => {
      this.completeResolve = resolve;
      this.completeReject = reject;
    });
  }
  
  private async monitorTasks() {
    const taskPromises: Promise<void>[] = [];
    
    for (const [taskName, handle] of this.taskHandles) {
      const promise = this.monitorTask(taskName, handle);
      taskPromises.push(promise);
    }
    
    try {
      await Promise.all(taskPromises);
      this.handleBatchComplete();
    } catch (error) {
      this.handleBatchError(error as Error);
    }
  }
  
  private async monitorTask(taskName: string, handle: TaskHandle): Promise<void> {
    try {
      // Get initial status
      const status = await handle.getStatus();
      this.taskStatuses.set(taskName, status);
      this.reportProgress();
      
      // Wait for completion
      const result = await handle.wait();
      this.taskResults.set(taskName, result);
      this.taskStatuses.set(taskName, {
        ...status,
        status: 'completed',
        completed_at: new Date().toISOString()
      });
      
      this.reportProgress();
    } catch (error) {
      this.taskErrors.set(taskName, error as Error);
      this.taskStatuses.set(taskName, {
        task_id: handle.taskId,
        status: 'failed',
        error: (error as Error).message,
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString()
      });
      
      this.reportProgress();
      throw error; // Re-throw to be caught by Promise.all
    }
  }
  
  private reportProgress() {
    const progress = this.getProgress();
    this.onBatchProgress?.(progress);
  }
  
  private handleBatchComplete() {
    const result = this.createBatchResult();
    this.onBatchComplete?.(result);
    this.completeResolve?.(result);
    this.dispose();
  }
  
  private handleBatchError(error: Error) {
    this.onBatchError?.(error);
    this.completeReject?.(error);
    this.dispose();
  }
  
  private createBatchResult(): BatchResult {
    const results: Record<string, TaskResult> = {};
    const errors: Record<string, Error> = {};
    
    for (const [taskName, result] of this.taskResults) {
      results[taskName] = result;
    }
    
    for (const [taskName, error] of this.taskErrors) {
      errors[taskName] = error;
    }
    
    return {
      batchId: this.batchId,
      success: this.taskErrors.size === 0,
      results,
      errors
    };
  }
  
  /**
   * Get current batch progress
   */
  getProgress(): BatchProgress {
    const total = this.taskHandles.size;
    const completed = this.taskResults.size;
    const failed = this.taskErrors.size;
    const progress = total > 0 ? ((completed + failed) / total) * 100 : 0;
    
    const tasks: Record<string, TaskStatus> = {};
    for (const [taskName, status] of this.taskStatuses) {
      tasks[taskName] = status;
    }
    
    return {
      batchId: this.batchId,
      total,
      completed,
      failed,
      progress,
      tasks
    };
  }
  
  /**
   * Get batch results
   */
  async getResults(): Promise<BatchResult> {
    if (!this.completePromise) {
      throw new Error('Batch handle already disposed');
    }
    
    return this.completePromise;
  }
  
  /**
   * Cancel all tasks in the batch
   */
  async cancel(): Promise<void> {
    if (this.disposed) {
      throw new Error('Batch handle already disposed');
    }
    
    const cancelPromises: Promise<void>[] = [];
    
    for (const handle of this.taskHandles.values()) {
      cancelPromises.push(handle.cancel().catch(() => {
        // Ignore individual cancel errors
      }));
    }
    
    await Promise.all(cancelPromises);
    this.dispose();
  }
  
  /**
   * Clean up resources
   */
  dispose() {
    if (!this.disposed) {
      this.disposed = true;
      
      // Dispose all task handles
      for (const handle of this.taskHandles.values()) {
        handle.dispose();
      }
      
      this.taskHandles.clear();
      this.taskStatuses.clear();
      this.taskResults.clear();
      this.taskErrors.clear();
      
      this.onBatchProgress = undefined;
      this.onBatchComplete = undefined;
      this.onBatchError = undefined;
    }
  }
}