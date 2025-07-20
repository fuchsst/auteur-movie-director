/**
 * Asset Propagation System Types
 * STORY-089 Implementation
 */

export enum HierarchyLevel {
  PROJECT = 'project',
  ACT = 'act',
  CHAPTER = 'chapter',
  SCENE = 'scene',
  SHOT = 'shot',
  TAKE = 'take'
}

export enum PropagationMode {
  INHERIT = 'inherit',
  OVERRIDE = 'override',
  MERGE = 'merge',
  BLOCK = 'block'
}

export interface AssetPropagationRule {
  ruleId: string;
  assetType: string;
  sourceLevel: HierarchyLevel;
  targetLevel: HierarchyLevel;
  propagationMode: PropagationMode;
  conditions: Record<string, any>;
  priority: number;
  enabled: boolean;
}

export interface AssetReference {
  assetId: string;
  assetType: string;
  referenceId: string;
  level: HierarchyLevel;
  levelId: string;
  sourceLevel: HierarchyLevel;
  sourceId: string;
  overrideData: Record<string, any>;
  isOverridden: boolean;
  usageContext: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface AssetPropagationContext {
  projectId: string;
  level: HierarchyLevel;
  levelId: string;
  parentContext?: AssetPropagationContext;
  childContexts: AssetPropagationContext[];
  localAssets: AssetReference[];
  inheritedAssets: AssetReference[];
  resolvedAssets: Record<string, AssetReference>;
  overrideRules: AssetPropagationRule[];
}

export interface AssetPropagationRequest {
  projectId: string;
  level: HierarchyLevel;
  levelId: string;
  assetId: string;
  assetType: string;
  overrideData?: Record<string, any>;
}

export interface PropagationRuleRequest {
  assetType: string;
  sourceLevel: HierarchyLevel;
  targetLevel: HierarchyLevel;
  propagationMode: PropagationMode;
  conditions?: Record<string, any>;
  priority?: number;
}

export interface AssetResolutionResponse {
  projectId: string;
  level: HierarchyLevel;
  levelId: string;
  resolvedAssets: Record<string, AssetReference[]>;
  totalAssets: number;
  assetTypes: Record<string, number>;
}

export interface AssetUsageResponse {
  assetId: string;
  usageCount: number;
  usageLocations: AssetUsageLocation[];
}

export interface AssetUsageLocation {
  level: HierarchyLevel;
  levelId: string;
  usageContext: Record<string, any>;
  timestamp: string;
}

export interface GenerationContext {
  characters: GenerationAsset[];
  styles: GenerationAsset[];
  locations: GenerationAsset[];
  props: GenerationAsset[];
  wardrobe: GenerationAsset[];
  vehicles: GenerationAsset[];
  setDressing: GenerationAsset[];
  sfx: GenerationAsset[];
  sounds: GenerationAsset[];
  music: GenerationAsset[];
  metadata: {
    projectId: string;
    level: HierarchyLevel;
    levelId: string;
    resolvedAt: string;
  };
}

export interface GenerationAsset {
  id: string;
  type: string;
  overrideData: Record<string, any>;
  context: Record<string, any>;
}

export interface AssetConsistencyReport {
  assetId: string;
  usageCount: number;
  levels: HierarchyLevel[];
  consistent: boolean;
  issues: string[];
  warnings?: string[];
}

export interface HierarchyValidation {
  projectId: string;
  consistent: boolean;
  issues: string[];
  warnings: string[];
  statistics: Record<string, number>;
}

// API request/response types
export interface AddAssetRequest {
  projectId: string;
  level: HierarchyLevel;
  levelId: string;
  assetId: string;
  assetType: string;
  overrideData?: Record<string, any>;
}

export interface AddRuleRequest {
  assetType: string;
  sourceLevel: HierarchyLevel;
  targetLevel: HierarchyLevel;
  propagationMode: PropagationMode;
  conditions?: Record<string, any>;
  priority?: number;
}

export interface AssetPropagationState {
  projectId: string;
  timestamp: string;
  contexts: Record<string, {
    level: HierarchyLevel;
    levelId: string;
    localAssets: AssetReference[];
    resolvedAssets: Record<string, AssetReference>;
  }>;
  rules: AssetPropagationRule[];
  validation: HierarchyValidation;
}