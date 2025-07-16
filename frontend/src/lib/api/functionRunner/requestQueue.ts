/**
 * Request queue for managing concurrent requests
 */

interface QueuedRequest<T = any> {
  fn: () => Promise<T>;
  resolve: (value: T) => void;
  reject: (error: any) => void;
  priority?: number;
}

export class RequestQueue {
  private queue: QueuedRequest[] = [];
  private active = 0;
  private paused = false;
  
  constructor(private maxConcurrent: number = 5) {}
  
  /**
   * Add a request to the queue
   */
  async add<T>(fn: () => Promise<T>, priority: number = 5): Promise<T> {
    return new Promise((resolve, reject) => {
      const request: QueuedRequest<T> = { fn, resolve, reject, priority };
      
      // Insert based on priority (higher priority first)
      const insertIndex = this.queue.findIndex(r => (r.priority || 5) < priority);
      if (insertIndex === -1) {
        this.queue.push(request);
      } else {
        this.queue.splice(insertIndex, 0, request);
      }
      
      this.process();
    });
  }
  
  /**
   * Process queued requests
   */
  private async process() {
    if (this.paused || this.active >= this.maxConcurrent || this.queue.length === 0) {
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
      // Process next request
      setImmediate(() => this.process());
    }
  }
  
  /**
   * Pause processing
   */
  pause() {
    this.paused = true;
  }
  
  /**
   * Resume processing
   */
  resume() {
    this.paused = false;
    // Start processing again
    for (let i = 0; i < this.maxConcurrent; i++) {
      this.process();
    }
  }
  
  /**
   * Clear the queue
   */
  clear() {
    const error = new Error('Request queue cleared');
    for (const request of this.queue) {
      request.reject(error);
    }
    this.queue = [];
  }
  
  /**
   * Get queue statistics
   */
  getStats() {
    return {
      queued: this.queue.length,
      active: this.active,
      paused: this.paused,
      maxConcurrent: this.maxConcurrent
    };
  }
  
  /**
   * Update max concurrent requests
   */
  setMaxConcurrent(max: number) {
    this.maxConcurrent = max;
    // Process more if we increased the limit
    if (!this.paused) {
      for (let i = this.active; i < max && i < this.queue.length; i++) {
        this.process();
      }
    }
  }
}