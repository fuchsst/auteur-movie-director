import { canvasStore } from '$lib/canvas/core/canvas-store';

export interface PerformanceMetrics {
  fps: number;
  nodeCount: number;
  edgeCount: number;
  memoryUsage: number;
  renderTime: number;
  interactionLatency: number;
}

export interface OptimizationSettings {
  enableVirtualization: boolean;
  maxVisibleNodes: number;
  enableLOD: boolean;
  minZoomForDetail: number;
  enableCaching: boolean;
  cacheSize: number;
  enableWebWorkers: boolean;
  workerPoolSize: number;
}

export class PerformanceOptimizer {
  private settings: OptimizationSettings = {
    enableVirtualization: true,
    maxVisibleNodes: 500,
    enableLOD: true,
    minZoomForDetail: 0.5,
    enableCaching: true,
    cacheSize: 1000,
    enableWebWorkers: true,
    workerPoolSize: 4
  };

  private metrics: PerformanceMetrics = {
    fps: 60,
    nodeCount: 0,
    edgeCount: 0,
    memoryUsage: 0,
    renderTime: 0,
    interactionLatency: 0
  };

  private frameCount = 0;
  private lastFrameTime = 0;
  private animationFrameId: number | null = null;
  private observer: PerformanceObserver | null = null;
  private cache = new Map<string, any>();
  private workers: Worker[] = [];

  constructor() {
    this.initializeWorkers();
    this.startMonitoring();
    this.setupCanvasStoreSubscription();
  }

  private initializeWorkers() {
    if (this.settings.enableWebWorkers && typeof Worker !== 'undefined') {
      for (let i = 0; i < this.settings.workerPoolSize; i++) {
        try {
          const worker = new Worker('/workers/canvas-worker.js');
          this.workers.push(worker);
        } catch (error) {
          console.warn('Failed to create worker:', error);
        }
      }
    }
  }

  private setupCanvasStoreSubscription() {
    canvasStore.subscribe(state => {
      this.metrics.nodeCount = state.nodes.length;
      this.metrics.edgeCount = state.edges.length;
      this.applyOptimizations();
    });
  }

