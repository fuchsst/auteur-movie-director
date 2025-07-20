/**
 * Scene Breakdown Types
 * =====================
 * TypeScript interfaces for scene-by-scene breakdown visualization
 */

export interface SceneAsset {
  asset_id: string;
  asset_type: string;
  asset_name: string;
  thumbnail_url?: string;
  properties: Record<string, any>;
  quantity: number;
}

export interface SceneCharacter {
  character_id: string;
  character_name: string;
  role_in_scene: string;
  dialogue_lines: number;
  screen_time: number;
  emotions: string[];
  objectives: string[];
}

export interface StoryBeat {
  beat_id: string;
  beat_type: string;
  description: string;
  timestamp?: number;
  duration?: number;
  importance: number;
  connects_to: string[];
}

export interface SceneSummary {
  scene_id: string;
  title: string;
  scene_number: number;
  act_number: number;
  chapter_number?: number;
  duration_minutes: number;
  status: 'draft' | 'in_progress' | 'complete' | 'review' | 'approved';
  completion_percentage: number;
  character_count: number;
  asset_count: number;
  story_beat_count: number;
  thumbnail_url?: string;
  color_indicator: string;
  synopsis?: string;
}

export interface SceneBreakdown {
  scene_id: string;
  project_id: string;
  act_number: number;
  chapter_number?: number;
  scene_number: number;
  title: string;
  description: string;
  scene_type: string;
  location: string;
  time_of_day: string;
  duration_minutes: number;
  slug_line: string;
  synopsis: string;
  script_notes?: string;
  status: 'draft' | 'in_progress' | 'complete' | 'review' | 'approved';
  completion_percentage: number;
  characters: SceneCharacter[];
  assets: SceneAsset[];
  story_beats: StoryBeat[];
  story_circle_position?: number;
  conflict_level: number;
  stakes_level: number;
  color_palette: string[];
  mood_tags: string[];
  camera_angles: string[];
  canvas_position?: { x: number; y: number };
  connections: string[];
  created_at: string;
  updated_at: string;
  version: number;
}

export interface SceneReorderRequest {
  scene_id: string;
  new_position: number;
  target_act?: number;
  target_chapter?: number;
}

export interface SceneBulkUpdate {
  scene_ids: string[];
  updates: Record<string, any>;
}

export interface SceneAnalysis {
  scene_id: string;
  pacing_score: number;
  character_balance: Record<string, number>;
  story_progression: number;
  missing_elements: string[];
  suggestions: string[];
}

export interface CanvasData {
  scenes: SceneSummary[];
  act_chapters: Record<string, SceneSummary[]>;
  total_scenes: number;
  total_duration: number;
  completion_stats: {
    draft: number;
    in_progress: number;
    complete: number;
  };
}

export interface StoryCircleMapping {
  positions: Record<number, SceneSummary[]>;
  mapping: Record<number, string>;
}