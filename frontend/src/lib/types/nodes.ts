/**
 * Node-based canvas type definitions
 * Compatible with @xyflow/svelte
 */

import type { Node, Edge, NodeProps } from '@xyflow/svelte';

export interface AuteurNode extends Node {
  type: NodeType;
  data: AuteurNodeData;
}

export interface AuteurEdge extends Edge {
  data?: EdgeData;
}

export enum NodeType {
  // Input nodes
  CHARACTER = 'character',
  STYLE = 'style',
  LOCATION = 'location',
  PROMPT = 'prompt',
  SCRIPT = 'script',

  // Generation nodes
  IMAGE_GEN = 'image_gen',
  VIDEO_GEN = 'video_gen',
  AUDIO_GEN = 'audio_gen',

  // Processing nodes
  UPSCALE = 'upscale',
  FACE_SWAP = 'face_swap',
  VOICE_CLONE = 'voice_clone',

  // Control nodes
  CONTROL_MAP = 'control_map',
  STYLE_TRANSFER = 'style_transfer',

  // Advanced nodes (Sprint 6)
  AUDIO = 'audio',
  EFFECT = 'effect',
  COMPOSITE = 'composite',

  // Output nodes
  RENDER = 'render',
  EXPORT = 'export'
}

export interface AuteurNodeData {
  label: string;
  status: NodeStatus;
  progress?: number;
  preview?: string;
  error?: string;
  inputs: NodeInput[];
  outputs: NodeOutput[];
  parameters: Record<string, any>;
  [key: string]: unknown; // Add index signature for compatibility
}

export enum NodeStatus {
  IDLE = 'idle',
  READY = 'ready',
  EXECUTING = 'executing',
  COMPLETE = 'complete',
  ERROR = 'error'
}

export interface NodeInput {
  id: string;
  name: string;
  type: DataType;
  required: boolean;
  connected: boolean;
  value?: any;
}

export interface NodeOutput {
  id: string;
  name: string;
  type: DataType;
  value?: any;
}

export enum DataType {
  IMAGE = 'image',
  VIDEO = 'video',
  AUDIO = 'audio',
  TEXT = 'text',
  LATENT = 'latent',
  MASK = 'mask',
  CONTROL = 'control',
  MODEL = 'model',
  LORA = 'lora',
  ANY = 'any'
}

export interface EdgeData {
  dataType: DataType;
  animated?: boolean;
  [key: string]: unknown; // Add index signature for compatibility
}

// Node component props
export interface CharacterNodeProps extends NodeProps {
  data: CharacterNodeData;
}

export interface CharacterNodeData extends AuteurNodeData {
  selectedCharacterId?: string;
  // Future: variation selection, expression, etc.
}

export interface ImageGenNodeProps extends NodeProps {
  data: ImageGenNodeData;
}

export interface ImageGenNodeData extends AuteurNodeData {
  model?: string;
  steps?: number;
  cfg_scale?: number;
  width?: number;
  height?: number;
  seed?: number;
}

// Character-specific socket types (for future use)
export interface CharacterReference {
  assetId: string;
  name: string;
  triggerWord?: string;
  loraPath?: string;
}

// Node type definition (for future node registry)
export const CHARACTER_NODE_DEFINITION = {
  type: 'character_asset',
  category: 'assets',
  label: 'Character',
  description: 'Reference a character asset (Future)',
  inputs: [], // No inputs - selection via properties
  outputs: [
    {
      id: 'character',
      name: 'Character',
      type: 'character_reference' as const
    },
    {
      id: 'lora',
      name: 'LoRA Model',
      type: 'string' as const
    },
    {
      id: 'trigger',
      name: 'Trigger Word',
      type: 'string' as const
    }
  ],
  // Note: Implementation deferred to PRD-002
  implemented: false
};

// Add to socket type registry (for future use)
export const CHARACTER_SOCKET_COLOR = '#fbbf24'; // Amber

/**
 * Character Node Data Flow (Future Implementation)
 *
 * When PRD-002 is implemented, Character nodes will:
 * 1. Allow selection of character from project assets
 * 2. Output character reference for other nodes
 * 3. Provide LoRA path for image generation nodes
 * 4. Supply trigger words for prompt construction
 *
 * Example future usage:
 * - Character Node -> Prompt Builder Node -> Image Generation Node
 * - Character Node -> Style Mixer Node -> Video Generation Node
 *
 * This is currently just type definitions - no implementation.
 */

// Advanced node interfaces (Sprint 6)
export interface AudioNodeProps extends NodeProps {
  data: AudioNodeData;
}

export interface AudioNodeData extends AuteurNodeData {
  audioSource?: 'file' | 'generate' | 'record';
  audioFile?: string;
  duration?: number;
  voiceId?: string;
  text?: string;
  waveform?: Float32Array;
  volume?: number;
  startTime?: number;
}

export interface EffectNodeProps extends NodeProps {
  data: EffectNodeData;
}

export interface EffectNodeData extends AuteurNodeData {
  effectType: 'blur' | 'color' | 'filter' | 'sharpen' | 'denoise' | 'custom';
  intensity?: number;
  parameters: Record<string, any>;
  preview?: string;
}

export interface CompositeNodeProps extends NodeProps {
  data: CompositeNodeData;
}

export interface CompositeNodeData extends AuteurNodeData {
  layers: CompositeLayer[];
  blendMode: BlendMode;
  outputFormat: 'image' | 'video';
  preview?: string;
  canvasWidth?: number;
  canvasHeight?: number;
}

export interface CompositeLayer {
  id: string;
  name: string;
  source?: string;
  visible: boolean;
  opacity: number;
  blendMode: BlendMode;
  transform: {
    x: number;
    y: number;
    scale: number;
    rotation: number;
  };
  mask?: string;
}

export enum BlendMode {
  NORMAL = 'normal',
  MULTIPLY = 'multiply',
  SCREEN = 'screen',
  OVERLAY = 'overlay',
  SOFT_LIGHT = 'soft-light',
  HARD_LIGHT = 'hard-light',
  COLOR_DODGE = 'color-dodge',
  COLOR_BURN = 'color-burn',
  DARKEN = 'darken',
  LIGHTEN = 'lighten',
  DIFFERENCE = 'difference',
  EXCLUSION = 'exclusion'
}

// Canvas state
export interface CanvasState {
  nodes: AuteurNode[];
  edges: AuteurEdge[];
  selectedNodes: string[];
  selectedEdges: string[];
  executing: boolean;
  viewport: {
    x: number;
    y: number;
    zoom: number;
  };
}

// Workflow definition
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  nodes: AuteurNode[];
  edges: AuteurEdge[];
  created: string;
  modified: string;
  thumbnail?: string;
}
