# Story: API Client Setup

**Story ID**: STORY-011  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Medium)  
**Priority**: High  

## Story Description
As a frontend developer, I need a well-structured TypeScript API client that handles all HTTP requests to the backend with proper error handling, type safety, container-aware configuration, and interceptors for common functionality like authentication and request tracking.

## Acceptance Criteria

### Functional Requirements
- [ ] Create typed API client for all endpoints
- [ ] Handle authentication headers automatically
- [ ] Implement request/response interceptors
- [ ] Add automatic retry logic for failed requests
- [ ] Transform error responses to consistent format
- [ ] Support request cancellation
- [ ] Support Celery task tracking with polling
- [ ] Handle container-aware API URL resolution

### Technical Requirements
- [ ] Use native Fetch API or lightweight wrapper
- [ ] Full TypeScript type coverage
- [ ] Container-aware base URL configuration
- [ ] Request timeout handling
- [ ] CSRF token management if needed
- [ ] Progress tracking for file uploads
- [ ] WebSocket fallback for long-running operations
- [ ] Support for Git LFS operations

### API Methods
- **Projects**: create, list, get, update, delete, validate structure
- **Files**: upload, list, download, delete, bulk operations
- **Workspace**: getConfig, updateSettings, initialize, validate
- **Git**: commit, getStatus, getHistory, push, pull, LFS track/untrack
- **Tasks**: submit, getStatus, getResult, cancel, list active
- **Docker**: health check, service status, container logs
- **Quality**: lint, format, test, validate structure
- **Nodes**: execute, getCapabilities, saveState, loadState
- **Pipeline**: getQualityMappings, getNodeTypes, validatePipeline
- **Takes**: generatePath, registerOutput, listTakes, getTakeMetadata

## Implementation Notes

### Container-Aware Configuration
```typescript
// src/lib/api/config.ts
function getApiUrl(): string {
  // Check if running in container environment
  if (typeof window !== 'undefined') {
    // Browser environment - use relative URL or env var
    return import.meta.env.PUBLIC_API_URL || '/api/v1';
  }
  
  // SSR environment - use container service name or localhost
  const isDocker = process.env.DOCKER_ENV === 'true';
  const backendHost = isDocker ? 'backend' : 'localhost';
  const backendPort = process.env.BACKEND_PORT || '8000';
  
  return `http://${backendHost}:${backendPort}/api/v1`;
}

export const apiConfig = {
  baseUrl: getApiUrl(),
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000
};
```

### Base API Client
```typescript
// src/lib/api/client.ts
import { apiConfig } from './config';

interface ApiConfig {
  baseUrl: string;
  timeout?: number;
  headers?: Record<string, string>;
  retryAttempts?: number;
  retryDelay?: number;
}

interface ApiError {
  code: string;
  message: string;
  details?: any;
  requestId?: string;
  timestamp?: string;
}

interface TaskStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  result?: any;
  error?: string;
}

class ApiClient {
  private config: ApiConfig;
  private abortControllers = new Map<string, AbortController>();
  
  constructor(config: ApiConfig) {
    this.config = {
      timeout: 30000,
      retryAttempts: 3,
      retryDelay: 1000,
      ...config
    };
  }
  
  private async request<T>(
    method: string,
    path: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    const url = `${this.config.baseUrl}${path}`;
    const requestId = crypto.randomUUID();
    
    // Create abort controller
    const controller = new AbortController();
    this.abortControllers.set(requestId, controller);
    
    // Set up timeout
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, this.config.timeout);
    
    try {
      const response = await fetch(url, {
        method,
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId,
          ...this.config.headers,
          ...options.headers
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      this.abortControllers.delete(requestId);
      
      // Handle response
      if (!response.ok) {
        const error = await this.parseError(response);
        
        // Retry on certain errors
        if (retryCount < this.config.retryAttempts && this.shouldRetry(response.status)) {
          await this.delay(this.config.retryDelay * Math.pow(2, retryCount));
          return this.request<T>(method, path, options, retryCount + 1);
        }
        
        throw error;
      }
      
      // Parse JSON response
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return await response.json();
      }
      
      return response as any;
      
    } catch (error) {
      clearTimeout(timeoutId);
      this.abortControllers.delete(requestId);
      
      if (error.name === 'AbortError') {
        throw new ApiError('REQUEST_TIMEOUT', 'Request timed out');
      }
      
      // Retry on network errors
      if (retryCount < this.config.retryAttempts && error.name === 'TypeError') {
        await this.delay(this.config.retryDelay * Math.pow(2, retryCount));
        return this.request<T>(method, path, options, retryCount + 1);
      }
      
      throw error;
    }
  }
  
