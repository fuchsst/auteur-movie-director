# Story: Function Runner API Client

**Story ID**: STORY-047  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Feature  
**Points**: 8 (Large)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description
As a frontend developer, I want a comprehensive TypeScript API client that provides type-safe access to all function runner capabilities with automatic retries, progress tracking, and error handling, so that I can easily integrate AI generation features into the UI without dealing with low-level communication details.

## Acceptance Criteria

### Functional Requirements
- [ ] Type-safe TypeScript client for all function runner endpoints
- [ ] Automatic schema generation from backend OpenAPI spec
- [ ] Real-time progress updates via WebSocket integration
- [ ] Automatic retry with exponential backoff for failures
- [ ] Request queuing and rate limiting
- [ ] Batch operation support for multiple tasks
- [ ] Cancellation support for long-running tasks
- [ ] Offline queue with sync when connection restored

### Technical Requirements
- [ ] Generate TypeScript types from OpenAPI schema
- [ ] Implement `FunctionRunnerClient` with all operations
- [ ] WebSocket integration for progress events
- [ ] Request interceptors for auth and error handling
- [ ] Response caching with configurable TTL
- [ ] Progress callbacks with detailed status
- [ ] Upload progress for large files
- [ ] Connection state management

### Quality Requirements
- [ ] Type coverage 100% for all API operations
- [ ] Bundle size < 50KB (gzipped)
- [ ] Retry logic handles all transient failures
- [ ] Progress updates every 100ms minimum
- [ ] Support for 100+ concurrent requests
- [ ] Memory efficient for large file uploads
- [ ] Works in all modern browsers

## Implementation Notes

### API Client Architecture
```typescript
// lib/api/functionRunner.ts
import { z } from 'zod';
import type { WebSocketClient } from '../services/websocket';

// Generated types from OpenAPI
import type {
  FunctionTemplate,
  TaskSubmission,
  TaskResult,
  TaskStatus,
  ResourceRequirements,
  QualityLevel
} from './generated/types';

export class FunctionRunnerClient {
  private baseUrl: string;
  private wsClient: WebSocketClient;
  private requestQueue: RequestQueue;
  private cache: ResponseCache;
  
  constructor(config: FunctionRunnerConfig) {
    this.baseUrl = config.baseUrl;
    this.wsClient = config.wsClient;
    this.requestQueue = new RequestQueue(config.maxConcurrent);
    this.cache = new ResponseCache(config.cacheConfig);
  }
  
  /**
   * List available function templates
   */
  async listTemplates(options?: ListTemplatesOptions): Promise<FunctionTemplate[]> {
    const cached = await this.cache.get('templates', options);
    if (cached) return cached;
    
    const response = await this.request<FunctionTemplate[]>({
      method: 'GET',
      path: '/api/v1/functions/templates',
      params: options
    });
    
    await this.cache.set('templates', response, options);
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
    
    // Create submission
    const submission: TaskSubmission = {
      template_id: templateId,
      inputs: validatedInputs,
      quality: options?.quality || 'standard',
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
    return new TaskHandle(
      response.task_id,
      this,
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
    
    return new BatchHandle(response.batch_id, this);
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
          output.blob = await this.downloadFile(output.url);
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
   * Internal request method with retries and queuing
   */
  private async request<T>(config: RequestConfig): Promise<T> {
    return this.requestQueue.add(async () => {
      const controller = new AbortController();
      const timeout = config.timeout || 60000;
      
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      try {
        const response = await this.fetchWithRetry(
          `${this.baseUrl}${config.path}`,
          {
            method: config.method,
            headers: {
              'Content-Type': 'application/json',
              ...config.headers
            },
            body: config.body ? JSON.stringify(config.body) : undefined,
            signal: controller.signal
          },
          config.retries
        );
        
        if (!response.ok) {
          throw new FunctionRunnerError(
            `Request failed: ${response.statusText}`,
            response.status,
            await response.text()
          );
        }
        
        return response.json();
      } finally {
        clearTimeout(timeoutId);
      }
    });
  }
}
```

