/**
 * File upload client with progress tracking
 */

import type {
  UploadOptions,
  UploadResult,
  UploadProgress
} from './types';
import type { FunctionRunnerClient } from './client';

export class FileUploadClient {
  constructor(private client: FunctionRunnerClient) {}
  
  /**
   * Upload a file
   */
  async uploadFile(
    file: File | Blob,
    options?: UploadOptions
  ): Promise<UploadResult> {
    const formData = new FormData();
    
    // Add file
    if (file instanceof File) {
      formData.append('file', file, file.name);
    } else {
      formData.append('file', file, 'blob');
    }
    
    // Add metadata
    if (options?.metadata) {
      formData.append('metadata', JSON.stringify(options.metadata));
    }
    
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      // Progress tracking
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && options?.onProgress) {
          const progress: UploadProgress = {
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded / event.total) * 100)
          };
          options.onProgress(progress);
        }
      });
      
      // Success handler
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText);
            resolve(result);
          } catch (error) {
            reject(new Error('Invalid response format'));
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
        }
      });
      
      // Error handlers
      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed: Network error'));
      });
      
      xhr.addEventListener('abort', () => {
        reject(new Error('Upload aborted'));
      });
      
      xhr.addEventListener('timeout', () => {
        reject(new Error('Upload timeout'));
      });
      
      // Configure request
      xhr.open('POST', `${(this.client as any).baseUrl}/api/v1/functions/upload`);
      
      // Set timeout (5 minutes for large files)
      xhr.timeout = 300000;
      
      // Send request
      xhr.send(formData);
      
      // Return abort function via promise property
      (resolve as any).abort = () => xhr.abort();
    });
  }
  
  /**
   * Upload multiple files
   */
  async uploadFiles(
    files: Array<File | Blob>,
    options?: UploadOptions & { parallel?: boolean }
  ): Promise<UploadResult[]> {
    const parallel = options?.parallel ?? true;
    
    if (parallel) {
      // Upload in parallel
      const promises = files.map(file => this.uploadFile(file, options));
      return Promise.all(promises);
    } else {
      // Upload sequentially
      const results: UploadResult[] = [];
      let totalLoaded = 0;
      const totalSize = files.reduce((sum, file) => sum + file.size, 0);
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileStart = totalLoaded;
        
        const result = await this.uploadFile(file, {
          ...options,
          onProgress: (progress) => {
            // Calculate overall progress
            const overallLoaded = fileStart + progress.loaded;
            const overallProgress: UploadProgress = {
              loaded: overallLoaded,
              total: totalSize,
              percentage: Math.round((overallLoaded / totalSize) * 100)
            };
            options?.onProgress?.(overallProgress);
          }
        });
        
        results.push(result);
        totalLoaded += file.size;
      }
      
      return results;
    }
  }
  
  /**
   * Create a resumable upload session
   */
  async createResumableUpload(
    file: File,
    chunkSize: number = 5 * 1024 * 1024 // 5MB chunks
  ): Promise<ResumableUpload> {
    const totalChunks = Math.ceil(file.size / chunkSize);
    
    // Initialize upload session
    const response = await (this.client as any).request({
      method: 'POST',
      path: '/api/v1/functions/upload/resumable',
      body: {
        filename: file.name,
        size: file.size,
        mime_type: file.type,
        chunks: totalChunks
      }
    });
    
    return new ResumableUpload(
      response.session_id,
      file,
      chunkSize,
      totalChunks,
      this
    );
  }
}

/**
 * Resumable upload handler
 */
export class ResumableUpload {
  private uploadedChunks: Set<number> = new Set();
  private abortController?: AbortController;
  
  constructor(
    private sessionId: string,
    private file: File,
    private chunkSize: number,
    private totalChunks: number,
    private uploadClient: FileUploadClient
  ) {}
  
  /**
   * Start or resume upload
   */
  async start(options?: UploadOptions): Promise<UploadResult> {
    this.abortController = new AbortController();
    
    // Get already uploaded chunks
    await this.checkStatus();
    
    // Upload remaining chunks
    for (let i = 0; i < this.totalChunks; i++) {
      if (this.uploadedChunks.has(i)) {
        continue; // Skip already uploaded chunks
      }
      
      if (this.abortController.signal.aborted) {
        throw new Error('Upload aborted');
      }
      
      await this.uploadChunk(i, options);
    }
    
    // Finalize upload
    return this.finalize();
  }
  
  /**
   * Abort the upload
   */
  abort() {
    this.abortController?.abort();
  }
  
  /**
   * Check upload status
   */
  private async checkStatus() {
    const response = await (this.uploadClient as any).client.request({
      method: 'GET',
      path: `/api/v1/functions/upload/resumable/${this.sessionId}/status`
    });
    
    this.uploadedChunks = new Set(response.uploaded_chunks || []);
  }
  
  /**
   * Upload a single chunk
   */
  private async uploadChunk(chunkIndex: number, options?: UploadOptions) {
    const start = chunkIndex * this.chunkSize;
    const end = Math.min(start + this.chunkSize, this.file.size);
    const chunk = this.file.slice(start, end);
    
    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunk_index', String(chunkIndex));
    formData.append('session_id', this.sessionId);
    
    const response = await fetch(
      `${(this.uploadClient as any).client.baseUrl}/api/v1/functions/upload/resumable/chunk`,
      {
        method: 'POST',
        body: formData,
        signal: this.abortController?.signal
      }
    );
    
    if (!response.ok) {
      throw new Error(`Chunk upload failed: ${response.statusText}`);
    }
    
    this.uploadedChunks.add(chunkIndex);
    
    // Report progress
    if (options?.onProgress) {
      const progress: UploadProgress = {
        loaded: this.uploadedChunks.size * this.chunkSize,
        total: this.file.size,
        percentage: Math.round((this.uploadedChunks.size / this.totalChunks) * 100)
      };
      options.onProgress(progress);
    }
  }
  
  /**
   * Finalize the upload
   */
  private async finalize(): Promise<UploadResult> {
    const response = await (this.uploadClient as any).client.request({
      method: 'POST',
      path: `/api/v1/functions/upload/resumable/${this.sessionId}/finalize`
    });
    
    return response;
  }
}