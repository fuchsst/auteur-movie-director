/**
 * Node component registry for the Production Canvas
 */

import type { ComponentType } from 'svelte';
import type { NodeProps } from '@xyflow/svelte';
import { NodeType } from '$lib/types/nodes';

// Import node components
import AudioNode from './AudioNode.svelte';
import EffectNode from './EffectNode.svelte';
import CompositeNode from './CompositeNode.svelte';

// Node type to component mapping
export const nodeTypes: Record<string, ComponentType<NodeProps>> = {
  [NodeType.AUDIO]: AudioNode as ComponentType<NodeProps>,
  [NodeType.EFFECT]: EffectNode as ComponentType<NodeProps>,
  [NodeType.COMPOSITE]: CompositeNode as ComponentType<NodeProps>,
  // Add other node types as they are implemented
};

// Node definitions for the node creation menu
export const nodeDefinitions = [
  {
    type: NodeType.AUDIO,
    label: 'Audio Node',
    category: 'Media',
    description: 'Generate or process audio',
    icon: '🎵',
    defaultData: {
      label: 'Audio',
      audioSource: 'file',
      volume: 1,
      parameters: {}
    }
  },
  {
    type: NodeType.EFFECT,
    label: 'Effect Node',
    category: 'Processing',
    description: 'Apply visual effects',
    icon: '🎨',
    defaultData: {
      label: 'Effect',
      effectType: 'color',
      intensity: 100,
      parameters: {
        brightness: 0,
        contrast: 0,
        saturation: 0,
        hue: 0
      }
    }
  },
  {
    type: NodeType.COMPOSITE,
    label: 'Composite Node',
    category: 'Processing',
    description: 'Combine multiple layers',
    icon: '🎬',
    defaultData: {
      label: 'Composite',
      layers: [],
      blendMode: 'normal',
      outputFormat: 'image',
      parameters: {}
    }
  }
];

// Connection validation rules
export const connectionRules = {
  // Audio connections
  [NodeType.AUDIO]: {
    inputs: ['audio', 'text'],
    outputs: ['audio']
  },
  // Effect connections
  [NodeType.EFFECT]: {
    inputs: ['image', 'video'],
    outputs: ['image', 'video']
  },
  // Composite connections
  [NodeType.COMPOSITE]: {
    inputs: ['image', 'video', 'layer'],
    outputs: ['image', 'video']
  }
};

// Helper function to validate connections
export function isValidConnection(
  sourceType: NodeType,
  targetType: NodeType,
  sourceHandle: string,
  targetHandle: string
): boolean {
  const sourceRules = connectionRules[sourceType];
  const targetRules = connectionRules[targetType];

  if (!sourceRules || !targetRules) {
    return false;
  }

  // Check if source can output to target input type
  // This is simplified - in a real implementation, you'd check handle data types
  return true;
}

// Node categories for grouping in the creation menu
export const nodeCategories = [
  { id: 'input', label: 'Input', icon: '📥' },
  { id: 'media', label: 'Media', icon: '🎬' },
  { id: 'processing', label: 'Processing', icon: '⚙️' },
  { id: 'output', label: 'Output', icon: '📤' }
];

export { AudioNode, EffectNode, CompositeNode };