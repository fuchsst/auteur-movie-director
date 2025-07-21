/**
 * Function Runner API Client
 * 
 * Provides type-safe access to function runner capabilities with:
 * - Automatic retries and exponential backoff
 * - Progress tracking via WebSocket
 * - Request queuing and rate limiting
 * - Offline support
 */

import type {
  FunctionRunnerConfig,
  FunctionTemplate,
  TaskSubmission,
  TaskResult,
  TaskStatus,
  TaskHandle,
  BatchHandle,
  ListTemplatesOptions,
  SubmitTaskOptions,
  BatchOptions,
  BatchTaskSubmission,
  TaskSubmitResponse,
  BatchSubmitResponse,
  RequestConfig,
  WebSocketClient
} from './types';

import { FunctionRunnerError } from './types';
import { TaskHandleImpl } from './taskHandle';
import { BatchHandleImpl } from './batchHandle';
import { RequestQueue } from './requestQueue';
import { RetryStrategy } from './retryStrategy';
import { ResponseCache } from './cache';
import { FileUploadClient } from './upload';
import { OfflineQueue } from './offline';

export class FunctionRunnerClient {
  private baseUrl: string;
  private wsClient: WebSocketClient;
  private requestQueue: RequestQueue;
  private retryStrategy: RetryStrategy;
  private cache: ResponseCache;
  private uploadClient: FileUploadClient;
  private offlineQueue?: OfflineQueue;
  
  constructor(config: FunctionRunnerConfig) {
    this.baseUrl = config.baseUrl;
    this.wsClient = config.wsClient;
    this.requestQueue = new RequestQueue(config.maxConcurrent || 5);
    this.retryStrategy = new RetryStrategy(config.retryConfig);
    this.cache = new ResponseCache(config.cacheConfig);
    this.uploadClient = new FileUploadClient(this);
    
    if (config.offlineEnabled) {
      this.offlineQueue = new OfflineQueue();
      this.initializeOfflineSupport();
    }
  }
  
  /**
   * List available function templates
   */
  async listTemplates(options?: ListTemplatesOptions): Promise<FunctionTemplate[]> {
    const cacheKey = this.cache.createKey('templates', options);
    const cached = await this.cache.get<FunctionTemplate[]>(cacheKey);
    if (cached) return cached;
    
    const response = await this.request<FunctionTemplate[]>({
      method: 'GET',
      path: '/api/v1/functions/templates',
      params: options
    });
    
    await this.cache.set(cacheKey, response, 300000); // Cache for 5 minutes
    return response;
  }
  
  /**
   * Get a specific template by ID
   */
  async getTemplate(templateId: string): Promise<FunctionTemplate> {
    const cacheKey = `template:${templateId}`;
    const cached = await this.cache.get<FunctionTemplate>(cacheKey);
    if (cached) return cached;
    
    const response = await this.request<FunctionTemplate>({
      method: 'GET',
      path: `/api/v1/functions/templates/${templateId}`
    });
    
    await this.cache.set(cacheKey, response, 600000); // Cache for 10 minutes
    return response;
  }
  
  /**
   * Submit a task for execution
   */
  async submitTask(
    templateId: string,
    inputs: Record<string, any>,
    options?: SubmitTaskOptions
  ): Promise<TaskHandle> {
    // Validate inputs against template
    const template = await this.getTemplate(templateId);
    const validatedInputs = await this.validateInputs(template, inputs);
    
    // Map quality tier if using three-tier system
    let quality = options?.quality || 'standard';
    if (['low', 'standard', 'high'].includes(quality)) {
      // Import dynamically to avoid circular dependencies
      const { mapQualityTierToFunctionRunner } = await import('$lib/utils/quality-mapping');
      quality = mapQualityTierToFunctionRunner(quality as any);
    }
    
    // Create submission
    const submission: TaskSubmission = {
      template_id: templateId,
      inputs: validatedInputs,
      quality: quality,
      priority: options?.priority || 5,
      metadata: options?.metadata
    };
    
    // Submit task
    const response = await this.request<TaskSubmitResponse>({
      method: 'POST',
      path: '/api/v1/functions/tasks',
      body: submission,
      timeout: 30000
    });
    
    // Create task handle for tracking
    return new TaskHandleImpl(
      response.task_id,
      this,
      this.wsClient,
      options?.onProgress,
      options?.onComplete,
      options?.onError
    );
  }
  