  private shouldRetry(status: number): boolean {
    return status === 502 || status === 503 || status === 504;
  }
  
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  private async parseError(response: Response): Promise<ApiError> {
    try {
      const data = await response.json();
      if (data.error) {
        return new ApiError(
          data.error.code || 'UNKNOWN_ERROR',
          data.error.message || response.statusText,
          data.error.details,
          data.request_id,
          data.timestamp
        );
      }
    } catch {
      // Failed to parse error response
    }
    
    // Default error
    return new ApiError(
      `HTTP_${response.status}`,
      response.statusText || 'Request failed'
    );
  }
  
  async get<T>(path: string, params?: Record<string, any>): Promise<T> {
    const url = params ? `${path}?${new URLSearchParams(params)}` : path;
    return this.request<T>('GET', url);
  }
  
  async post<T>(path: string, data?: any): Promise<T> {
    return this.request<T>('POST', path, {
      body: data ? JSON.stringify(data) : undefined
    });
  }
  
  async put<T>(path: string, data?: any): Promise<T> {
    return this.request<T>('PUT', path, {
      body: data ? JSON.stringify(data) : undefined
    });
  }
  
  async delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }
  
  async upload(
    path: string,
    files: File[],
    onProgress?: (progress: number) => void
  ): Promise<any> {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    // Use XMLHttpRequest for progress tracking
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            onProgress((e.loaded / e.total) * 100);
          }
        });
      }
      
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(xhr.statusText));
        }
      });
      
      xhr.addEventListener('error', () => reject(new Error('Upload failed')));
      
      xhr.open('POST', `${this.config.baseUrl}${path}`);
      Object.entries(this.config.headers || {}).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value);
      });
      
      xhr.send(formData);
    });
  }
  
  // Celery task tracking
  async pollTask<T>(
    taskId: string,
    onProgress?: (status: TaskStatus) => void,
    pollInterval = 1000
  ): Promise<T> {
    while (true) {
      const status = await this.get<TaskStatus>(`/tasks/${taskId}`);
      
      if (onProgress) {
        onProgress(status);
      }
      
      if (status.status === 'completed') {
        return status.result as T;
      }
      
      if (status.status === 'failed') {
        throw new ApiError('TASK_FAILED', status.error || 'Task execution failed');
      }
      
      await this.delay(pollInterval);
    }
  }
  
  cancelRequest(requestId: string) {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
    }
  }
}

class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: any,
    public requestId?: string,
    public timestamp?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Create singleton instance
export const api = new ApiClient(apiConfig);
```

### Typed API Services
```typescript
// src/lib/api/projects.ts
import { api } from './client';
import type { Project, ProjectCreate, ProjectUpdate, ProjectStructure } from '$types';

export const projectsApi = {
  async list(): Promise<Project[]> {
    return api.get<Project[]>('/projects');
  },
  
  async get(id: string): Promise<Project> {
    return api.get<Project>(`/projects/${id}`);
  },
  
  async create(data: ProjectCreate): Promise<Project> {
    return api.post<Project>('/projects', data);
  },
  
  async update(id: string, data: ProjectUpdate): Promise<Project> {
    return api.put<Project>(`/projects/${id}`, data);
  },
  
  async delete(id: string): Promise<void> {
    return api.delete<void>(`/projects/${id}`);
  },
  
  async validateStructure(id: string): Promise<ProjectStructure> {
    return api.get<ProjectStructure>(`/projects/${id}/validate`);
  },
  
  async getFiles(id: string, assetType?: string): Promise<FileInfo[]> {
    const params = assetType ? { asset_type: assetType } : undefined;
    return api.get<FileInfo[]>(`/projects/${id}/assets`, params);
  },
  
  async uploadFiles(
    id: string,
    assetType: string,
    files: File[],
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    return api.upload(
      `/projects/${id}/assets?asset_type=${assetType}`,
      files,
      onProgress
    );
  },
  
  async deleteFiles(id: string, filePaths: string[]): Promise<void> {
    return api.post<void>(`/projects/${id}/assets/delete`, { paths: filePaths });
  }
};