### Task Handle for Progress Tracking
```typescript
export class TaskHandle {
  private disposed = false;
  private unsubscribe?: () => void;
  
  constructor(
    public readonly taskId: string,
    private client: FunctionRunnerClient,
    private onProgress?: (progress: TaskProgress) => void,
    private onComplete?: (result: TaskResult) => void,
    private onError?: (error: Error) => void
  ) {
    this.subscribeToUpdates();
  }
  
  private subscribeToUpdates() {
    // Subscribe to WebSocket updates for this task
    this.unsubscribe = this.client.wsClient.subscribe(
      `task.${this.taskId}`,
      (message) => {
        switch (message.type) {
          case 'task.progress':
            this.handleProgress(message.data);
            break;
          case 'task.completed':
            this.handleComplete(message.data);
            break;
          case 'task.failed':
            this.handleError(new Error(message.data.error));
            break;
        }
      }
    );
  }
  
  private handleProgress(data: any) {
    const progress: TaskProgress = {
      taskId: this.taskId,
      stage: data.stage,
      progress: data.progress,
      message: data.message,
      eta: data.eta ? new Date(data.eta) : undefined,
      metadata: data.metadata
    };
    
    this.onProgress?.(progress);
  }
  
  private async handleComplete(data: any) {
    try {
      const result = await this.client.getTaskResult(this.taskId);
      this.onComplete?.(result);
    } catch (error) {
      this.handleError(error as Error);
    } finally {
      this.dispose();
    }
  }
  
  private handleError(error: Error) {
    this.onError?.(error);
    this.dispose();
  }
  
  /**
   * Wait for task completion
   */
  async wait(timeoutMs?: number): Promise<TaskResult> {
    return new Promise((resolve, reject) => {
      const cleanup = () => {
        this.onComplete = undefined;
        this.onError = undefined;
        clearTimeout(timeoutId);
      };
      
      this.onComplete = (result) => {
        cleanup();
        resolve(result);
      };
      
      this.onError = (error) => {
        cleanup();
        reject(error);
      };
      
      const timeoutId = timeoutMs ? setTimeout(() => {
        cleanup();
        reject(new Error('Task timeout'));
      }, timeoutMs) : undefined;
    });
  }
  
  /**
   * Cancel the task
   */
  async cancel(): Promise<void> {
    await this.client.cancelTask(this.taskId);
    this.dispose();
  }
  
  /**
   * Get current status
   */
  async getStatus(): Promise<TaskStatus> {
    return this.client.getTaskStatus(this.taskId);
  }
  
  dispose() {
    if (!this.disposed) {
      this.disposed = true;
      this.unsubscribe?.();
    }
  }
}
```

### Request Queue and Retry Logic
```typescript
class RequestQueue {
  private queue: QueuedRequest[] = [];
  private active = 0;
  
  constructor(private maxConcurrent: number = 5) {}
  
  async add<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve, reject });
      this.process();
    });
  }
  
  private async process() {
    if (this.active >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }
    
    this.active++;
    const request = this.queue.shift()!;
    
    try {
      const result = await request.fn();
      request.resolve(result);
    } catch (error) {
      request.reject(error);
    } finally {
      this.active--;
      this.process();
    }
  }
}

class RetryStrategy {
  constructor(
    private maxRetries: number = 3,
    private baseDelay: number = 1000,
    private maxDelay: number = 30000
  ) {}
  
  async execute<T>(
    fn: () => Promise<T>,
    isRetryable: (error: any) => boolean
  ): Promise<T> {
    let lastError: any;
    
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        
        if (attempt === this.maxRetries || !isRetryable(error)) {
          throw error;
        }
        
        const delay = Math.min(
          this.baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
          this.maxDelay
        );
        
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError;
  }
}
```

