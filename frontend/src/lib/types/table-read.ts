/**
 * Digital Table Read TypeScript Types
 * STORY-088 Implementation
 */

export enum StoryCircleBeat {
  YOU = 'you',
  NEED = 'need',
  GO = 'go',
  SEARCH = 'search',
  FIND = 'find',
  TAKE = 'take',
  RETURN = 'return',
  CHANGE = 'change'
}

export enum CharacterArchetype {
  HERO = 'hero',
  MENTOR = 'mentor',
  ALLY = 'ally',
  SHADOW = 'shadow',
  THRESHOLD_GUARDIAN = 'threshold_guardian',
  TRICKSTER = 'trickster',
  HERALD = 'herald',
  SHAPESHIFTER = 'shapeshifter'
}

export enum SceneType {
  SETUP = 'setup',
  CONFRONTATION = 'confrontation',
  RESOLUTION = 'resolution',
  CHARACTER = 'character',
  EXPOSITION = 'exposition',
  TRANSITION = 'transition',
  CLIMAX = 'climax',
  DENOUEMENT = 'denouement'
}

export enum EmotionalTone {
  JOY = 'joy',
  SADNESS = 'sadness',
  ANGER = 'anger',
  FEAR = 'fear',
  SURPRISE = 'surprise',
  DISGUST = 'disgust',
  TRUST = 'trust',
  ANTICIPATION = 'anticipation',
  LOVE = 'love',
  HOPE = 'hope',
  DESPAIR = 'despair',
  CURIOSITY = 'curiosity'
}

export enum ConflictLevel {
  NONE = 'none',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  EXTREME = 'extreme'
}

export interface CharacterAnalysis {
  character_name: string;
  archetype: CharacterArchetype;
  primary_motivation: string;
  internal_conflict: string;
  external_conflict: string;
  character_arc: string;
  story_circle_position: StoryCircleBeat;
  emotional_journey: EmotionalTone[];
  relationships: Record<string, string>;
  dialogue_patterns: string[];
  key_moments: string[];
  transformation_summary: string;
}

export interface SceneAnalysis {
  scene_id: string;
  scene_number: string;
  scene_heading: string;
  synopsis: string;
  story_circle_beat: StoryCircleBeat;
  scene_type: SceneType;
  primary_emotion: EmotionalTone;
  conflict_level: ConflictLevel;
  character_development: Record<string, string>;
  thematic_elements: string[];
  visual_descriptions: string[];
  dialogue_highlights: string[];
  pacing_analysis: string;
  dramatic_function: string;
  foreshadowing: string[];
  callbacks: string[];
  character_arcs: Record<string, string>;
  emotional_arc: EmotionalTone[];
  stakes: string;
  tension_level: number;
}

export interface StoryCircleAnalysis {
  beats: Record<StoryCircleBeat, SceneAnalysis[]>;
  character_journeys: Record<string, StoryCircleBeat[]>;
  overall_arc: string;
  thematic_throughline: string;
  character_transformations: Record<string, string>;
  pacing_analysis: string;
  emotional_progression: EmotionalTone[];
  structural_strengths: string[];
  structural_weaknesses: string[];
  improvement_suggestions: string[];
}

export interface DialogueAnalysis {
  character_id: string;
  character_name: string;
  speech_patterns: string[];
  vocabulary_level: string;
  sentence_structure: string;
  emotional_indicators: string[];
  subtext_analysis: string;
  voice_consistency: number;
  unique_phrases: string[];
  dialogue_functions: string[];
  relationship_indicators: Record<string, string>;
}

export interface ThemeAnalysis {
  primary_themes: string[];
  secondary_themes: string[];
  motifs: string[];
  symbols: string[];
  thematic_questions: string[];
  moral_dilemmas: string[];
  philosophical_exploration: string;
  cultural_commentary: string;
  universal_themes: string[];
}

export interface TableReadRequest {
  project_id: string;
  script_content: string;
  scene_breakdown?: any;
  analysis_depth: 'basic' | 'comprehensive' | 'deep';
  focus_areas: string[];
  character_voices?: Record<string, any>;
  include_audio: boolean;
  generate_bible: boolean;
}

export interface TableReadSession {
  session_id: string;
  project_id: string;
  bible_id: string;
  status: 'processing' | 'completed' | 'error';
  progress: number;
  current_analysis?: string;
  results?: CreativeBible;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface CreativeBible {
  bible_id: string;
  project_id: string;
  title: string;
  logline: string;
  synopsis: string;
  character_bios: Record<string, CharacterAnalysis>;
  scene_analyses: SceneAnalysis[];
  story_circle: StoryCircleAnalysis;
  themes: ThemeAnalysis;
  dialogue_analysis: DialogueAnalysis[];
  visual_style: string;
  tone_description: string;
  genre_analysis: string;
  target_audience: string;
  comparable_works: string[];
  production_notes: string;
  character_relationships: Record<string, string[]>;
  emotional_heatmap: Record<string, EmotionalTone[]>;
  structural_timeline: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface AudioGenerationRequest {
  session_id: string;
  character_voices: Record<string, any>;
  background_music?: string;
  sound_effects?: string[];
  pacing: 'slow' | 'natural' | 'fast';
  emotion_intensity: number;
}

export interface AudioGenerationResult {
  result_id: string;
  session_id: string;
  audio_files: string[];
  total_duration: number;
  character_voices_used: Record<string, string>;
  metadata: any;
  created_at: string;
}

export interface TableReadExportRequest {
  session_id: string;
  format: 'pdf' | 'json' | 'markdown' | 'docx';
  include_audio: boolean;
  sections: string[];
}

export interface TableReadExportResult {
  export_id: string;
  session_id: string;
  format: string;
  file_path: string;
  file_size: number;
  sections_included: string[];
  created_at: string;
}

// API Response Types
export interface TableReadAPIResponse<T> {
  data: T;
  message: string;
  timestamp: string;
}

export interface SessionListResponse {
  sessions: TableReadSession[];
  total: number;
}

export interface BibleSummary {
  bible_id: string;
  title: string;
  logline: string;
  synopsis: string;
  total_characters: number;
  total_scenes: number;
  created_at: string;
  updated_at: string;
}

// Frontend-specific types
export interface TableReadStoreState {
  sessions: Record<string, TableReadSession>;
  bibles: Record<string, CreativeBible>;
  current_session: TableReadSession | null;
  loading: boolean;
  error: string | null;
}

export interface TableReadFormData {
  script_content: string;
  analysis_depth: 'basic' | 'comprehensive' | 'deep';
  focus_areas: string[];
  include_audio: boolean;
  generate_bible: boolean;
}

export interface CharacterVoiceConfig {
  character_name: string;
  voice_type: 'male' | 'female' | 'neutral';
  accent?: string;
  age_range?: string;
  emotion_style?: string;
  speech_pattern?: string;
}

export interface StoryCircleVisualization {
  beat: StoryCircleBeat;
  scenes: SceneAnalysis[];
  character_progressions: Record<string, number>;
  emotional_intensity: number;
  conflict_level: number;
}

export interface TableReadFilters {
  project_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
}

export interface AnalysisProgress {
  session_id: string;
  stage: string;
  progress: number;
  estimated_time_remaining?: number;
}