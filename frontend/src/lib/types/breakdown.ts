/**
 * Breakdown Type Definitions
 * STORY-086: Professional Script Breakdown Interface
 * 
 * TypeScript interfaces for the breakdown system that mirrors
 * traditional production workflows.
 */

export interface BreakdownElement {
  element_id: string;
  element_type: ElementCategory;
  name: string;
  description: string;
  scene_id: string;
  script_position: {
    start: number;
    end: number;
    line: number;
  };
  context_text: string;
  asset_id?: string;
  asset_type?: string;
  status: BreakdownElementStatus;
  confidence: number;
  quantity: number;
  notes: string;
  special_instructions: string;
  estimated_cost: number;
  estimated_time: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface SceneBreakdown {
  scene_id: string;
  scene_number: string;
  scene_heading: string;
  synopsis: string;
  location: string;
  time_of_day: string;
  interior_exterior: string;
  estimated_pages: number;
  estimated_duration: number;
  elements: Record<ElementCategory, BreakdownElement[]>;
  characters: string[];
  day_night: string;
  continuity_notes: string;
  special_notes: string;
  breakdown_complete: boolean;
  validated: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScriptBreakdown {
  project_id: string;
  project_name: string;
  script_title: string;
  script_author: string;
  total_scenes: number;
  total_pages: number;
  scenes: Record<string, SceneBreakdown>;
  scene_order: string[];
  all_characters: string[];
  all_locations: string[];
  total_elements: number;
  total_estimated_cost: number;
  total_estimated_duration: number;
  element_counts: Record<ElementCategory, number>;
  is_valid: boolean;
  validation_errors: string[];
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export enum ElementCategory {
  CAST = 'cast',
  PROPS = 'props',
  WARDROBE = 'wardrobe',
  VEHICLES = 'vehicles',
  SET_DRESSING = 'set_dressing',
  SFX = 'sfx',
  SOUNDS = 'sounds',
  MUSIC = 'music',
  LOCATIONS = 'locations',
  SPECIAL_EFFECTS = 'special_effects'
}

export enum BreakdownElementStatus {
  DETECTED = 'detected',
  CONFIRMED = 'confirmed',
  LINKED = 'linked',
  CREATED = 'created',
  IGNORED = 'ignored'
}

export enum BreakdownExportFormat {
  PDF = 'pdf',
  CSV = 'csv',
  JSON = 'json',
  EXCEL = 'excel',
  FDX = 'fdx'
}

export interface BreakdownExportRequest {
  project_id: string;
  export_format: BreakdownExportFormat;
  include_scenes?: string[];
  export_options?: Record<string, any>;
  filter_categories?: ElementCategory[];
  min_confidence?: number;
  include_notes?: boolean;
  include_costs?: boolean;
  created_at?: string;
  created_by?: string;
}

export interface BreakdownTemplate {
  template_id: string;
  template_name: string;
  template_description: string;
  element_categories: ElementCategory[];
  detection_rules: Record<string, any>;
  default_values: Record<string, any>;
  required_fields: string[];
  validation_rules: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface BreakdownSummary {
  total_scenes: number;
  total_elements: number;
  total_estimated_cost: number;
  total_estimated_duration: number;
  element_counts: Record<ElementCategory, number>;
  all_characters: string[];
  all_locations: string[];
}

export interface SceneElementUpdate {
  status?: BreakdownElementStatus;
  notes?: string;
  estimated_cost?: number;
  quantity?: number;
  special_instructions?: string;
}

export interface SceneNotesUpdate {
  continuity_notes?: string;
  special_notes?: string;
}

export interface ElementSearchFilters {
  category?: ElementCategory;
  status?: BreakdownElementStatus;
  min_confidence?: number;
  max_cost?: number;
  scene_id?: string;
}

export interface BreakdownAnalytics {
  cost_by_category: Record<ElementCategory, number>;
  element_count_by_category: Record<ElementCategory, number>;
  scenes_by_location: Record<string, number>;
  characters_by_scene: Record<string, string[]>;
  budget_analysis: {
    total_estimated: number;
    highest_cost_category: ElementCategory;
    most_expensive_scene: string;
  };
}