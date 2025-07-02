# Story: API Client Setup

**Story ID**: STORY-011  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 2 (Small)  
**Priority**: High  

## Story Description
As a frontend developer, I need a well-structured TypeScript API client that handles all HTTP requests to the backend with proper error handling, type safety, and interceptors for common functionality like authentication and request tracking.

## Acceptance Criteria

### Functional Requirements
- [ ] Create typed API client for all endpoints
- [ ] Handle authentication headers automatically
- [ ] Implement request/response interceptors
- [ ] Add automatic retry logic for failed requests
- [ ] Transform error responses to consistent format
- [ ] Support request cancellation

### Technical Requirements
- [ ] Use native Fetch API or lightweight wrapper
- [ ] Full TypeScript type coverage
- [ ] Configurable base URL from environment
- [ ] Request timeout handling
- [ ] CSRF token management if needed
- [ ] Progress tracking for file uploads

### API Methods
- Projects: create, list, get, update, delete
- Files: upload, list, download, delete
- Workspace: getConfig, updateSettings
- Git: commit, getStatus, getHistory

## Implementation Notes

### Base API Client
```typescript
// src/lib/api/client.ts
interface ApiConfig {
  baseUrl: string;
  timeout?: number;
  headers?: Record<string, string>;
}

interface ApiError {
  code: string;
  message: string;
  details?: any;
  requestId?: string;
  timestamp?: string;
}

class ApiClient {
  private config: ApiConfig;
  private abortControllers = new Map<string, AbortController>();
  
  constructor(config: ApiConfig) {
    this.config = {
      timeout: 30000,
      ...config
    };
  }
  
  private async request<T>(
    method: string,
    path: string,
    options: RequestInit = {}
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
      
      throw error;
    }
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
export const api = new ApiClient({
  baseUrl: import.meta.env.PUBLIC_API_URL || 'http://localhost:8000/api/v1'
});
```

### Typed API Services
```typescript
// src/lib/api/projects.ts
import { api } from './client';
import type { Project, ProjectCreate, ProjectUpdate } from '$types';

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
  }
};

// src/lib/api/workspace.ts
export const workspaceApi = {
  async getConfig(): Promise<WorkspaceConfig> {
    return api.get<WorkspaceConfig>('/workspace/config');
  },
  
  async updateConfig(config: Partial<WorkspaceConfig>): Promise<WorkspaceConfig> {
    return api.put<WorkspaceConfig>('/workspace/config', config);
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
  
  async getStatus(projectId: string): Promise<GitStatus> {
    return api.get<GitStatus>(`/projects/${projectId}/git/status`);
  },
  
  async getHistory(projectId: string, limit = 10): Promise<CommitHistory> {
    return api.get<CommitHistory>(`/projects/${projectId}/git/history`, { limit });
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

### Usage Example
```typescript
// Using the API client in a component
import { projectsApi } from '$lib/api/projects';
import { handleApiError } from '$lib/utils/errors';

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

## Definition of Done
- [ ] API client implemented with all methods
- [ ] Full TypeScript coverage with no any types
- [ ] Error handling standardized across all calls
- [ ] Request/response interceptors working
- [ ] Documentation includes usage examples
- [ ] Unit tests cover main functionality

## Story Links
- **Depends On**: STORY-004-file-management-api
- **Blocks**: STORY-008-project-gallery-view, STORY-010-file-upload-component
- **Related PRD**: PRD-001-web-platform-foundation