// src/lib/api/workspace.ts
export const workspaceApi = {
  async initialize(): Promise<WorkspaceConfig> {
    return api.post<WorkspaceConfig>('/workspace/initialize');
  },
  
  async getConfig(): Promise<WorkspaceConfig> {
    return api.get<WorkspaceConfig>('/workspace/config');
  },
  
  async updateConfig(config: Partial<WorkspaceConfig>): Promise<WorkspaceConfig> {
    return api.put<WorkspaceConfig>('/workspace/config', config);
  },
  
  async validate(): Promise<WorkspaceValidation> {
    return api.get<WorkspaceValidation>('/workspace/validate');
  }
};

// src/lib/api/git.ts
export const gitApi = {
  async commit(projectId: string, message: string, files?: string[]): Promise<CommitResponse> {
    return api.post<CommitResponse>(`/projects/${projectId}/git/commit`, {
      message,
      files
    });
  },
  
  async push(projectId: string, remote = 'origin', branch = 'main'): Promise<PushResponse> {
    return api.post<PushResponse>(`/projects/${projectId}/git/push`, {
      remote,
      branch
    });
  },
  
  async pull(projectId: string, remote = 'origin', branch = 'main'): Promise<PullResponse> {
    return api.post<PullResponse>(`/projects/${projectId}/git/pull`, {
      remote,
      branch
    });
  },
  
  async getStatus(projectId: string): Promise<GitStatus> {
    return api.get<GitStatus>(`/projects/${projectId}/git/status`);
  },
  
  async getHistory(projectId: string, limit = 10): Promise<CommitHistory> {
    return api.get<CommitHistory>(`/projects/${projectId}/git/history`, { limit });
  },
  
  // Git LFS operations
  async lfsTrack(projectId: string, pattern: string): Promise<LFSResponse> {
    return api.post<LFSResponse>(`/projects/${projectId}/git/lfs/track`, { pattern });
  },
  
  async lfsUntrack(projectId: string, pattern: string): Promise<LFSResponse> {
    return api.post<LFSResponse>(`/projects/${projectId}/git/lfs/untrack`, { pattern });
  },
  
  async lfsStatus(projectId: string): Promise<LFSStatus> {
    return api.get<LFSStatus>(`/projects/${projectId}/git/lfs/status`);
  }
};

// src/lib/api/tasks.ts
export const tasksApi = {
  async submit(taskType: string, params: any): Promise<TaskSubmission> {
    const response = await api.post<TaskSubmission>('/tasks/submit', {
      task_type: taskType,
      params
    });
    
    // Return enhanced response with polling helper
    return {
      ...response,
      poll: (onProgress?: (status: TaskStatus) => void) => 
        api.pollTask(response.task_id, onProgress)
    };
  },
  
  async getStatus(taskId: string): Promise<TaskStatus> {
    return api.get<TaskStatus>(`/tasks/${taskId}`);
  },
  
  async getResult(taskId: string): Promise<any> {
    return api.get<any>(`/tasks/${taskId}/result`);
  },
  
  async cancel(taskId: string): Promise<void> {
    return api.post<void>(`/tasks/${taskId}/cancel`);
  },
  
  async listActive(): Promise<TaskStatus[]> {
    return api.get<TaskStatus[]>('/tasks/active');
  }
};

// src/lib/api/docker.ts
export const dockerApi = {
  async healthCheck(): Promise<HealthStatus> {
    return api.get<HealthStatus>('/docker/health');
  },
  
  async getServiceStatus(): Promise<ServiceStatus[]> {
    return api.get<ServiceStatus[]>('/docker/services');
  },
  
  async getContainerLogs(service: string, lines = 100): Promise<ContainerLogs> {
    return api.get<ContainerLogs>(`/docker/services/${service}/logs`, { lines });
  },
  
  async restartService(service: string): Promise<ServiceStatus> {
    return api.post<ServiceStatus>(`/docker/services/${service}/restart`);
  }
};

// src/lib/api/nodes.ts
import { api } from './client';
import type { NodeDefinition, NodeState, NodeExecution, NodeCapabilities } from '$types';

