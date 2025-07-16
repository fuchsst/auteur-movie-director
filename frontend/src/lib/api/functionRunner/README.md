# Function Runner API Client

Comprehensive TypeScript client for the Function Runner backend with automatic retries, progress tracking, and offline support.

## Installation

```typescript
import { createFunctionRunnerClient } from '$lib/api/functionRunner';

// Create client instance
const client = createFunctionRunnerClient('http://localhost:8000', {
  maxConcurrent: 5,
  cacheConfig: {
    ttl: 300000, // 5 minutes
    storage: 'localStorage'
  },
  retryConfig: {
    maxRetries: 3,
    baseDelay: 1000
  },
  offlineEnabled: true
});
```

## Basic Usage

### List Templates

```typescript
// List all templates
const templates = await client.listTemplates();

// Filter templates
const imageTemplates = await client.listTemplates({
  category: 'image',
  tags: ['generation'],
  backend_type: 'comfyui'
});

// Get specific template
const template = await client.getTemplate('stable-diffusion-xl');
```

### Submit Tasks

```typescript
// Submit a single task
const handle = await client.submitTask(
  'stable-diffusion-xl',
  {
    prompt: 'A beautiful sunset',
    negative_prompt: 'blurry, low quality',
    width: 1024,
    height: 1024
  },
  {
    quality: 'high',
    priority: 10,
    onProgress: (progress) => {
      console.log(`${progress.stage}: ${progress.progress}%`);
    },
    onComplete: (result) => {
      console.log('Task completed:', result);
    },
    onError: (error) => {
      console.error('Task failed:', error);
    }
  }
);

// Wait for completion
const result = await handle.wait();

// Or check status
const status = await handle.getStatus();

// Cancel if needed
await handle.cancel();
```

### Batch Operations

```typescript
// Submit multiple tasks
const batchHandle = await client.submitBatch([
  {
    template_id: 'stable-diffusion-xl',
    inputs: { prompt: 'Sunset' },
    quality: 'standard',
    priority: 5,
    task_name: 'sunset'
  },
  {
    template_id: 'stable-diffusion-xl',
    inputs: { prompt: 'Sunrise' },
    quality: 'standard',
    priority: 5,
    task_name: 'sunrise'
  }
], {
  parallel: true,
  stopOnError: false,
  onBatchProgress: (progress) => {
    console.log(`Batch: ${progress.completed}/${progress.total}`);
  }
});

// Get batch results
const results = await batchHandle.getResults();
```

### File Uploads

```typescript
// Upload single file
const uploadResult = await client.upload.uploadFile(file, {
  metadata: { type: 'reference' },
  onProgress: (progress) => {
    console.log(`Upload: ${progress.percentage}%`);
  }
});

// Upload multiple files
const results = await client.upload.uploadFiles(files, {
  parallel: true,
  onProgress: (progress) => {
    console.log(`Total: ${progress.percentage}%`);
  }
});

// Resumable upload for large files
const resumable = await client.upload.createResumableUpload(largeFile);
try {
  const result = await resumable.start({
    onProgress: (progress) => {
      console.log(`Resumable: ${progress.percentage}%`);
    }
  });
} catch (error) {
  // Can resume later
  await resumable.start();
}
```

## Advanced Features

### Progress Tracking

Tasks automatically report progress via WebSocket:

```typescript
const handle = await client.submitTask(templateId, inputs, {
  onProgress: (progress) => {
    // Progress updates
    console.log({
      stage: progress.stage,        // 'queued', 'processing', 'finalizing'
      progress: progress.progress,   // 0-100
      message: progress.message,     // Optional status message
      eta: progress.eta,            // Estimated completion time
      metadata: progress.metadata    // Additional data
    });
  }
});
```

### Offline Queue

When offline support is enabled, requests are automatically queued:

```typescript
// Configure offline support
const client = createFunctionRunnerClient(baseUrl, {
  offlineEnabled: true
});

// Requests made while offline are queued
// They'll be processed when connection is restored
const handle = await client.submitTask(...); // Queued if offline

// The promise resolves when the request is eventually processed
```

### Request Queue Management

Control concurrent requests:

