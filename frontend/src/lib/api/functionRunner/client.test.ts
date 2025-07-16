/**
 * Tests for Function Runner API Client
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { FunctionRunnerClient } from './client';
import type { 
  FunctionRunnerConfig, 
  WebSocketClient,
  FunctionTemplate,
  TaskSubmitResponse,
  TaskStatus,
  TaskResult
} from './types';

// Mock WebSocket client
const createMockWebSocketClient = (): WebSocketClient => ({
  subscribe: vi.fn(() => vi.fn()),
  send: vi.fn(),
  isConnected: vi.fn(() => true)
});

// Mock fetch
global.fetch = vi.fn();

describe('FunctionRunnerClient', () => {
  let client: FunctionRunnerClient;
  let mockWsClient: WebSocketClient;
  let mockFetch: typeof fetch;
  
  beforeEach(() => {
    mockWsClient = createMockWebSocketClient();
    mockFetch = global.fetch as any;
    vi.clearAllMocks();
    
    const config: FunctionRunnerConfig = {
      baseUrl: 'http://localhost:8000',
      wsClient: mockWsClient,
      maxConcurrent: 3,
      cacheConfig: {
        ttl: 1000,
        storage: 'memory'
      }
    };
    
    client = new FunctionRunnerClient(config);
  });
  
  afterEach(() => {
    client.dispose();
  });
  
  describe('listTemplates', () => {
    it('should fetch templates from API', async () => {
      const mockTemplates: FunctionTemplate[] = [
        {
          id: 'template-1',
          name: 'Test Template',
          description: 'A test template',
          version: '1.0.0',
          backend_type: 'comfyui',
          category: 'test',
          tags: ['test'],
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          parameter_schema: {},
          output_schema: {},
          resource_requirements: {
            cpu_cores: 1,
            memory_gb: 1,
            gpu_count: 0,
            gpu_memory_gb: 0,
            disk_gb: 1,
            estimated_duration_seconds: 60
          },
          quality_presets: []
        }
      ];
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockTemplates
      } as Response);
      
      const templates = await client.listTemplates();
      
      expect(templates).toEqual(mockTemplates);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/functions/templates',
        expect.objectContaining({
          method: 'GET'
        })
      );
    });
    
    it('should cache template responses', async () => {
      const mockTemplates: FunctionTemplate[] = [{ id: 'test' } as any];
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockTemplates
      } as Response);
      
      // First call
      await client.listTemplates();
      
      // Second call should use cache
      const cached = await client.listTemplates();
      
      expect(cached).toEqual(mockTemplates);
      expect(mockFetch).toHaveBeenCalledTimes(1); // Only one fetch
    });
    
    it('should handle API errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Server error'
      } as Response);
      
      await expect(client.listTemplates()).rejects.toThrow('Request failed');
    });
  });
  
  describe('submitTask', () => {
    const mockTemplate: FunctionTemplate = {
      id: 'test-template',
      name: 'Test',
      description: 'Test template',
      version: '1.0.0',
      backend_type: 'custom',
      category: 'test',
      tags: [],
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
      parameter_schema: {
        input: { type: 'string', required: true }
      },
      output_schema: {},
      resource_requirements: {
        cpu_cores: 1,
        memory_gb: 1,
        gpu_count: 0,
        gpu_memory_gb: 0,
        disk_gb: 1,
        estimated_duration_seconds: 60
      },
      quality_presets: []
    };
    
    beforeEach(() => {
      // Mock getTemplate
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockTemplate
      } as Response);
    });
    
    it('should submit task and return handle', async () => {
      const mockResponse: TaskSubmitResponse = {
        task_id: 'task-123',
        status: 'queued',
        queue_position: 1
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse
      } as Response);
      
      const handle = await client.submitTask(
        'test-template',
        { input: 'test value' },
        {
          quality: 'high',
          priority: 10
        }
      );
      
      expect(handle.taskId).toBe('task-123');
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/functions/tasks',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            template_id: 'test-template',
            inputs: { input: 'test value' },
            quality: 'high',
            priority: 10
          })
        })
      );
    });
    
    it('should validate inputs against template schema', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ task_id: 'test' })
      } as Response);
      
      // Missing required field
      await expect(
        client.submitTask('test-template', {})
      ).rejects.toThrow('Missing required parameter: input');
    });
    
    it('should handle progress callbacks', async () => {
      const mockProgress = vi.fn();
      const mockComplete = vi.fn();
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ task_id: 'task-123' })
      } as Response);
      
      const handle = await client.submitTask(
        'test-template',
        { input: 'test' },
        {
          onProgress: mockProgress,
          onComplete: mockComplete
        }
      );
      
      // Simulate WebSocket subscription
      expect(mockWsClient.subscribe).toHaveBeenCalledWith(
        'task.task-123',
        expect.any(Function)
      );
    });
  });
  
  describe('getTaskStatus', () => {
    it('should fetch task status', async () => {
      const mockStatus: TaskStatus = {
        task_id: 'task-123',
        status: 'running',
        stage: 'processing',
        progress: 50,
        created_at: '2024-01-01T00:00:00Z'
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockStatus
      } as Response);
      
      const status = await client.getTaskStatus('task-123');
      
      expect(status).toEqual(mockStatus);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/functions/tasks/task-123/status',
        expect.any(Object)
      );
    });
  });
  
  describe('getTaskResult', () => {
    it('should fetch task result and download files', async () => {
      const mockResult: TaskResult = {
        task_id: 'task-123',
        status: 'completed',
        outputs: {
          image: {
            type: 'file',
            url: 'http://localhost:8000/files/output.png',
            filename: 'output.png',
            mime_type: 'image/png'
          }
        },
        execution_time_seconds: 10,
        worker_id: 'worker-1'
      };
      
      const mockBlob = new Blob(['image data'], { type: 'image/png' });
      
      // Mock result fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResult
      } as Response);
      
      // Mock file download
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      } as Response);
      
      const result = await client.getTaskResult('task-123');
      
      expect(result.outputs?.image.blob).toEqual(mockBlob);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });
  
  describe('cancelTask', () => {
    it('should cancel a task', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({})
      } as Response);
      
      await client.cancelTask('task-123');
      
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/functions/tasks/task-123/cancel',
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });
  
  describe('batch operations', () => {
    it('should submit batch tasks', async () => {
      const mockResponse = {
        batch_id: 'batch-123',
        tasks: [
          { task_id: 'task-1', status: 'queued' },
          { task_id: 'task-2', status: 'queued' }
        ]
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockResponse
      } as Response);
      
      const batchHandle = await client.submitBatch([
        {
          template_id: 'template-1',
          inputs: { value: 1 },
          quality: 'standard',
          priority: 5,
          task_name: 'task1'
        },
        {
          template_id: 'template-2',
          inputs: { value: 2 },
          quality: 'high',
          priority: 5,
          task_name: 'task2'
        }
      ]);
      
      expect(batchHandle.batchId).toBe('batch-123');
      expect(batchHandle.taskHandles.size).toBe(2);
    });
  });
  
  describe('request queue', () => {
    it('should limit concurrent requests', async () => {
      const delays = [100, 100, 100, 100, 100];
      let activeRequests = 0;
      let maxActive = 0;
      
      // Mock slow responses
      for (const delay of delays) {
        mockFetch.mockImplementationOnce(async () => {
          activeRequests++;
          maxActive = Math.max(maxActive, activeRequests);
          
          await new Promise(resolve => setTimeout(resolve, delay));
          
          activeRequests--;
          return {
            ok: true,
            headers: new Headers({ 'content-type': 'application/json' }),
            json: async () => ({ task_id: 'test' })
          } as Response;
        });
      }
      
      // Submit multiple requests
      const promises = delays.map((_, i) => 
        client.getTaskStatus(`task-${i}`)
      );
      
      await Promise.all(promises);
      
      // Should not exceed max concurrent (3)
      expect(maxActive).toBeLessThanOrEqual(3);
    });
  });
  
  describe('retry logic', () => {
    it('should retry on network errors', async () => {
      // First two calls fail, third succeeds
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({ task_id: 'test' })
        } as Response);
      
      const result = await client.getTaskStatus('task-123');
      
      expect(result).toEqual({ task_id: 'test' });
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });
    
    it('should retry on server errors', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 503,
          statusText: 'Service Unavailable'
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({ task_id: 'test' })
        } as Response);
      
      const result = await client.getTaskStatus('task-123');
      
      expect(result).toEqual({ task_id: 'test' });
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
    
    it('should not retry on client errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        text: async () => 'Invalid input'
      } as Response);
      
      await expect(client.getTaskStatus('task-123')).rejects.toThrow();
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('offline support', () => {
    let offlineClient: FunctionRunnerClient;
    
    beforeEach(() => {
      const config: FunctionRunnerConfig = {
        baseUrl: 'http://localhost:8000',
        wsClient: mockWsClient,
        offlineEnabled: true
      };
      
      offlineClient = new FunctionRunnerClient(config);
    });
    
    afterEach(() => {
      offlineClient.dispose();
    });
    
    it('should queue requests when offline', async () => {
      // Mock offline
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });
      
      // Request should be queued
      const promise = offlineClient.getTaskStatus('task-123');
      
      // Should not call fetch immediately
      expect(mockFetch).not.toHaveBeenCalled();
      
      // Restore online
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true
      });
    });
  });
});

describe('Type Guards', () => {
  it('should correctly identify task results', () => {
    const { isTaskResult } = require('./types');
    
    expect(isTaskResult({
      task_id: 'test',
      status: 'completed'
    })).toBe(true);
    
    expect(isTaskResult({
      task_id: 'test',
      status: 'invalid'
    })).toBe(false);
    
    expect(isTaskResult(null)).toBe(false);
  });
  
  it('should correctly identify task progress', () => {
    const { isTaskProgress } = require('./types');
    
    expect(isTaskProgress({
      taskId: 'test',
      stage: 'processing',
      progress: 50
    })).toBe(true);
    
    expect(isTaskProgress({
      taskId: 'test',
      progress: 'invalid'
    })).toBe(false);
  });
  
  it('should correctly identify upload progress', () => {
    const { isUploadProgress } = require('./types');
    
    expect(isUploadProgress({
      loaded: 100,
      total: 1000,
      percentage: 10
    })).toBe(true);
    
    expect(isUploadProgress({
      loaded: '100',
      total: 1000,
      percentage: 10
    })).toBe(false);
  });
});