export const nodesApi = {
  async execute(nodeType: string, params: any, metadata?: any): Promise<NodeExecution> {
    const response = await api.post<TaskSubmission>('/nodes/execute', {
      node_type: nodeType,
      params,
      metadata
    });
    
    return {
      execution_id: response.task_id,
      status: response.status,
      poll: (onProgress?: (status: TaskStatus) => void) => 
        response.poll(onProgress)
    };
  },
  
  async getCapabilities(nodeType: string): Promise<NodeCapabilities> {
    return api.get<NodeCapabilities>(`/nodes/${nodeType}/capabilities`);
  },
  
  async saveState(nodeId: string, state: NodeState): Promise<void> {
    return api.post<void>('/nodes/state', {
      node_id: nodeId,
      state
    });
  },
  
  async loadState(nodeId: string): Promise<NodeState> {
    return api.get<NodeState>(`/nodes/state/${nodeId}`);
  },
  
  async listNodeTypes(): Promise<NodeDefinition[]> {
    return api.get<NodeDefinition[]>('/nodes/types');
  },
  
  async validateParams(nodeType: string, params: any): Promise<ValidationResult> {
    return api.post<ValidationResult>(`/nodes/${nodeType}/validate`, params);
  }
};

// src/lib/api/pipeline.ts
import { api } from './client';
import type { QualityMapping, PipelineConfig, NodeTypeInfo } from '$types';

export const pipelineApi = {
  async getQualityMappings(): Promise<QualityMapping[]> {
    return api.get<QualityMapping[]>('/pipeline/quality-mappings');
  },
  
  async getQualityMapping(quality: string, nodeType: string): Promise<PipelineConfig> {
    return api.get<PipelineConfig>(`/pipeline/quality-mappings/${quality}/${nodeType}`);
  },
  
  async getNodeTypes(): Promise<NodeTypeInfo[]> {
    return api.get<NodeTypeInfo[]>('/pipeline/node-types');
  },
  
  async validatePipeline(config: PipelineConfig): Promise<ValidationResult> {
    return api.post<ValidationResult>('/pipeline/validate', config);
  },
  
  async estimateResources(nodeType: string, params: any): Promise<ResourceEstimate> {
    return api.post<ResourceEstimate>('/pipeline/estimate', {
      node_type: nodeType,
      params
    });
  }
};

// src/lib/api/takes.ts
import { api } from './client';
import type { Take, TakeMetadata, TakePath } from '$types';

export const takesApi = {
  async generatePath(projectId: string, nodeType: string, nodeId: string): Promise<TakePath> {
    return api.post<TakePath>('/takes/generate-path', {
      project_id: projectId,
      node_type: nodeType,
      node_id: nodeId
    });
  },
  
  async registerOutput(
    projectId: string,
    takePath: string,
    metadata: TakeMetadata
  ): Promise<Take> {
    return api.post<Take>('/takes/register', {
      project_id: projectId,
      take_path: takePath,
      metadata
    });
  },
  
  async listTakes(projectId: string, nodeId?: string): Promise<Take[]> {
    const params = nodeId ? { node_id: nodeId } : undefined;
    return api.get<Take[]>(`/projects/${projectId}/takes`, params);
  },
  
  async getTakeMetadata(projectId: string, takePath: string): Promise<TakeMetadata> {
    return api.get<TakeMetadata>(`/projects/${projectId}/takes/metadata`, {
      take_path: takePath
    });
  },
  
  async deleteTake(projectId: string, takePath: string): Promise<void> {
    return api.delete<void>(`/projects/${projectId}/takes`, {
      take_path: takePath
    });
  }
};

// src/lib/api/quality.ts
export const qualityApi = {
  async lint(projectId: string, paths?: string[]): Promise<QualityResult> {
    const taskSubmission = await api.post<TaskSubmission>(`/projects/${projectId}/quality/lint`, {
      paths
    });
    return taskSubmission.poll();
  },
  
  async format(projectId: string, paths?: string[]): Promise<QualityResult> {
    const taskSubmission = await api.post<TaskSubmission>(`/projects/${projectId}/quality/format`, {
      paths
    });
    return taskSubmission.poll();
  },
  
  async test(projectId: string, testPath?: string): Promise<TestResult> {
    const taskSubmission = await api.post<TaskSubmission>(`/projects/${projectId}/quality/test`, {
      test_path: testPath
    });
    return taskSubmission.poll();
  },
  
  async validateStructure(projectId: string): Promise<StructureValidation> {
    return api.get<StructureValidation>(`/projects/${projectId}/quality/validate`);
  }
};
```

### Store Integration
```typescript
// src/lib/stores/api.ts
import { writable } from 'svelte/store';
import { api } from '$lib/api/client';

interface ApiState {
  loading: boolean;
  error: string | null;
}

export const apiState = writable<ApiState>({
  loading: false,
  error: null
});

// Add request interceptor
api.interceptors.request.use((config) => {
  apiState.update(s => ({ ...s, loading: true, error: null }));
  return config;
});

