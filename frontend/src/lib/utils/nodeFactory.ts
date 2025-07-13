/**
 * Node factory for creating Production Canvas nodes
 */

import type { AuteurNode, AuteurNodeData, NodeType as NodeTypeEnum } from '$lib/types/nodes';
import { NodeStatus } from '$lib/types/nodes';
import { nodeDefinitions } from '$lib/components/canvas/nodes';

export interface CreateNodeOptions {
  type: NodeTypeEnum;
  position: { x: number; y: number };
  data?: Partial<AuteurNodeData>;
}

/**
 * Creates a new node with default values
 */
export function createNode(options: CreateNodeOptions): AuteurNode {
  const { type, position, data = {} } = options;

  // Find the node definition
  const definition = nodeDefinitions.find((def) => def.type === type);
  if (!definition) {
    throw new Error(`Unknown node type: ${type}`);
  }

  // Generate unique ID
  const id = `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Merge default data with provided data
  const nodeData: AuteurNodeData = {
    ...definition.defaultData,
    ...data,
    status: NodeStatus.IDLE,
    inputs: [],
    outputs: [],
    parameters: {
      ...definition.defaultData.parameters,
      ...data.parameters
    }
  };

  return {
    id,
    type,
    position,
    data: nodeData
  };
}

/**
 * Updates node status
 */
export function updateNodeStatus(
  node: AuteurNode,
  status: NodeStatus,
  progress?: number,
  error?: string
): AuteurNode {
  return {
    ...node,
    data: {
      ...node.data,
      status,
      progress,
      error
    }
  };
}

/**
 * Updates node parameters
 */
export function updateNodeParameter(node: AuteurNode, parameter: string, value: any): AuteurNode {
  // Handle nested parameters (e.g., 'parameters.brightness')
  const keys = parameter.split('.');

  if (keys.length === 1) {
    // Top-level parameter
    return {
      ...node,
      data: {
        ...node.data,
        [parameter]: value
      }
    };
  } else if (keys[0] === 'parameters') {
    // Nested in parameters object
    return {
      ...node,
      data: {
        ...node.data,
        parameters: {
          ...node.data.parameters,
          [keys[1]]: value
        }
      }
    };
  } else {
    // Other nested parameters
    const newData = { ...node.data };
    let current: any = newData;

    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in current)) {
        current[keys[i]] = {};
      }
      current = current[keys[i]];
    }

    current[keys[keys.length - 1]] = value;

    return {
      ...node,
      data: newData
    };
  }
}

/**
 * Validates if a node is ready to execute
 */
export function isNodeReady(node: AuteurNode): boolean {
  // Check if all required inputs are connected
  const requiredInputs = node.data.inputs.filter((input) => input.required);
  const allConnected = requiredInputs.every((input) => input.connected);

  // Check node-specific readiness
  switch (node.type) {
    case 'audio':
      const audioData = node.data as any;
      if (audioData.audioSource === 'generate' && !audioData.text) {
        return false;
      }
      break;

    case 'composite':
      const compositeData = node.data as any;
      if (compositeData.layers.length === 0) {
        return false;
      }
      break;
  }

  return allConnected;
}

/**
 * Gets node execution parameters for the Function Runner
 */
export function getNodeExecutionParams(node: AuteurNode): Record<string, any> {
  const params: Record<string, any> = {
    nodeId: node.id,
    nodeType: node.type,
    ...node.data.parameters
  };

  // Add node-specific parameters
  switch (node.type) {
    case 'audio':
      params.audioSource = node.data.audioSource;
      params.text = node.data.text;
      params.voiceId = node.data.voiceId;
      params.volume = node.data.volume;
      break;

    case 'effect':
      params.effectType = node.data.effectType;
      params.intensity = node.data.intensity;
      break;

    case 'composite':
      params.layers = node.data.layers;
      params.blendMode = node.data.blendMode;
      params.outputFormat = node.data.outputFormat;
      break;
  }

  return params;
}
