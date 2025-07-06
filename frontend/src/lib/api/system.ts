/**
 * System information API client
 */

import { api } from './client';

export interface SystemInfo {
  version: string;
  pythonVersion: string;
  nodeVersion: string | null;
  platform: string;
  gitVersion: string | null;
  gitLFSInstalled: boolean;
  dockerVersion: string | null;
  workspacePath: string;
  apiEndpoint: string;
  gpuSupport?: boolean;
}

export const systemApi = {
  /**
   * Get system information
   */
  async getSystemInfo(): Promise<SystemInfo> {
    return api.get<SystemInfo>('/system/info');
  }
};