  private startMonitoring() {
    if (typeof PerformanceObserver !== 'undefined') {
      this.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'measure') {
            this.updateMetrics(entry);
          }
        }
      });
      this.observer.observe({ entryTypes: ['measure', 'navigation'] });
    }

    this.startFPSCounter();
  }

  private startFPSCounter() {
    const measureFPS = () => {
      const now = performance.now();
      if (this.lastFrameTime) {
        const delta = now - this.lastFrameTime;
        this.metrics.fps = Math.round(1000 / delta);
      }
      this.lastFrameTime = now;
      this.frameCount++;

      this.animationFrameId = requestAnimationFrame(measureFPS);
    };
    measureFPS();
  }

  private updateMetrics(entry: PerformanceEntry) {
    if (entry.name.includes('render')) {
      this.metrics.renderTime = entry.duration;
    } else if (entry.name.includes('interaction')) {
      this.metrics.interactionLatency = entry.duration;
    }
  }

  public getMetrics(): PerformanceMetrics {
    if (typeof performance !== 'undefined' && performance.memory) {
      this.metrics.memoryUsage = performance.memory.usedJSHeapSize / 1024 / 1024;
    }
    return { ...this.metrics };
  }

  public optimizeForNodeCount(nodeCount: number): void {
    if (nodeCount > 100) {
      this.settings.enableVirtualization = true;
      this.settings.enableLOD = true;
    }
    
    if (nodeCount > 500) {
      this.settings.maxVisibleNodes = Math.min(500, nodeCount);
      this.settings.enableCaching = true;
    }
    
    if (nodeCount > 1000) {
      this.settings.maxVisibleNodes = Math.min(300, nodeCount);
      this.settings.cacheSize = 2000;
    }
  }

  public applyOptimizations(): void {
    const state = canvasStore.get();
    this.optimizeForNodeCount(state.nodes.length);
    
    if (this.settings.enableVirtualization) {
      this.applyVirtualization();
    }
    
    if (this.settings.enableLOD) {
      this.applyLevelOfDetail();
    }
    
    if (this.settings.enableCaching) {
      this.setupCaching();
    }
  }

  private applyVirtualization() {
    const state = canvasStore.get();
    const visibleNodes = this.calculateVisibleNodes(state.nodes, state.viewport);
    
    if (visibleNodes.length > this.settings.maxVisibleNodes) {
      // Implement node virtualization
      const optimizedNodes = visibleNodes.slice(0, this.settings.maxVisibleNodes);
      this.cache.set('visible-nodes', optimizedNodes);
    }
  }

  private calculateVisibleNodes(nodes: any[], viewport: any): any[] {
    const { x, y, zoom } = viewport;
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;
    
    const visibleBounds = {
      left: x - screenWidth / (2 * zoom),
      right: x + screenWidth / (2 * zoom),
      top: y - screenHeight / (2 * zoom),
      bottom: y + screenHeight / (2 * zoom)
    };

    return nodes.filter(node => {
      const pos = node.position;
      return pos.x >= visibleBounds.left &&
             pos.x <= visibleBounds.right &&
             pos.y >= visibleBounds.top &&
             pos.y <= visibleBounds.bottom;
    });
  }

  private applyLevelOfDetail() {
    const state = canvasStore.get();
    const zoom = state.viewport.zoom;
    
    if (zoom < this.settings.minZoomForDetail) {
      // Simplify rendering for distant nodes
      this.simplifyNodes(state.nodes);
    } else {
      // Full detail rendering
      this.restoreFullDetail();
    }
  }

  private simplifyNodes(nodes: any[]) {
    const simplified = nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        simplified: true,
        hideDetails: true
      }
    }));
    
    this.cache.set('simplified-nodes', simplified);
  }

  private restoreFullDetail() {
    const cached = this.cache.get('simplified-nodes');
    if (cached) {
      // Restore full detail
      this.cache.delete('simplified-nodes');
    }
  }

  private setupCaching() {
    // Implement LRU cache for node data
    const lruCache = new Map();
    const maxCacheSize = this.settings.cacheSize;

    return {
      get: (key: string) => lruCache.get(key),
      set: (key: string, value: any) => {
        if (lruCache.size >= maxCacheSize) {
          const firstKey = lruCache.keys().next().value;
          lruCache.delete(firstKey);
        }
        lruCache.set(key, value);
      },
      clear: () => lruCache.clear()
    };
  }

  public async optimizeLayout(nodes: any[]): Promise<any[]> {
    if (this.workers.length === 0) {
      return this.optimizeLayoutSync(nodes);
    }

    const worker = this.workers[0]; // Round-robin worker selection
    return new Promise((resolve) => {
      const messageId = Date.now().toString();
      
      const handleMessage = (event: MessageEvent) => {
        if (event.data.id === messageId) {
          worker.removeEventListener('message', handleMessage);
          resolve(event.data.result);
        }
      };
      
      worker.addEventListener('message', handleMessage);
      worker.postMessage({ type: 'optimizeLayout', nodes, id: messageId });
    });
  }

  private optimizeLayoutSync(nodes: any[]): any[] {
    // Synchronous layout optimization
    const gridSize = Math.ceil(Math.sqrt(nodes.length));
    const spacing = 200;
    
    return nodes.map((node, index) => ({
      ...node,
      position: {
        x: (index % gridSize) * spacing,
        y: Math.floor(index / gridSize) * spacing
      }
    }));
  }

  public debounceRender(callback: () => void, delay: number = 16): () => void {
    let timeoutId: NodeJS.Timeout;
    
    return () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(callback, delay);
    };
  }

  public throttleInteraction(callback: () => void, limit: number = 60): () => void {
    let inThrottle: boolean;
    
    return () => {
      if (!inThrottle) {
        callback();
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  public measurePerformance(): PerformanceMetrics {
    const metrics = this.getMetrics();
    
    // Log performance warnings
    if (metrics.fps < 30) {
      console.warn('Low FPS detected:', metrics.fps);
    }
    
    if (metrics.memoryUsage > 100) {
      console.warn('High memory usage:', metrics.memoryUsage, 'MB');
    }
    
    if (metrics.nodeCount > 1000) {
      console.warn('High node count:', metrics.nodeCount);
    }
    
    return metrics;
  }

  public dispose(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    
    if (this.observer) {
      this.observer.disconnect();
    }
    
    this.workers.forEach(worker => worker.terminate());
    this.workers = [];
    
    this.cache.clear();
  }

  public getOptimizationSettings(): OptimizationSettings {
    return { ...this.settings };
  }

  public updateSettings(newSettings: Partial<OptimizationSettings>): void {
    this.settings = { ...this.settings, ...newSettings };
    this.applyOptimizations();
  }

  public resetToDefaults(): void {
    this.settings = {
      enableVirtualization: true,
      maxVisibleNodes: 500,
      enableLOD: true,
      minZoomForDetail: 0.5,
      enableCaching: true,
      cacheSize: 1000,
      enableWebWorkers: true,
      workerPoolSize: 4
    };
    this.applyOptimizations();
  }
}

export const performanceOptimizer = new PerformanceOptimizer();