```typescript
// Get queue statistics
const stats = client.requestQueue.getStats();
console.log(`Active: ${stats.active}, Queued: ${stats.queued}`);

// Pause/resume processing
client.requestQueue.pause();
// ... do something ...
client.requestQueue.resume();

// Update concurrency limit
client.requestQueue.setMaxConcurrent(10);
```

### Custom Retry Strategy

```typescript
import { RetryStrategy } from '$lib/api/functionRunner';

// Create custom retry strategy
const customRetry = RetryStrategy.custom({
  maxRetries: 5,
  shouldRetry: (error, attempt) => {
    // Custom logic
    return attempt < 5 && error.status >= 500;
  },
  calculateDelay: (attempt) => {
    // Custom backoff
    return Math.min(1000 * Math.pow(3, attempt), 60000);
  }
});

// Use with client
const client = new FunctionRunnerClient({
  retryStrategy: customRetry,
  // ... other config
});
```

## Svelte Integration

### Store Integration

```svelte
<script lang="ts">
  import { createFunctionRunnerClient } from '$lib/api/functionRunner';
  import { writable } from 'svelte/store';
  
  const client = createFunctionRunnerClient();
  const progress = writable(0);
  const result = writable(null);
  
  async function generate() {
    const handle = await client.submitTask('template-id', inputs, {
      onProgress: (p) => progress.set(p.progress),
      onComplete: (r) => result.set(r)
    });
  }
</script>

<button on:click={generate}>Generate</button>
{#if $progress > 0}
  <progress value={$progress} max="100">{$progress}%</progress>
{/if}
```

### Component Example

```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { TaskHandle } from '$lib/api/functionRunner';
  
  export let templateId: string;
  export let inputs: Record<string, any>;
  
  let handle: TaskHandle | null = null;
  let status = 'idle';
  let progress = 0;
  let result = null;
  let error = null;
  
  async function start() {
    status = 'running';
    error = null;
    
    try {
      handle = await client.submitTask(templateId, inputs, {
        onProgress: (p) => {
          progress = p.progress;
        },
        onComplete: (r) => {
          result = r;
          status = 'completed';
        },
        onError: (e) => {
          error = e;
          status = 'failed';
        }
      });
    } catch (e) {
      error = e;
      status = 'failed';
    }
  }
  
  async function cancel() {
    if (handle) {
      await handle.cancel();
      status = 'cancelled';
    }
  }
  
  onDestroy(() => {
    handle?.dispose();
  });
</script>

<div class="task-runner">
  {#if status === 'idle'}
    <button on:click={start}>Start Task</button>
  {:else if status === 'running'}
    <progress value={progress} max="100">{progress}%</progress>
    <button on:click={cancel}>Cancel</button>
  {:else if status === 'completed'}
    <div class="result">{JSON.stringify(result)}</div>
  {:else if status === 'failed'}
    <div class="error">{error.message}</div>
  {/if}
</div>
```

## Error Handling

```typescript
import { FunctionRunnerError } from '$lib/api/functionRunner';

try {
  const result = await client.submitTask(...);
} catch (error) {
  if (error instanceof FunctionRunnerError) {
    console.error('API Error:', {
      message: error.message,
      status: error.status,
      body: error.body,
      code: error.code
    });
  } else {
    console.error('Unknown error:', error);
  }
}
```

## Type Safety

All operations are fully typed:

```typescript
// Template types
const template: FunctionTemplate = await client.getTemplate('id');

// Input validation
const inputs: typeof template.parameter_schema = {
  // TypeScript ensures correct types
};

// Result types
const result: TaskResult = await handle.wait();
if (result.status === 'completed') {
  // Access outputs safely
  const output = result.outputs?.image;
}
```

## Performance Tips

1. **Enable Caching**: Use localStorage or IndexedDB for persistent caching
2. **Batch Operations**: Submit multiple tasks in one request
3. **Limit Concurrency**: Adjust based on server capacity
4. **Use Quality Presets**: Lower quality for previews, higher for finals
5. **Handle Progress**: Update UI with progress for better UX
6. **Dispose Handles**: Clean up when components unmount

## API Reference

See the [type definitions](./types.ts) for complete API documentation.