import { writable, type Writable } from 'svelte/store';

export interface PersistentStoreOptions<T> {
  defaultValue: T;
  serializer?: {
    parse: (text: string) => T;
    stringify: (value: T) => string;
  };
}

/**
 * Create a persistent Svelte store that syncs with localStorage
 */
export function persistent<T>(
  key: string,
  defaultValue: T,
  options?: Partial<PersistentStoreOptions<T>>
): Writable<T> {
  const {
    serializer = {
      parse: JSON.parse,
      stringify: JSON.stringify,
    },
  } = options || {};

  // Initialize with default value
  let storedValue: T = defaultValue;

  // Try to load from localStorage
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem(key);
      if (stored !== null) {
        storedValue = serializer.parse(stored);
      }
    } catch (error) {
      console.warn(`Failed to load ${key} from localStorage:`, error);
    }
  }

  const store = writable<T>(storedValue);

  // Subscribe to changes and save to localStorage
  store.subscribe((value) => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(key, serializer.stringify(value));
      } catch (error) {
        console.warn(`Failed to save ${key} to localStorage:`, error);
      }
    }
  });

  return {
    ...store,
    
    // Override set to handle errors gracefully
    set(value: T) {
      store.set(value);
    },
    
    // Override update to handle errors gracefully
    update(updater: (value: T) => T) {
      store.update(updater);
    },
    
    // Add clear method to remove from storage
    clear() {
      if (typeof window !== 'undefined') {
        localStorage.removeItem(key);
      }
      store.set(defaultValue);
    },
    
    // Add get method to get current value without subscribing
    get(): T {
      let currentValue: T = defaultValue;
      store.subscribe(value => { currentValue = value; })();
      return currentValue;
    }
  };
}

/**
 * Create a persistent store with sessionStorage instead of localStorage
 */
export function sessionPersistent<T>(
  key: string,
  defaultValue: T,
  options?: Partial<PersistentStoreOptions<T>>
): Writable<T> {
  const {
    serializer = {
      parse: JSON.parse,
      stringify: JSON.stringify,
    },
  } = options || {};

  let storedValue: T = defaultValue;

  if (typeof window !== 'undefined') {
    try {
      const stored = sessionStorage.getItem(key);
      if (stored !== null) {
        storedValue = serializer.parse(stored);
      }
    } catch (error) {
      console.warn(`Failed to load ${key} from sessionStorage:`, error);
    }
  }

  const store = writable<T>(storedValue);

  store.subscribe((value) => {
    if (typeof window !== 'undefined') {
      try {
        sessionStorage.setItem(key, serializer.stringify(value));
      } catch (error) {
        console.warn(`Failed to save ${key} to sessionStorage:`, error);
      }
    }
  });

  return {
    ...store,
    clear() {
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem(key);
      }
      store.set(defaultValue);
    },
    get(): T {
      let currentValue: T = defaultValue;
      store.subscribe(value => { currentValue = value; })();
      return currentValue;
    }
  };
}

/**
 * Clear all persistent stores with a given prefix
 */
export function clearPersistentStores(prefix: string): void {
  if (typeof window === 'undefined') return;

  const keys: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith(prefix)) {
      keys.push(key);
    }
  }
  
  keys.forEach(key => localStorage.removeItem(key));
}

/**
 * Get all keys with a given prefix
 */
export function getPersistentKeys(prefix: string): string[] {
  if (typeof window === 'undefined') return [];

  const keys: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith(prefix)) {
      keys.push(key);
    }
  }
  return keys;
}