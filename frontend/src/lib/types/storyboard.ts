/**
 * Storyboard/Pre-vis TypeScript Types
 * STORY-087 Implementation
 */

export enum StoryboardFrameStatus {
    CONCEPT = 'concept',
    SKETCH = 'sketch',
    DRAFT = 'draft',
    FINALIZED = 'finalized',
    APPROVED = 'approved',
    GENERATED = 'generated'
}

export enum CameraMovement {
    STATIC = 'static',
    PAN = 'pan',
    TILT = 'tilt',
    TRACK = 'track',
    DOLLY = 'dolly',
    CRANE = 'crane',
    ZOOM = 'zoom',
    HANDHELD = 'handheld',
    STEADICAM = 'steadicam',
    DRONE = 'drone'
}

export enum ShotComposition {
    WIDE = 'wide',
    MEDIUM = 'medium',
    CLOSEUP = 'closeup',
    EXTREME_CLOSEUP = 'extreme_closeup',
    TWO_SHOT = 'two_shot',
    OVER_SHOULDER = 'over_shoulder',
    POV = 'pov',
    ESTABLISHING = 'establishing',
    INSERT = 'insert'
}

export interface StoryboardFrame {
    frame_id: string;
    scene_id: string;
    shot_number: number;
    frame_number: number;
    description: string;
    visual_notes?: string;
    camera_angle: string;
    camera_movement: CameraMovement;
    composition: ShotComposition;
    focal_length: number;
    position: Record<string, number>;
    status: StoryboardFrameStatus;
    previs_path?: string;
    thumbnail_path?: string;
    generation_params: Record<string, any>;
    model_version: string;
    created_at: string;
    updated_at: string;
    created_by?: string;
}

export interface StoryboardShot {
    shot_id: string;
    scene_id: string;
    shot_number: number;
    shot_type: string;
    duration: number;
    camera_setup: Record<string, any>;
    lighting_setup: Record<string, any>;
    audio_notes: string;
    frames: StoryboardFrame[];
    previs_sequence: Record<string, any>;
    linked_elements: string[];
    created_at: string;
    updated_at: string;
}

export interface StoryboardSequence {
    sequence_id: string;
    scene_id: string;
    sequence_name: string;
    description: string;
    shots: StoryboardShot[];
    scene_breakdown?: any;
    previs_sequence_path?: string;
    total_duration: number;
    aspect_ratio: string;
    resolution: string;
    frame_rate: number;
    created_at: string;
    updated_at: string;
    created_by?: string;
}

export interface PrevisGenerationRequest {
    sequence_id: string;
    scene_id: string;
    style: string;
    quality: string;
    resolution: string;
    frame_rate: number;
    camera_preset: string;
    lighting_preset: string;
    include_assets: boolean;
    asset_overrides: Record<string, any>;
    batch_size: number;
    priority: number;
}

export interface PrevisGenerationResult {
    result_id: string;
    sequence_id: string;
    status: string;
    progress: number;
    sequence_path?: string;
    frame_paths: string[];
    thumbnail_paths: string[];
    metadata: Record<string, any>;
    error_message?: string;
    started_at: string;
    completed_at?: string;
}

export interface StoryboardTemplate {
    template_id: string;
    template_name: string;
    template_description: string;
    default_frames_per_shot: number;
    default_shot_duration: number;
    camera_presets: Record<string, Record<string, any>>;
    composition_templates: Record<string, Record<string, any>>;
    visual_style: string;
    color_palette: string[];
    created_at: string;
    updated_at: string;
}

export interface StoryboardCreateRequest {
    project_id: string;
    scene_id: string;
    template_id?: string;
}

export interface FrameUpdateData {
    description?: string;
    camera_angle?: string;
    camera_movement?: CameraMovement;
    composition?: ShotComposition;
    focal_length?: number;
    visual_notes?: string;
    status?: StoryboardFrameStatus;
}

export interface ShotUpdateData {
    shot_type?: string;
    duration?: number;
    camera_setup?: Record<string, any>;
    lighting_setup?: Record<string, any>;
    audio_notes?: string;
}

// API Response Types
export interface StoryboardAPIResponse<T> {
    data: T;
    message: string;
    timestamp: string;
}

export interface SequenceListResponse {
    sequences: StoryboardSequence[];
    total: number;
}

export interface ExportResponse {
    format: string;
    sequence: StoryboardSequence;
    metadata: {
        format: string;
        exported_at: string;
        total_shots: number;
        total_frames: number;
        total_duration: number;
        filtered: boolean;
    };
}