/**
 * Main type definitions
 */

// Task management
export interface Task {
  id: string;
  name: string;
  type: 'upload' | 'download' | 'generation' | 'training' | 'processing' | 'export';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  details?: string;
  createdAt: number;
  completedAt?: number;
  estimatedTimeRemaining?: number;
  cancellable?: boolean;
  error?: string;
}

// Notification system
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  priority: 'low' | 'medium' | 'high';
  timestamp: number;
  read: boolean;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}

// View tab system
export interface ViewTab {
  id: string;
  label: string;
  icon: string;
  component: any; // Svelte component
  shortcut?: string;
  closeable?: boolean;
}

export interface ViewState {
  zoom?: number;
  pan?: { x: number; y: number };
  selection?: string[];
  filters?: Record<string, any>;
}

// Re-export other types
export * from './project';
export * from './websocket';
export * from './nodes';
export * from './properties';
