/**
 * Test Utility Functions
 */

export function generateProjectName(prefix = 'test-project'): string {
  const timestamp = Date.now();
  const randomStr = Math.random().toString(36).substring(2, 8);
  return `${prefix}-${timestamp}-${randomStr}`;
}

export function generateCharacterName(prefix = 'Character'): string {
  const timestamp = Date.now();
  return `${prefix} ${timestamp}`;
}

export async function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function formatBytes(bytes: number): string {
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 B';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

export function isValidProjectName(name: string): boolean {
  // Check for empty or too long
  if (!name || name.length > 255) return false;
  
  // Check for invalid characters
  const invalidChars = /[<>:"/\\|?*\x00-\x1f]/;
  if (invalidChars.test(name)) return false;
  
  // Check for Windows reserved names
  const reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                   'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                   'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'];
  if (reserved.includes(name.toUpperCase())) return false;
  
  // Check for dots at start/end
  if (name.startsWith('.') || name.endsWith('.')) return false;
  
  return true;
}

export interface TestProject {
  id: string;
  name: string;
  quality: string;
  path?: string;
}

export interface TestCharacter {
  id: string;
  name: string;
  description: string;
  triggerWord?: string;
}

export interface TestTask {
  id: string;
  type: string;
  status: string;
  progress: number;
  node_id: string;
}