### File Upload Support
```typescript
export class FileUploadClient {
  constructor(private client: FunctionRunnerClient) {}
  
  async uploadFile(
    file: File | Blob,
    options?: UploadOptions
  ): Promise<UploadResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options?.metadata) {
      formData.append('metadata', JSON.stringify(options.metadata));
    }
    
    const xhr = new XMLHttpRequest();
    
    return new Promise((resolve, reject) => {
      // Progress tracking
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100;
          options?.onProgress?.({
            loaded: event.loaded,
            total: event.total,
            percentage: progress
          });
        }
      });
      
      // Success handler
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      });
      
      // Error handlers
      xhr.addEventListener('error', () => reject(new Error('Upload failed')));
      xhr.addEventListener('abort', () => reject(new Error('Upload aborted')));
      
      // Send request
      xhr.open('POST', `${this.client.baseUrl}/api/v1/functions/upload`);
      xhr.send(formData);
    });
  }
}
```

### Offline Queue Support
```typescript
export class OfflineQueue {
  private queue: OfflineRequest[] = [];
  private db: IDBDatabase;
  
  async initialize() {
    this.db = await this.openDatabase();
    await this.loadQueue();
  }
  
  async add(request: OfflineRequest) {
    this.queue.push(request);
    await this.saveQueue();
  }
  
  async process(client: FunctionRunnerClient) {
    const pending = [...this.queue];
    this.queue = [];
    
    for (const request of pending) {
      try {
        const result = await this.executeRequest(client, request);
        
        // Notify original caller if possible
        if (request.callbackId) {
          window.postMessage({
            type: 'offline-request-complete',
            callbackId: request.callbackId,
            result
          }, '*');
        }
      } catch (error) {
        // Re-queue failed requests
        this.queue.push(request);
      }
    }
    
    await this.saveQueue();
  }
  
  private async executeRequest(
    client: FunctionRunnerClient,
    request: OfflineRequest
  ): Promise<any> {
    switch (request.type) {
      case 'submitTask':
        return client.submitTask(
          request.data.templateId,
          request.data.inputs,
          request.data.options
        );
      
      case 'cancelTask':
        return client.cancelTask(request.data.taskId);
      
      default:
        throw new Error(`Unknown request type: ${request.type}`);
    }
  }
}
```

### Type Generation
```typescript
// scripts/generate-types.ts
import { generateApi } from 'swagger-typescript-api';
import * as path from 'path';

async function generateTypes() {
  await generateApi({
    url: 'http://localhost:8000/openapi.json',
    output: path.resolve(__dirname, '../src/lib/api/generated'),
    name: 'types.ts',
    httpClientType: 'fetch',
    generateClient: false,
    generateRouteTypes: true,
    generateResponses: true,
    extractRequestParams: true,
    extractRequestBody: true,
    prettier: {
      printWidth: 100,
      singleQuote: true,
      trailingComma: 'es5'
    }
  });
}

generateTypes().catch(console.error);
```

## Dependencies
- **STORY-041**: Worker Pool Management - for task execution
- **STORY-044**: Function Template Registry - for template info
- **STORY-048**: Progress Tracking System - for real-time updates
- **STORY-009**: WebSocket Client - for progress events
- TypeScript for type safety
- Zod for runtime validation
- swagger-typescript-api for type generation

## Testing Criteria
- [ ] Unit tests for all client methods
- [ ] Integration tests with mock server
- [ ] Type safety tests with TypeScript
- [ ] Retry logic tests with network failures
- [ ] Progress tracking tests
- [ ] File upload tests with large files
- [ ] Offline queue tests
- [ ] Browser compatibility tests

## Definition of Done
- [ ] TypeScript client with all operations
- [ ] Automatic type generation from OpenAPI
- [ ] WebSocket integration for progress
- [ ] Retry logic with exponential backoff
- [ ] Request queuing and rate limiting
- [ ] File upload with progress tracking
- [ ] Offline queue implementation
- [ ] Comprehensive test suite
- [ ] Documentation with examples
- [ ] Published to npm registry

## Story Links
- **Depends On**: STORY-041, STORY-044, STORY-048
- **Blocks**: STORY-051 (Integration & Testing)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/client/api_design.md