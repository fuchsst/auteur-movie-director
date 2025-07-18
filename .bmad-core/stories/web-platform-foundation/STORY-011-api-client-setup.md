# Story: API Client Setup

**Story ID**: STORY-011  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Medium)  
**Priority**: High  
**Status**: ❌ Not Completed (January 2025)  

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
- **Projects**: create, list, get, update, delete, validate structure, narrative setup
- **Files**: upload, list, download, delete, bulk operations, asset categorization
- **Workspace**: getConfig, updateSettings, initialize, validate
- **Git**: commit, getStatus, getHistory, push, pull, LFS track/untrack
- **Tasks**: submit, getStatus, getResult, cancel, list active
- **Docker**: health check, service status, container logs
- **Quality**: lint, format, test, validate structure
- **Nodes**: execute, getCapabilities, saveState, loadState
- **Pipeline**: getQualityMappings, getNodeTypes, validatePipeline
- **Takes**: generatePath, registerOutput, listTakes, getTakeMetadata, scene/shot hierarchy
- **Agents**: assignTask, getProgress, getCapabilities, handoff
- **Assets**: categorize, extractMetadata, getCompatibility, compositePrompt
- **Narrative**: getStructure, updateBeat, getEmotionalKeywords
- **Characters**: create, list, get, update, uploadBaseFace, uploadVariation, uploadLoRA, findUsage, updateLoRAStatus

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
  
  async getWithNarrative(id: string): Promise<Project> {
    return api.get<Project>(`/projects/${id}?include=narrative,assets`);
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
  async submit(taskType: string, params: any, context?: TaskContext): Promise<TaskSubmission> {
    const response = await api.post<TaskSubmission>('/tasks/submit', {
      task_type: taskType,
      params,
      context  // Include filmmaking context
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
  async generatePath(
    projectId: string, 
    nodeType: string, 
    nodeId: string,
    context: {
      chapterId: string;
      sceneId: string;
      shotId: string;
    }
  ): Promise<TakePath> {
    return api.post<TakePath>('/takes/generate-path', {
      project_id: projectId,
      node_type: nodeType,
      node_id: nodeId,
      chapter_id: context.chapterId,
      scene_id: context.sceneId,
      shot_id: context.shotId
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
  
  async listTakes(
    projectId: string, 
    filters?: {
      nodeId?: string;
      sceneId?: string;
      shotId?: string;
      chapterId?: string;
    }
  ): Promise<Take[]> {
    return api.get<Take[]>(`/projects/${projectId}/takes`, filters);
  },
  
  async getSceneTakes(projectId: string, sceneId: string): Promise<Take[]> {
    return api.get<Take[]>(`/projects/${projectId}/scenes/${sceneId}/takes`);
  },
  
  async getShotTakes(projectId: string, shotId: string): Promise<Take[]> {
    return api.get<Take[]>(`/projects/${projectId}/shots/${shotId}/takes`);
  },
  
  async setActiveTake(projectId: string, shotId: string, takeId: string): Promise<void> {
    return api.post<void>(`/projects/${projectId}/shots/${shotId}/active-take`, {
      take_id: takeId
    });
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

// src/lib/api/agents.ts
import { api } from './client';
import type { AgentTask, AgentCapabilities, AgentProgress } from '$types';

export const agentsApi = {
  async assignTask(
    agentType: string,
    task: AgentTask
  ): Promise<TaskSubmission> {
    const response = await api.post<TaskSubmission>('/agents/assign', {
      agent_type: agentType,
      task
    });
    
    return {
      ...response,
      poll: (onProgress?: (status: AgentProgress) => void) => 
        api.pollTask(response.task_id, onProgress)
    };
  },
  
  async getCapabilities(agentType: string): Promise<AgentCapabilities> {
    return api.get<AgentCapabilities>(`/agents/${agentType}/capabilities`);
  },
  
  async getProgress(taskId: string): Promise<AgentProgress> {
    return api.get<AgentProgress>(`/agents/tasks/${taskId}/progress`);
  },
  
  async handoff(
    fromAgent: string,
    toAgent: string,
    payload: any
  ): Promise<void> {
    return api.post<void>('/agents/handoff', {
      from_agent: fromAgent,
      to_agent: toAgent,
      payload
    });
  },
  
  async getVRAMUsage(): Promise<VRAMStatus> {
    return api.get<VRAMStatus>('/agents/producer/vram-status');
  }
};

// src/lib/api/assets.ts
import { api } from './client';
import type { AssetMetadata, CompositePrompt, AssetCompatibility } from '$types';

export const assetsApi = {
  async categorize(filePath: string): Promise<AssetMetadata> {
    return api.post<AssetMetadata>('/assets/categorize', {
      file_path: filePath
    });
  },
  
  async extractMetadata(assetId: string): Promise<AssetMetadata> {
    return api.get<AssetMetadata>(`/assets/${assetId}/metadata`);
  },
  
  async getCompatibility(assetId: string): Promise<AssetCompatibility> {
    return api.get<AssetCompatibility>(`/assets/${assetId}/compatibility`);
  },
  
  async buildCompositePrompt(
    basePrompt: string,
    context: {
      characterIds?: string[];
      styleIds?: string[];
      locationId?: string;
      emotionalBeat?: string;
    }
  ): Promise<CompositePrompt> {
    return api.post<CompositePrompt>('/assets/composite-prompt', {
      base_prompt: basePrompt,
      ...context
    });
  },
  
  async getAssetsByAgent(agentType: string): Promise<AssetReference[]> {
    return api.get<AssetReference[]>(`/assets/by-agent/${agentType}`);
  }
};

// src/lib/api/narrative.ts
import { api } from './client';
import type { NarrativeStructure, EmotionalBeat } from '$types';

export const narrativeApi = {
  async getStructure(projectId: string): Promise<NarrativeStructure> {
    return api.get<NarrativeStructure>(`/projects/${projectId}/narrative`);
  },
  
  async updateStructure(
    projectId: string,
    structure: Partial<NarrativeStructure>
  ): Promise<NarrativeStructure> {
    return api.put<NarrativeStructure>(`/projects/${projectId}/narrative`, structure);
  },
  
  async updateBeat(
    projectId: string,
    sceneId: string,
    beat: EmotionalBeat
  ): Promise<void> {
    return api.post<void>(`/projects/${projectId}/scenes/${sceneId}/beat`, beat);
  },
  
  async getEmotionalKeywords(beatName: string): Promise<string[]> {
    return api.get<string[]>(`/narrative/beats/${beatName}/keywords`);
  },
  
  async suggestNextBeat(
    projectId: string,
    currentSceneId: string
  ): Promise<EmotionalBeat> {
    return api.get<EmotionalBeat>(
      `/projects/${projectId}/narrative/suggest-beat`,
      { current_scene: currentSceneId }
    );
  }
};

// src/lib/api/characters.ts
import { api } from './client';
import type { 
  CharacterAsset, 
  CharacterCreate, 
  CharacterUpdate,
  CharacterUsage,
  LoRAStatus,
  CharacterVariation 
} from '$types';

export const charactersApi = {
  async create(
    projectId: string, 
    character: CharacterCreate
  ): Promise<CharacterAsset> {
    return api.post<CharacterAsset>(`/projects/${projectId}/characters`, character);
  },
  
  async list(projectId: string): Promise<CharacterAsset[]> {
    return api.get<CharacterAsset[]>(`/projects/${projectId}/characters`);
  },
  
  async get(projectId: string, characterId: string): Promise<CharacterAsset> {
    return api.get<CharacterAsset>(`/projects/${projectId}/characters/${characterId}`);
  },
  
  async update(
    projectId: string, 
    characterId: string, 
    updates: CharacterUpdate
  ): Promise<CharacterAsset> {
    return api.put<CharacterAsset>(
      `/projects/${projectId}/characters/${characterId}`, 
      updates
    );
  },
  
  async uploadBaseFace(
    projectId: string,
    characterId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<CharacterAsset> {
    const response = await api.upload(
      `/projects/${projectId}/characters/${characterId}/base-face`,
      [file],
      onProgress
    );
    return response.character;
  },
  
  async uploadVariation(
    projectId: string,
    characterId: string,
    variationType: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<CharacterAsset> {
    const response = await api.upload(
      `/projects/${projectId}/characters/${characterId}/variations?type=${variationType}`,
      [file],
      onProgress
    );
    return response.character;
  },
  
  async uploadLoRA(
    projectId: string,
    characterId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<CharacterAsset> {
    const response = await api.upload(
      `/projects/${projectId}/characters/${characterId}/lora`,
      [file],
      onProgress
    );
    return response.character;
  },
  
  async trainLoRA(
    projectId: string,
    characterId: string,
    trainingParams?: {
      epochs?: number;
      learningRate?: number;
      batchSize?: number;
    }
  ): Promise<TaskSubmission> {
    const response = await api.post<TaskSubmission>(
      `/projects/${projectId}/characters/${characterId}/lora/train`,
      trainingParams || {}
    );
    
    return {
      ...response,
      poll: (onProgress?: (status: LoRAStatus) => void) => 
        api.pollTask(response.task_id, onProgress)
    };
  },
  
  async findUsage(
    projectId: string,
    characterId: string
  ): Promise<CharacterUsage> {
    return api.get<CharacterUsage>(
      `/projects/${projectId}/characters/${characterId}/usage`
    );
  },
  
  async updateLoRAStatus(
    projectId: string,
    characterId: string,
    status: LoRAStatus
  ): Promise<CharacterAsset> {
    return api.post<CharacterAsset>(
      `/projects/${projectId}/characters/${characterId}/lora/status`,
      status
    );
  },
  
  async getVariations(
    projectId: string,
    characterId: string
  ): Promise<Record<string, CharacterVariation>> {
    return api.get<Record<string, CharacterVariation>>(
      `/projects/${projectId}/characters/${characterId}/variations`
    );
  },
  
  async deleteVariation(
    projectId: string,
    characterId: string,
    variationType: string
  ): Promise<CharacterAsset> {
    return api.delete<CharacterAsset>(
      `/projects/${projectId}/characters/${characterId}/variations/${variationType}`
    );
  },
  
  async generateVariations(
    projectId: string,
    characterId: string,
    types: string[] = ['happy', 'sad', 'angry', 'surprised', 'neutral']
  ): Promise<TaskSubmission> {
    const response = await api.post<TaskSubmission>(
      `/projects/${projectId}/characters/${characterId}/variations/generate`,
      { variation_types: types }
    );
    
    return {
      ...response,
      poll: (onProgress?: (status: TaskStatus) => void) => 
        api.pollTask(response.task_id, onProgress)
    };
  },
  
  async getTriggerWord(
    projectId: string,
    characterId: string
  ): Promise<{ triggerWord: string }> {
    return api.get<{ triggerWord: string }>(
      `/projects/${projectId}/characters/${characterId}/trigger-word`
    );
  },
  
  async updateTriggerWord(
    projectId: string,
    characterId: string,
    triggerWord: string
  ): Promise<CharacterAsset> {
    return api.post<CharacterAsset>(
      `/projects/${projectId}/characters/${characterId}/trigger-word`,
      { trigger_word: triggerWord }
    );
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
// Using the API client for node execution with filmmaking context
import { nodesApi, pipelineApi, takesApi, assetsApi, narrativeApi } from '$lib/api';
import type { TextToImageParams } from '$types/nodes';

// Get quality mapping for node
const qualityConfig = await pipelineApi.getQualityMapping('standard', 'text_to_image');

// Get narrative context
const narrative = await narrativeApi.getStructure(projectId);
const currentScene = narrative.chapters[0].scenes[0];
const emotionalKeywords = await narrativeApi.getEmotionalKeywords(currentScene.emotionalBeat);

// Build composite prompt with assets
const compositePrompt = await assetsApi.buildCompositePrompt(
  'A beautiful sunset over mountains',
  {
    characterIds: ['char_001'],
    styleIds: ['style_cinematic'],
    locationId: 'loc_mountains',
    emotionalBeat: currentScene.emotionalBeat
  }
);

// Prepare node parameters with composite prompt
const params: TextToImageParams = {
  prompt: compositePrompt.final_prompt,
  negative_prompt: 'blurry, low quality',
  width: qualityConfig.params.width || 1024,
  height: qualityConfig.params.height || 1024,
  steps: qualityConfig.params.steps || 20,
  cfg_scale: 7.5,
  seed: 42,
  model: qualityConfig.params.model || 'sdxl-base-1.0',
  scheduler: qualityConfig.params.scheduler || 'euler',
  batch_size: 1,
  // Include LoRA models from composite prompt
  loras: compositePrompt.lora_models
};

// Validate parameters before execution
const validation = await nodesApi.validateParams('text_to_image', params);
if (!validation.is_valid) {
  throw new Error(`Invalid parameters: ${validation.errors.join(', ')}`);
}

// Generate take path with scene/shot context
const takePath = await takesApi.generatePath(
  projectId, 
  'text_to_image', 
  nodeId,
  {
    chapterId: narrative.chapters[0].id,
    sceneId: currentScene.id,
    shotId: currentScene.shots[0].id
  }
);

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

// Register output as take with full context
if (result.success) {
  await takesApi.registerOutput(projectId, takePath.path, {
    node_type: 'text_to_image',
    node_id: nodeId,
    params,
    output_files: result.outputs,
    execution_time: result.execution_time,
    quality: 'standard',
    // Filmmaking context
    scene_id: currentScene.id,
    shot_id: currentScene.shots[0].id,
    emotional_beat: currentScene.emotionalBeat,
    composite_prompt: compositePrompt,
    agent_notes: {
      art_director: 'Cinematic style applied',
      cinematographer: 'Golden hour lighting'
    }
  });
  
  // Set as active take if it's the first one
  const shotTakes = await takesApi.getShotTakes(projectId, currentScene.shots[0].id);
  if (shotTakes.length === 1) {
    await takesApi.setActiveTake(projectId, currentScene.shots[0].id, result.take_id);
  }
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
  // Filmmaking context
  scene_id: string;
  shot_id: string;
  chapter_id?: string;
  take_number: number;
  emotional_beat?: string;
  composite_prompt?: CompositePrompt;
  agent_notes?: Record<string, string>;
}

// Additional types for filmmaking pipeline
export interface TaskContext {
  scene_id?: string;
  shot_id?: string;
  chapter_id?: string;
  emotional_beat?: string;
  assigned_agent?: string;
  composite_prompt?: CompositePrompt;
}

export interface CompositePrompt {
  base_prompt: string;
  final_prompt: string;
  character_refs: string[];
  style_refs: string[];
  location_ref?: string;
  emotional_keywords: string[];
  lora_models?: Array<{
    model_path: string;
    weight: number;
    trigger_word?: string;
  }>;
  agent_contributions: Record<string, string>;
}

export interface AgentTask {
  task_type: string;
  priority: 'high' | 'medium' | 'low';
  context: {
    project_id: string;
    scene_id?: string;
    shot_id?: string;
  };
  payload: any;
  dependencies?: string[];  // Other agent tasks
}

export interface AgentCapabilities {
  agent_type: string;
  supported_tasks: string[];
  max_concurrent_tasks: number;
  vram_requirements?: number;
  estimated_duration: Record<string, number>;
}

export interface AgentProgress {
  task_id: string;
  agent_type: string;
  status: 'assigned' | 'working' | 'completed' | 'failed';
  progress: number;
  current_step?: string;
  vram_usage?: number;
  outputs?: any;
  handoff_to?: string;
}

export interface VRAMStatus {
  total_vram: number;
  used_vram: number;
  available_vram: number;
  agent_usage: Record<string, number>;
  recommended_quality: 'low' | 'standard' | 'high';
}

export interface AssetReference {
  id: string;
  name: string;
  path: string;
  type: 'character' | 'style' | 'location' | 'music';
  metadata: AssetMetadata;
  trigger_word?: string;
  agent_owner?: string;
}

export interface AssetMetadata {
  originalName: string;
  fileSize: number;
  mimeType: string;
  fileExtension: string;
  uploadedAt: string;
  assetCategory: 'character' | 'style' | 'location' | 'music' | 'creative_document' | 'project_file';
  // Character specific
  characterName?: string;
  triggerWord?: string;
  trainingSteps?: number;
  // Style specific
  styleType?: string;
  // Music specific
  bpm?: number;
  mood?: string;
  // Agent integration
  agentCompatible?: string[];
  supportsCompositePrompts?: boolean;
}

export interface AssetCompatibility {
  compatible_nodes: string[];
  compatible_agents: string[];
  composite_prompt_field?: string;
  requirements?: string[];
}

export interface NarrativeStructure {
  structure_type: 'three-act' | 'hero-journey' | 'beat-sheet' | 'story-circle';
  chapters: Chapter[];
  emotional_arc: EmotionalBeat[];
  current_position: {
    chapter: number;
    scene: string;
    beat?: string;
  };
}

export interface Chapter {
  id: string;
  name: string;
  order: number;
  scenes: Scene[];
}

export interface Scene {
  id: string;
  name: string;
  order: number;
  shots: Shot[];
  emotionalBeat?: string;
}

export interface Shot {
  id: string;
  name: string;
  order: number;
  takes: Take[];
  activeTakeId?: string;
}

export interface EmotionalBeat {
  id: string;
  name: string;
  sceneId: string;
  keywords: string[];
  intensity: number;
}

// Character-specific types
export interface CharacterAsset extends AssetReference {
  assetId: string;  // UUID
  assetType: 'Character';
  description: string;  // Character appearance/personality
  triggerWord?: string;  // LoRA activation token
  baseFaceImagePath?: string;  // Canonical face image
  loraModelPath?: string;  // Trained LoRA file
  loraTrainingStatus: 'untrained' | 'training' | 'completed' | 'failed';
  variations: Record<string, string>;  // variation_type -> image_path
  usage: string[];  // Shot IDs where character is used
}

export interface CharacterCreate {
  name: string;
  description: string;
  triggerWord?: string;
}

export interface CharacterUpdate {
  name?: string;
  description?: string;
  triggerWord?: string;
  loraTrainingStatus?: 'untrained' | 'training' | 'completed' | 'failed';
}

export interface CharacterUsage {
  characterId: string;
  shotIds: string[];
  sceneIds: string[];
  totalUsages: number;
  usageDetails: Array<{
    shotId: string;
    sceneId: string;
    takeIds: string[];
    lastUsed: string;
  }>;
}

export interface LoRAStatus {
  status: 'untrained' | 'training' | 'completed' | 'failed';
  progress?: number;
  currentStep?: string;
  totalSteps?: number;
  trainingParams?: {
    epochs: number;
    learningRate: number;
    batchSize: number;
  };
  startedAt?: string;
  completedAt?: string;
  error?: string;
}

export interface CharacterVariation {
  type: string;  // 'happy', 'sad', 'angry', etc.
  imagePath: string;
  generatedAt: string;
  generationParams?: {
    prompt: string;
    seed: number;
    model: string;
  };
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

// Agent integration example
import { agentsApi, assetsApi } from '$lib/api';

// Check VRAM before assigning task
const vramStatus = await agentsApi.getVRAMUsage();
if (vramStatus.available_vram < 8) {
  console.warn('Low VRAM, using lower quality preset');
}

// Assign task to Art Director
const artDirectorTask = await agentsApi.assignTask('ArtDirector', {
  task_type: 'style_curation',
  priority: 'high',
  context: {
    project_id: projectId,
    scene_id: 'S001'
  },
  payload: {
    mood: 'cinematic',
    time_of_day: 'golden_hour'
  }
});

// Poll for completion
const result = await artDirectorTask.poll((progress) => {
  console.log(`Art Director: ${progress.current_step} (${progress.progress}%)`);
});

// Hand off to Cinematographer
await agentsApi.handoff('ArtDirector', 'Cinematographer', result.outputs);

// Character API usage example
import { charactersApi, assetsApi } from '$lib/api';

// Create a new character
const newCharacter = await charactersApi.create(projectId, {
  name: 'Sarah Connor',
  description: 'Strong female protagonist, athletic build, determined expression',
  triggerWord: 'sarahconnor_lora'
});

// Upload base face image
const baseFaceFile = new File([baseFaceBlob], 'sarah_base_face.png');
await charactersApi.uploadBaseFace(
  projectId, 
  newCharacter.assetId, 
  baseFaceFile,
  (progress) => console.log(`Upload progress: ${progress}%`)
);

// Train LoRA model
const trainingTask = await charactersApi.trainLoRA(projectId, newCharacter.assetId, {
  epochs: 10,
  learningRate: 0.0001,
  batchSize: 4
});

// Poll for training progress
await trainingTask.poll((status) => {
  console.log(`LoRA training: ${status.status} (${status.progress}%)`);
  if (status.currentStep) {
    console.log(`Current step: ${status.currentStep} of ${status.totalSteps}`);
  }
});

// Generate character variations
const variationTask = await charactersApi.generateVariations(
  projectId,
  newCharacter.assetId,
  ['happy', 'sad', 'angry', 'determined', 'surprised']
);

await variationTask.poll((status) => {
  console.log(`Generating variations: ${status.progress}%`);
});

// Use character in composite prompt
const compositePrompt = await assetsApi.buildCompositePrompt(
  'A woman standing in a post-apocalyptic wasteland',
  {
    characterIds: [newCharacter.assetId],
    styleIds: ['style_cinematic_action'],
    locationId: 'loc_wasteland',
    emotionalBeat: 'determination'
  }
);

// Find character usage across project
const usage = await charactersApi.findUsage(projectId, newCharacter.assetId);
console.log(`Character used in ${usage.totalUsages} shots across ${usage.sceneIds.length} scenes`);
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
- [ ] Character API endpoints handle CRUD operations
- [ ] Character asset uploads track progress correctly
- [ ] LoRA training status updates via task polling
- [ ] Character variation generation completes successfully
- [ ] Character usage tracking returns accurate data

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
- [ ] Character API endpoints implemented with full type safety
- [ ] Character asset management (base face, variations, LoRA) functional
- [ ] Documentation includes usage examples
- [ ] Unit tests cover main functionality including retries and polling
- [ ] Integration tests verify container networking
- [ ] TypeScript interfaces match backend API contracts

## Story Links
- **Depends On**: STORY-004-file-management-api
- **Blocks**: STORY-008-project-gallery-view, STORY-010-file-upload-component
- **Related PRD**: PRD-001-web-platform-foundation

## Implementation Status

### ✅ Implemented Features (~20%):
- Basic ApiClient class structure in `frontend/src/lib/api/client.ts`
- Environment-based URL configuration
- TypeScript interfaces for some entities (workspace, takes, git, characters)
- API endpoint files created for:
  - workspace.ts (project operations)
  - takes.ts (takes management)
  - git.ts (git and LFS operations)
  - characters.ts (basic character operations)
  - system.ts (system info)

### ❌ Critical Issues:
- **The API client is fundamentally broken** - missing core HTTP methods (get, post, put, delete)
- All endpoint files call non-existent methods on the ApiClient class
- No actual HTTP request implementation

### ❌ Not Implemented (~80%):
- HTTP methods (get, post, put, delete) in ApiClient
- Error handling and ApiError class
- Request/response interceptors
- Retry logic with exponential backoff
- Request timeout handling
- Request cancellation support
- Task polling mechanism
- Upload progress tracking
- Container-aware configuration
- Most API endpoints from the story:
  - Docker API
  - Quality API  
  - Nodes API
  - Pipeline API
  - Agents API
  - Assets API (beyond basic characters)
  - Narrative API
- Character API is mostly stubbed with "Not implemented" errors
- No store integration
- No usage examples or documentation

### Implementation Notes:
The current implementation appears to be a work-in-progress with the structure in place but missing the core functionality. The API client cannot make any actual HTTP requests in its current state. All the endpoint files that depend on it would throw errors if used.