// Add response interceptor
api.interceptors.response.use(
  (response) => {
    apiState.update(s => ({ ...s, loading: false }));
    return response;
  },
  (error) => {
    apiState.update(s => ({ 
      ...s, 
      loading: false, 
      error: error.message 
    }));
    throw error;
  }
);
```

### Node Execution Example
```typescript
// Using the API client for node execution
import { nodesApi, pipelineApi, takesApi } from '$lib/api';
import type { TextToImageParams } from '$types/nodes';

// Get quality mapping for node
const qualityConfig = await pipelineApi.getQualityMapping('standard', 'text_to_image');

// Prepare node parameters
const params: TextToImageParams = {
  prompt: 'A beautiful sunset over mountains',
  negative_prompt: 'blurry, low quality',
  width: qualityConfig.params.width || 1024,
  height: qualityConfig.params.height || 1024,
  steps: qualityConfig.params.steps || 20,
  cfg_scale: 7.5,
  seed: 42,
  model: qualityConfig.params.model || 'sdxl-base-1.0',
  scheduler: qualityConfig.params.scheduler || 'euler',
  batch_size: 1
};

// Validate parameters before execution
const validation = await nodesApi.validateParams('text_to_image', params);
if (!validation.is_valid) {
  throw new Error(`Invalid parameters: ${validation.errors.join(', ')}`);
}

// Generate take path for output
const takePath = await takesApi.generatePath(projectId, 'text_to_image', nodeId);

// Execute node with progress tracking
const execution = await nodesApi.execute('text_to_image', params, {
  project_id: projectId,
  node_id: nodeId,
  take_path: takePath.path
});

// Poll for results
const result = await execution.poll((status) => {
  console.log(`Node execution: ${status.status} (${status.progress}%)`);
  if (status.status === 'running' && status.details) {
    console.log(`Current step: ${status.details.current_step}`);
  }
});

// Register output as take
if (result.success) {
  await takesApi.registerOutput(projectId, takePath.path, {
    node_type: 'text_to_image',
    node_id: nodeId,
    params,
    output_files: result.outputs,
    execution_time: result.execution_time,
    quality: 'standard'
  });
}

// Save node state
await nodesApi.saveState(nodeId, {
  params,
  last_execution: execution.execution_id,
  outputs: result.outputs
});
```

### Type Definitions
```typescript
// src/lib/types/api.ts
export interface WorkspaceConfig {
  workspace_root: string;
  default_quality: string;
  git_lfs_enabled: boolean;
  container_mode: boolean;
}

export interface WorkspaceValidation {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface ProjectStructure {
  is_valid: boolean;
  missing_directories: string[];
  invalid_files: string[];
}

export interface TaskSubmission {
  task_id: string;
  status: 'pending' | 'running';
  poll: <T>(onProgress?: (status: TaskStatus) => void) => Promise<T>;
}

export interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error';
  health: 'healthy' | 'unhealthy' | 'unknown';
  ports: number[];
  logs_preview?: string;
}

export interface HealthStatus {
  overall: 'healthy' | 'degraded' | 'unhealthy';
  services: ServiceStatus[];
  timestamp: string;
}

export interface ContainerLogs {
  service: string;
  logs: string[];
  timestamp: string;
}

export interface LFSStatus {
  tracked_patterns: string[];
  tracked_files: Array<{
    path: string;
    size: number;
    oid: string;
  }>;
}

export interface QualityResult {
  success: boolean;
  changes_made: boolean;
  files_affected: string[];
  output: string;
}

export interface TestResult {
  success: boolean;
  tests_run: number;
  tests_passed: number;
  tests_failed: number;
  coverage?: number;
  output: string;
}

export interface StructureValidation {
  is_valid: boolean;
  structure: Record<string, any>;
  issues: Array<{
    path: string;
    issue: string;
    severity: 'error' | 'warning';
  }>;
}

// Node execution types
export interface NodeDefinition {
  type: string;
  category: string;
  display_name: string;
  description: string;
  inputs: Record<string, ParameterDefinition>;
  outputs: Record<string, OutputDefinition>;
  capabilities: NodeCapabilities;
}

export interface ParameterDefinition {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  required: boolean;
  default?: any;
  description: string;
  constraints?: any;
}

export interface OutputDefinition {
  type: string;
  description: string;
  multiple?: boolean;
}

export interface NodeCapabilities {
  supports_batch: boolean;
  supports_streaming: boolean;
  estimated_vram: number;
  estimated_time: number;
  quality_levels: string[];
}

