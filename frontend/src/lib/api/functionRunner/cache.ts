/**
 * Response cache implementation
 */

import type { CacheConfig } from './types';

interface CacheEntry<T = any> {
  value: T;
  expires: number;
  size: number;
}

export class ResponseCache {
  private storage: CacheStorage;
  private memoryCache: Map<string, CacheEntry> = new Map();
  private totalSize = 0;
  private readonly maxSize: number;
  private readonly defaultTTL: number;
  
  constructor(config?: CacheConfig) {
    this.maxSize = config?.maxSize ?? 50 * 1024 * 1024; // 50MB default
    this.defaultTTL = config?.ttl ?? 300000; // 5 minutes default
    this.storage = this.createStorage(config?.storage);
  }
  
  private createStorage(type?: 'memory' | 'localStorage' | 'indexedDB'): CacheStorage {
    switch (type) {
      case 'localStorage':
        return new LocalStorageCache();
      case 'indexedDB':
        return new IndexedDBCache();
      case 'memory':
      default:
        return new MemoryCache(this.memoryCache);
    }
  }
  
  /**
   * Create a cache key from method and params
   */
  createKey(method: string, params?: any): string {
    const paramStr = params ? JSON.stringify(params, Object.keys(params).sort()) : '';
    return `${method}:${paramStr}`;
  }
  
  /**
   * Get item from cache
   */
  async get<T>(key: string): Promise<T | null> {
    const entry = await this.storage.get<CacheEntry<T>>(key);
    
    if (!entry) {
      return null;
    }
    
    // Check expiration
    if (entry.expires < Date.now()) {
      await this.delete(key);
      return null;
    }
    
    return entry.value;
  }
  
  /**
   * Set item in cache
   */
  async set<T>(key: string, value: T, ttl?: number): Promise<void> {
    const size = this.estimateSize(value);
    const expires = Date.now() + (ttl ?? this.defaultTTL);
    
    // Evict if necessary
    await this.evictIfNeeded(size);
    
    const entry: CacheEntry<T> = { value, expires, size };
    await this.storage.set(key, entry);
    
    if (this.storage instanceof MemoryCache) {
      this.totalSize += size;
    }
  }
  
  /**
   * Delete item from cache
   */
  async delete(key: string): Promise<void> {
    const entry = await this.storage.get<CacheEntry>(key);
    if (entry && this.storage instanceof MemoryCache) {
      this.totalSize -= entry.size;
    }
    
    await this.storage.delete(key);
  }
  
  /**
   * Clear all cache
   */
  async clear(): Promise<void> {
    await this.storage.clear();
    this.totalSize = 0;
  }
  
  /**
   * Estimate size of a value
   */
  private estimateSize(value: any): number {
    const str = JSON.stringify(value);
    return new Blob([str]).size;
  }
  
  /**
   * Evict old entries if needed
   */
  private async evictIfNeeded(requiredSize: number): Promise<void> {
    if (!(this.storage instanceof MemoryCache)) {
      return; // Only memory cache tracks size
    }
    
    while (this.totalSize + requiredSize > this.maxSize && this.memoryCache.size > 0) {
      // Find oldest entry
      let oldestKey: string | null = null;
      let oldestTime = Infinity;
      
      for (const [key, entry] of this.memoryCache) {
        if (entry.expires < oldestTime) {
          oldestTime = entry.expires;
          oldestKey = key;
        }
      }
      
      if (oldestKey) {
        await this.delete(oldestKey);
      } else {
        break;
      }
    }
  }
}

/**
 * Cache storage interface
 */
interface CacheStorage {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
}

/**
 * Memory cache storage
 */
class MemoryCache implements CacheStorage {
  constructor(private cache: Map<string, any>) {}
  
  async get<T>(key: string): Promise<T | null> {
    return this.cache.get(key) ?? null;
  }
  
  async set<T>(key: string, value: T): Promise<void> {
    this.cache.set(key, value);
  }
  
  async delete(key: string): Promise<void> {
    this.cache.delete(key);
  }
  
  async clear(): Promise<void> {
    this.cache.clear();
  }
}

/**
 * LocalStorage cache storage
 */
class LocalStorageCache implements CacheStorage {
  private readonly prefix = 'fnrunner:';
  
  async get<T>(key: string): Promise<T | null> {
    try {
      const item = localStorage.getItem(this.prefix + key);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  }
  
  async set<T>(key: string, value: T): Promise<void> {
    try {
      localStorage.setItem(this.prefix + key, JSON.stringify(value));
    } catch (e) {
      // Storage quota exceeded, clear old entries
      this.clearOldEntries();
      localStorage.setItem(this.prefix + key, JSON.stringify(value));
    }
  }
  
  async delete(key: string): Promise<void> {
    localStorage.removeItem(this.prefix + key);
  }
  
  async clear(): Promise<void> {
    const keys = Object.keys(localStorage);
    for (const key of keys) {
      if (key.startsWith(this.prefix)) {
        localStorage.removeItem(key);
      }
    }
  }
  
  private clearOldEntries() {
    const entries: Array<[string, CacheEntry]> = [];
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.prefix)) {
        try {
          const value = JSON.parse(localStorage.getItem(key)!);
          entries.push([key, value]);
        } catch {
          // Invalid entry, remove it
          localStorage.removeItem(key);
        }
      }
    }
    
    // Sort by expiration
    entries.sort((a, b) => a[1].expires - b[1].expires);
    
    // Remove oldest half
    const toRemove = Math.floor(entries.length / 2);
    for (let i = 0; i < toRemove; i++) {
      localStorage.removeItem(entries[i][0]);
    }
  }
}

/**
 * IndexedDB cache storage
 */
class IndexedDBCache implements CacheStorage {
  private dbName = 'fnrunner-cache';
  private storeName = 'responses';
  private db?: IDBDatabase;
  
  private async getDB(): Promise<IDBDatabase> {
    if (this.db) return this.db;
    
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName);
        }
      };
    });
  }
  
  async get<T>(key: string): Promise<T | null> {
    const db = await this.getDB();
    const tx = db.transaction(this.storeName, 'readonly');
    const store = tx.objectStore(this.storeName);
    
    return new Promise((resolve) => {
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result ?? null);
      request.onerror = () => resolve(null);
    });
  }
  
  async set<T>(key: string, value: T): Promise<void> {
    const db = await this.getDB();
    const tx = db.transaction(this.storeName, 'readwrite');
    const store = tx.objectStore(this.storeName);
    
    return new Promise((resolve, reject) => {
      const request = store.put(value, key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
  
  async delete(key: string): Promise<void> {
    const db = await this.getDB();
    const tx = db.transaction(this.storeName, 'readwrite');
    const store = tx.objectStore(this.storeName);
    
    return new Promise((resolve, reject) => {
      const request = store.delete(key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
  
  async clear(): Promise<void> {
    const db = await this.getDB();
    const tx = db.transaction(this.storeName, 'readwrite');
    const store = tx.objectStore(this.storeName);
    
    return new Promise((resolve, reject) => {
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}