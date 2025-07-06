/**
 * Project type definitions matching backend schemas
 */

export interface ProjectSettings {
  fps: number;
  resolution: [number, number];
  aspectRatio: string;
  defaultQuality: string;
  outputFormat: string;
}

export interface ProjectManifest {
  id: string;
  name: string;
  created: string;
  modified: string;
  version: string;
  quality: QualityLevel;
  takes_system_enabled: boolean;
  narrative: NarrativeConfig;
  settings: ProjectSettings;
  metadata: Record<string, any>;
  git: GitInfo;
}

export enum QualityLevel {
  LOW = 'low',
  STANDARD = 'standard',
  HIGH = 'high'
}

export interface NarrativeConfig {
  structure: NarrativeStructure;
  chapters: ChapterInfo[];
}

export enum NarrativeStructure {
  THREE_ACT = 'three-act',
  HERO_JOURNEY = 'hero-journey',
  BEAT_SHEET = 'beat-sheet',
  STORY_CIRCLE = 'story-circle'
}

export interface ChapterInfo {
  id: string;
  name: string;
  order: number;
  scenes: SceneInfo[];
}

export interface SceneInfo {
  id: string;
  name: string;
  order: number;
  shots: ShotInfo[];
  location?: string;
  characters: string[];
}

export interface ShotInfo {
  id: string;
  name: string;
  order: number;
  type: ShotType;
  duration?: number;
  camera_angle?: string;
  description?: string;
}

export enum ShotType {
  WIDE = 'wide',
  MEDIUM = 'medium',
  CLOSEUP = 'closeup',
  EXTREME_CLOSEUP = 'extreme_closeup',
  OVER_SHOULDER = 'over_shoulder',
  POV = 'pov',
  ESTABLISHING = 'establishing'
}

export interface GitInfo {
  initialized: boolean;
  lfs_enabled: boolean;
  branch?: string;
  last_commit?: string;
}

export interface WorkspaceProject {
  name: string;
  path: string;
  manifest?: ProjectManifest;
  git_status?: GitStatus;
}

export interface GitStatus {
  initialized: boolean;
  branch?: string;
  is_dirty?: boolean;
  untracked_files: string[];
  modified_files: string[];
  staged_files: string[];
  lfs_files?: string[];
}

export interface CharacterAsset {
  id: string;
  name: string;
  base_face: string;
  lora_path?: string;
  voice_model?: string;
  description?: string;
  variations: CharacterVariation[];
}

export interface CharacterVariation {
  id: string;
  name: string;
  type: 'age' | 'emotion' | 'costume' | 'custom';
  lora_strength?: number;
  prompt_modifier?: string;
}

export interface AssetReference {
  id: string;
  type: AssetType;
  path: string;
  metadata: Record<string, any>;
  git_lfs_tracked: boolean;
  created: string;
  modified: string;
}

export enum AssetType {
  CHARACTER = 'character',
  STYLE = 'style',
  LOCATION = 'location',
  MUSIC = 'music',
  SCRIPT = 'script',
  RENDER = 'render',
  EXPORT = 'export'
}

export interface CharacterAssetReference {
  assetId: string;
  // Minimal reference for type safety
  // Full implementation in PRD-004
}
