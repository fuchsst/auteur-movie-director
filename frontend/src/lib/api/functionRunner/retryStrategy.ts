/**
 * Retry strategy with exponential backoff
 */

import type { RetryConfig } from './types';

export class RetryStrategy {
  private maxRetries: number;
  private baseDelay: number;
  private maxDelay: number;
  private retryableStatuses: Set<number>;
  
  constructor(config?: RetryConfig) {
    this.maxRetries = config?.maxRetries ?? 3;
    this.baseDelay = config?.baseDelay ?? 1000;
    this.maxDelay = config?.maxDelay ?? 30000;
    this.retryableStatuses = new Set(
      config?.retryableStatuses ?? [408, 429, 500, 502, 503, 504]
    );
  }
  
  /**
   * Execute a function with retry logic
   */
  async execute<T>(
    fn: () => Promise<Response>,
    maxRetries?: number
  ): Promise<Response> {
    const attempts = maxRetries ?? this.maxRetries;
    let lastError: any;
    
    for (let attempt = 0; attempt <= attempts; attempt++) {
      try {
        const response = await fn();
        
        // Check if we should retry based on status
        if (!response.ok && attempt < attempts && this.shouldRetry(response)) {
          lastError = new Error(`HTTP ${response.status}: ${response.statusText}`);
          await this.delay(attempt);
          continue;
        }
        
        return response;
      } catch (error) {
        lastError = error;
        
        // Check if error is retryable
        if (attempt < attempts && this.isRetryableError(error)) {
          await this.delay(attempt);
          continue;
        }
        
        throw error;
      }
    }
    
    throw lastError;
  }
  
  /**
   * Check if response status indicates we should retry
   */
  private shouldRetry(response: Response): boolean {
    return this.retryableStatuses.has(response.status);
  }
  
  /**
   * Check if error is retryable
   */
  private isRetryableError(error: any): boolean {
    // Network errors
    if (error.name === 'NetworkError' || error.name === 'TypeError') {
      return true;
    }
    
    // Timeout errors
    if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
      return true;
    }
    
    // Connection errors
    if (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET') {
      return true;
    }
    
    return false;
  }
  
  /**
   * Calculate delay with exponential backoff and jitter
   */
  private async delay(attempt: number): Promise<void> {
    const exponentialDelay = Math.min(
      this.baseDelay * Math.pow(2, attempt),
      this.maxDelay
    );
    
    // Add jitter (±25%)
    const jitter = exponentialDelay * 0.25 * (Math.random() * 2 - 1);
    const finalDelay = Math.max(0, exponentialDelay + jitter);
    
    await new Promise(resolve => setTimeout(resolve, finalDelay));
  }
  
  /**
   * Create a custom retry strategy
   */
  static custom(config: {
    shouldRetry: (error: any, attempt: number) => boolean;
    calculateDelay: (attempt: number) => number;
    maxRetries?: number;
  }): RetryStrategy {
    const strategy = new RetryStrategy({ maxRetries: config.maxRetries });
    
    // Override methods
    (strategy as any).isRetryableError = (error: any) => {
      return config.shouldRetry(error, 0);
    };
    
    (strategy as any).delay = async (attempt: number) => {
      const delay = config.calculateDelay(attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    };
    
    return strategy;
  }
}