export interface NodeState {
  params: any;
  last_execution?: string;
  outputs?: any[];
  metadata?: Record<string, any>;
}

export interface NodeExecution {
  execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  poll: <T>(onProgress?: (status: TaskStatus) => void) => Promise<T>;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  result?: any;
  error?: string;
  details?: {
    current_step?: string;
    total_steps?: number;
    message?: string;
  };
}

// Pipeline types
export interface QualityMapping {
  quality: string;
  node_type: string;
  params: Record<string, any>;
  resource_limits: {
    max_vram: number;
    max_time: number;
  };
}

export interface PipelineConfig {
  quality: string;
  node_type: string;
  params: Record<string, any>;
  model_configs: Record<string, any>;
  optimization_hints: string[];
}

export interface NodeTypeInfo {
  type: string;
  category: string;
  backend: string;
  supports_qualities: string[];
  resource_requirements: {
    min_vram: number;
    recommended_vram: number;
  };
}

export interface ResourceEstimate {
  estimated_vram: number;
  estimated_time: number;
  warnings: string[];
  optimization_suggestions: string[];
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

// Takes system types
export interface TakePath {
  path: string;
  full_path: string;
  relative_path: string;
  take_number: number;
}

export interface Take {
  id: string;
  project_id: string;
  node_id: string;
  take_path: string;
  metadata: TakeMetadata;
  created_at: string;
  file_size: number;
}

export interface TakeMetadata {
  node_type: string;
  node_id: string;
  params: any;
  output_files: string[];
  execution_time: number;
  quality: string;
  resolution?: {
    width: number;
    height: number;
  };
  tags?: string[];
}
```

### Usage Example
```typescript
// Using the API client in a component
import { projectsApi, tasksApi } from '$lib/api';
import { handleApiError } from '$lib/utils/errors';

// Simple API call
try {
  const projects = await projectsApi.list();
  // Handle success
} catch (error) {
  if (error instanceof ApiError) {
    // Handle specific API errors
    if (error.code === 'PROJECT_NOT_FOUND') {
      // Show specific message
    }
  }
  handleApiError(error);
}

// Long-running task with progress
try {
  const task = await tasksApi.submit('video_render', {
    project_id: '123',
    scenes: ['scene1', 'scene2']
  });
  
  const result = await task.poll((status) => {
    console.log(`Progress: ${status.progress}%`);
  });
  
  console.log('Render complete:', result);
} catch (error) {
  handleApiError(error);
}

// Container-aware health check
import { dockerApi } from '$lib/api';

const health = await dockerApi.healthCheck();
if (health.overall !== 'healthy') {
  // Show service status warning
}
```

## Dependencies
- Backend API endpoints defined
- TypeScript types for all entities
- Environment configuration

## Testing Criteria
- [ ] All API methods have proper types
- [ ] Error handling works for all scenarios
- [ ] Request timeouts trigger correctly
- [ ] File upload progress tracking works
- [ ] Request cancellation functions properly
- [ ] Interceptors process all requests
- [ ] Container-aware URL resolution works in both environments
- [ ] Retry logic triggers on appropriate errors
- [ ] Task polling mechanism works correctly
- [ ] Git LFS operations handle large files properly
- [ ] Docker health checks return accurate status
- [ ] Quality checks integrate with task system
- [ ] Node execution endpoints handle async tasks properly
- [ ] Quality mapping retrieval works for all node types
- [ ] Node state persistence functions correctly
- [ ] Takes system generates unique paths
- [ ] Parameter validation catches invalid inputs
- [ ] Progress tracking provides meaningful updates

## Definition of Done
- [ ] API client implemented with all methods
- [ ] Full TypeScript coverage with no any types
- [ ] Error handling standardized across all calls
- [ ] Request/response interceptors working
- [ ] Container-aware configuration implemented
- [ ] Celery task polling with progress tracking
- [ ] All new endpoints (workspace, git, tasks, docker, quality) implemented
- [ ] Node execution endpoints with async task pattern
- [ ] Pipeline configuration and quality mapping endpoints
- [ ] Takes system endpoints for output management
- [ ] Retry logic with exponential backoff
- [ ] Documentation includes usage examples
- [ ] Unit tests cover main functionality including retries and polling
- [ ] Integration tests verify container networking
- [ ] TypeScript interfaces match backend API contracts

## Story Links
- **Depends On**: STORY-004-file-management-api
- **Blocks**: STORY-008-project-gallery-view, STORY-010-file-upload-component
- **Related PRD**: PRD-001-web-platform-foundation