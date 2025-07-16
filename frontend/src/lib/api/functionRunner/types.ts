/**
 * Function Runner API types
 */

// Core types
export interface FunctionTemplate {
  id: string;
  name: string;
  description: string;
  version: string;
  backend_type: 'comfyui' | 'gradio' | 'custom';
  category: string;
  tags: string[];
  author?: string;
  created_at: string;
  updated_at: string;
  parameter_schema: Record<string, any>;
  output_schema: Record<string, any>;
  resource_requirements: ResourceRequirements;
  quality_presets: QualityPreset[];
  examples?: Example[];
}

export interface ResourceRequirements {
  cpu_cores: number;
  memory_gb: number;
  gpu_count: number;
  gpu_memory_gb: number;
  gpu_compute_capability?: string;
  disk_gb: number;
  estimated_duration_seconds: number;
}

export interface QualityPreset {
  name: QualityLevel;
  description: string;
  resource_multiplier: number;
  time_multiplier: number;
  parameters?: Record<string, any>;
}

export type QualityLevel = 'draft' | 'standard' | 'high' | 'ultra';

export interface Example {
  name: string;
  description?: string;
  inputs: Record<string, any>;
  preview_url?: string;
}

// Task submission types
export interface TaskSubmission {
  template_id: string;
  inputs: Record<string, any>;
  quality: QualityLevel;
  priority: number;
  metadata?: Record<string, any>;
}

export interface BatchTaskSubmission extends TaskSubmission {
  task_name?: string;
  dependencies?: string[];
}

export interface SubmitTaskOptions {
  quality?: QualityLevel;
  priority?: number;
  metadata?: Record<string, any>;
  onProgress?: (progress: TaskProgress) => void;
  onComplete?: (result: TaskResult) => void;
  onError?: (error: Error) => void;
}

export interface BatchOptions {
  parallel?: boolean;
  stopOnError?: boolean;
  onBatchProgress?: (progress: BatchProgress) => void;
  onBatchComplete?: (results: BatchResult) => void;
  onBatchError?: (error: Error) => void;
}

// Task status and results
export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  stage?: string;
  progress?: number;
  message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  worker_id?: string;
  queue_position?: number;
  eta?: string;
}

export interface TaskProgress {
  taskId: string;
  stage: string;
  progress: number;
  message?: string;
  eta?: Date;
  metadata?: Record<string, any>;
}

export interface TaskResult {
  task_id: string;
  status: 'completed' | 'failed' | 'cancelled';
  outputs?: Record<string, TaskOutput>;
  error?: string;
  execution_time_seconds: number;
  worker_id: string;
  metadata?: Record<string, any>;
}

export interface TaskOutput {
  type: 'file' | 'data' | 'url';
  value?: any;
  url?: string;
  filename?: string;
  mime_type?: string;
  size_bytes?: number;
  blob?: Blob;
}

// Batch types
export interface BatchHandle {
  batchId: string;
  taskHandles: Map<string, TaskHandle>;
  getProgress(): BatchProgress;
  getResults(): Promise<BatchResult>;
  cancel(): Promise<void>;
  dispose(): void;
}

export interface BatchProgress {
  batchId: string;
  total: number;
  completed: number;
  failed: number;
  progress: number;
  tasks: Record<string, TaskStatus>;
}

export interface BatchResult {
  batchId: string;
  success: boolean;
  results: Record<string, TaskResult>;
  errors: Record<string, Error>;
}

// API response types
export interface TaskSubmitResponse {
  task_id: string;
  status: string;
  queue_position?: number;
  estimated_start?: string;
  estimated_completion?: string;
}

export interface BatchSubmitResponse {
  batch_id: string;
  tasks: TaskSubmitResponse[];
}

export interface ListTemplatesOptions {
  category?: string;
  tags?: string[];
  backend_type?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

// Upload types
export interface UploadOptions {
  metadata?: Record<string, any>;
  onProgress?: (progress: UploadProgress) => void;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface UploadResult {
  file_id: string;
  filename: string;
  size_bytes: number;
  mime_type: string;
  url: string;
  metadata?: Record<string, any>;
}

// Client configuration
export interface FunctionRunnerConfig {
  baseUrl: string;
  wsClient: WebSocketClient;
  maxConcurrent?: number;
  cacheConfig?: CacheConfig;
  retryConfig?: RetryConfig;
  offlineEnabled?: boolean;
}

export interface CacheConfig {
  ttl?: number;
  maxSize?: number;
  storage?: 'memory' | 'localStorage' | 'indexedDB';
}

export interface RetryConfig {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  retryableStatuses?: number[];
}

// Request types
export interface RequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  params?: Record<string, any>;
  body?: any;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

// Error types
export class FunctionRunnerError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly body?: string,
    public readonly code?: string
  ) {
    super(message);
    this.name = 'FunctionRunnerError';
  }
}

// WebSocket client interface (minimal, actual implementation in services)
export interface WebSocketClient {
  subscribe(channel: string, handler: (message: any) => void): () => void;
  send(message: any): void;
  isConnected(): boolean;
}

// Task handle interface
export interface TaskHandle {
  readonly taskId: string;
  wait(timeoutMs?: number): Promise<TaskResult>;
  cancel(): Promise<void>;
  getStatus(): Promise<TaskStatus>;
  dispose(): void;
}

// Offline support types
export interface OfflineRequest {
  id: string;
  type: 'submitTask' | 'cancelTask' | 'getStatus';
  data: any;
  timestamp: number;
  callbackId?: string;
}

// Type guards
export function isTaskResult(value: any): value is TaskResult {
  return value && 
    typeof value.task_id === 'string' &&
    ['completed', 'failed', 'cancelled'].includes(value.status);
}

export function isTaskProgress(value: any): value is TaskProgress {
  return value &&
    typeof value.taskId === 'string' &&
    typeof value.stage === 'string' &&
    typeof value.progress === 'number';
}

export function isUploadProgress(value: any): value is UploadProgress {
  return value &&
    typeof value.loaded === 'number' &&
    typeof value.total === 'number' &&
    typeof value.percentage === 'number';
}