  /**
   * Submit multiple tasks as a batch
   */
  async submitBatch(
    tasks: BatchTaskSubmission[],
    options?: BatchOptions
  ): Promise<BatchHandle> {
    const response = await this.request<BatchSubmitResponse>({
      method: 'POST',
      path: '/api/v1/functions/batches',
      body: {
        tasks,
        parallel: options?.parallel ?? true,
        stop_on_error: options?.stopOnError ?? false
      }
    });
    
    // Create task handles for each task
    const taskHandles = new Map<string, TaskHandle>();
    for (const taskResponse of response.tasks) {
      const task = tasks.find(t => 
        t.template_id === taskResponse.task_id.split(':')[0]
      );
      if (task) {
        const handle = new TaskHandleImpl(
          taskResponse.task_id,
          this,
          this.wsClient
        );
        taskHandles.set(task.task_name || taskResponse.task_id, handle);
      }
    }
    
    return new BatchHandleImpl(
      response.batch_id,
      taskHandles,
      this,
      options?.onBatchProgress,
      options?.onBatchComplete,
      options?.onBatchError
    );
  }
  
  /**
   * Get task status and progress
   */
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    return this.request<TaskStatus>({
      method: 'GET',
      path: `/api/v1/functions/tasks/${taskId}/status`
    });
  }
  
  /**
   * Get task result
   */
  async getTaskResult(taskId: string): Promise<TaskResult> {
    const result = await this.request<TaskResult>({
      method: 'GET',
      path: `/api/v1/functions/tasks/${taskId}/result`
    });
    
    // Download output files if needed
    if (result.outputs) {
      for (const [key, output] of Object.entries(result.outputs)) {
        if (output.type === 'file' && output.url) {
          try {
            output.blob = await this.downloadFile(output.url);
          } catch (error) {
            console.error(`Failed to download output file ${key}:`, error);
          }
        }
      }
    }
    
    return result;
  }
  
  /**
   * Cancel a running task
   */
  async cancelTask(taskId: string): Promise<void> {
    await this.request({
      method: 'POST',
      path: `/api/v1/functions/tasks/${taskId}/cancel`
    });
  }
  
  /**
   * Get file upload client
   */
  get upload(): FileUploadClient {
    return this.uploadClient;
  }
  
  /**
   * Internal request method with retries and queuing
   */
  async request<T>(config: RequestConfig): Promise<T> {
    // Check if offline
    if (this.offlineQueue && !navigator.onLine) {
      return this.offlineQueue.enqueue(config) as Promise<T>;
    }
    
    return this.requestQueue.add(async () => {
      const controller = new AbortController();
      const timeout = config.timeout || 60000;
      
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      try {
        // Build URL with params
        const url = new URL(`${this.baseUrl}${config.path}`);
        if (config.params) {
          Object.entries(config.params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
              url.searchParams.append(key, String(value));
            }
          });
        }
        
        // Execute request with retry
        const response = await this.retryStrategy.execute(
          () => fetch(url.toString(), {
            method: config.method,
            headers: {
              'Content-Type': 'application/json',
              ...config.headers
            },
            body: config.body ? JSON.stringify(config.body) : undefined,
            signal: controller.signal
          }),
          config.retries
        );
        
        if (!response.ok) {
          const errorBody = await response.text();
          throw new FunctionRunnerError(
            `Request failed: ${response.statusText}`,
            response.status,
            errorBody
          );
        }
        
        // Parse response
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return response.json();
        } else {
          return response.text() as any;
        }
      } finally {
        clearTimeout(timeoutId);
      }
    });
  }
  
  /**
   * Download a file
   */
  private async downloadFile(url: string): Promise<Blob> {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`);
    }
    return response.blob();
  }
  
  /**
   * Validate inputs against template schema
   */
  private async validateInputs(
    template: FunctionTemplate,
    inputs: Record<string, any>
  ): Promise<Record<string, any>> {
    // Basic validation - in production would use a schema validator
    const validated: Record<string, any> = {};
    const schema = template.parameter_schema;
    
    for (const [key, value] of Object.entries(inputs)) {
      if (schema[key]) {
        // TODO: Add proper schema validation
        validated[key] = value;
      }
    }
    
    // Check required fields
    for (const [key, paramSchema] of Object.entries(schema)) {
      if (paramSchema.required && !(key in validated)) {
        throw new Error(`Missing required parameter: ${key}`);
      }
    }
    
    return validated;
  }
  
  /**
   * Initialize offline support
   */
  private async initializeOfflineSupport() {
    if (!this.offlineQueue) return;
    
    await this.offlineQueue.initialize();
    
    // Process queue when coming online
    window.addEventListener('online', async () => {
      console.log('Connection restored, processing offline queue...');
      await this.offlineQueue!.process(this);
    });
    
    // Check if already online
    if (navigator.onLine) {
      await this.offlineQueue.process(this);
    }
  }
  
  /**
   * Clean up resources
   */
  dispose() {
    this.requestQueue.clear();
    this.cache.clear();
  }
}