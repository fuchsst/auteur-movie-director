export interface SceneTimelineData {
  id: string;
  title: string;
  description: string;
  startPosition: number;
  duration: number;
  characters: string[];
  assetCount: number;
  emotionalIntensity: number;
  beatType: string;
  storyPosition: number;
  thumbnail?: string;
  metadata: {
    location: string;
    timeOfDay: string;
    weather?: string;
    mood: string;
  };
}

export interface StoryBeat {
  id: string;
  name: string;
  type: string;
  position: number;
  description: string;
  emotionalGoal: string;
  keywords: string[];
  scenes: string[];
}

export interface CharacterArcData {
  id: string;
  name: string;
  color: string;
  points: Array<{
    position: number;
    emotionalArc: number;
    sceneId: string;
    description: string;
  }>;
  arcType: 'positive' | 'negative' | 'flat' | 'complex';
  consistencyScore: number;
  developmentScore: number;
}

export interface DigitalAssetUsage {
  assetId: string;
  assetType: 'character' | 'prop' | 'wardrobe' | 'location' | 'style' | 'audio';
  usageCount: number;
  scenes: string[];
  consistency: number;
  recommendations: string[];
}

export interface NarrativeAnalytics {
  structureCompliance: number;
  characterConsistency: number;
  pacingScore: number;
  emotionalArc: number[];
  assetUtilization: Record<string, number>;
  qualityMetrics: {
    narrativeCoherence: number;
    characterDevelopment: number;
    pacingBalance: number;
    visualConsistency: number;
  };
  recommendations: {
    structure: string[];
    pacing: string[];
    character: string[];
    assets: string[];
  };
}

export interface StoryStructureValidation {
  isValid: boolean;
  framework: string;
  acts: Array<{
    name: string;
    type: string;
    startPosition: number;
    endPosition: number;
    scenes: string[];
    completeness: number;
  }>;
  plotPoints: Array<{
    name: string;
    expectedPosition: number;
    actualPosition: number;
    status: 'present' | 'missing' | 'misplaced';
    sceneId?: string;
  }>;
  gaps: string[];
  warnings: string[];
  suggestions: string[];
}

export interface SceneGridItem {
  id: string;
  title: string;
  beat: string;
  characters: string[];
  location: string;
  duration: number;
  emotionalIntensity: number;
  assetCount: number;
  thumbnail?: string;
  status: 'planned' | 'generated' | 'approved' | 'needs_revision';
}

export interface AssetFlowNode {
  id: string;
  type: string;
  name: string;
  connections: Array<{
    toScene: string;
    usageType: 'primary' | 'secondary' | 'background';
    frequency: number;
  }>;
  dependencies: string[];
  consistency: number;
}

export interface CollaborativeAnnotation {
  id: string;
  sceneId: string;
  userId: string;
  userName: string;
  content: string;
  type: 'note' | 'suggestion' | 'question' | 'approval';
  position: { x: number; y: number };
  timestamp: string;
  replies: Array<{
    id: string;
    userId: string;
    content: string;
    timestamp: string;
  }>;
}

export interface StoryVisualizationConfig {
  viewType: 'timeline' | 'grid' | 'character' | 'asset' | 'analytics';
  filters: {
    characters?: string[];
    beats?: string[];
    locations?: string[];
    intensityRange?: [number, number];
    durationRange?: [number, number];
    status?: string[];
  };
  sortBy: 'position' | 'duration' | 'intensity' | 'alphabetical' | 'status';
  sortOrder: 'asc' | 'desc';
  groupBy?: 'act' | 'character' | 'location' | 'beat';
  showGrid: boolean;
  showCharacterArcs: boolean;
  showBeats: boolean;
  showAssetUsage: boolean;
}

export interface TimelineExportOptions {
  format: 'pdf' | 'png' | 'json';
  include: {
    timeline: boolean;
    characterArcs: boolean;
    beats: boolean;
    analytics: boolean;
    annotations: boolean;
  };
  style: {
    theme: 'light' | 'dark' | 'auto';
    compact: boolean;
    showThumbnails: boolean;
  };
}

export interface RealTimeCollaborationEvent {
  type: 'annotation_added' | 'annotation_updated' | 'scene_updated' | 'beat_moved' | 'character_arc_updated';
  projectId: string;
  data: any;
  userId: string;
  timestamp: string;
}