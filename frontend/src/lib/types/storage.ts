/**
 * Storage metrics and management types
 */

export interface StorageMetrics {
  projectId: string;
  totalSize: number;
  breakdown: StorageBreakdown;
  takesDetails: TakesStorageDetails;
  storageLimit: number;
  usagePercentage: number;
}

export interface StorageBreakdown {
  takes: number;
  media: number;
  thumbnails: number;
  assets: number;
  exports: number;
  other: number;
}

export interface TakesStorageDetails {
  count: number;
  byQuality: Record<string, number>;
  byStatus: Record<string, number>;
  largest: LargeTake[];
}

export interface LargeTake {
  id: string;
  shotId: string;
  size: number;
  quality: string;
}

export interface CleanupStats {
  orphanedDirectories: number;
  orphanedFiles: number;
  bytesFreed: number;
}

export interface CleanupResponse {
  projectId: string;
  cleanupStats: CleanupStats;
  message: string;
}
