import { describe, it, expect } from 'vitest';
import {
  createNode,
  updateNodeStatus,
  updateNodeParameter,
  isNodeReady,
  getNodeExecutionParams
} from './nodeFactory';
import { NodeType, NodeStatus, BlendMode } from '$lib/types/nodes';
import type { AuteurNode } from '$lib/types/nodes';

describe('nodeFactory', () => {
  describe('createNode', () => {
    it('creates an audio node with default values', () => {
      const node = createNode({
        type: NodeType.AUDIO,
        position: { x: 100, y: 200 }
      });

      expect(node.type).toBe(NodeType.AUDIO);
      expect(node.position).toEqual({ x: 100, y: 200 });
      expect(node.data.label).toBe('Audio');
      expect(node.data.status).toBe(NodeStatus.IDLE);
      expect(node.data.audioSource).toBe('file');
      expect(node.data.volume).toBe(1);
    });

    it('creates an effect node with custom data', () => {
      const node = createNode({
        type: NodeType.EFFECT,
        position: { x: 300, y: 400 },
        data: {
          label: 'Custom Effect',
          effectType: 'blur',
          intensity: 50
        }
      });

      expect(node.data.label).toBe('Custom Effect');
      expect(node.data.effectType).toBe('blur');
      expect(node.data.intensity).toBe(50);
    });

    it('creates a composite node with layers', () => {
      const node = createNode({
        type: NodeType.COMPOSITE,
        position: { x: 500, y: 600 }
      });

      expect(node.type).toBe(NodeType.COMPOSITE);
      expect(node.data.layers).toEqual([]);
      expect(node.data.blendMode).toBe('normal');
      expect(node.data.outputFormat).toBe('image');
    });

    it('generates unique IDs for each node', () => {
      const node1 = createNode({
        type: NodeType.AUDIO,
        position: { x: 0, y: 0 }
      });
      const node2 = createNode({
        type: NodeType.AUDIO,
        position: { x: 0, y: 0 }
      });

      expect(node1.id).not.toBe(node2.id);
      expect(node1.id).toMatch(/^audio-\d+-[a-z0-9]+$/);
    });

    it('throws error for unknown node type', () => {
      expect(() => {
        createNode({
          type: 'unknown' as NodeType,
          position: { x: 0, y: 0 }
        });
      }).toThrow('Unknown node type: unknown');
    });
  });

  describe('updateNodeStatus', () => {
    it('updates node status', () => {
      const node = createNode({
        type: NodeType.AUDIO,
        position: { x: 0, y: 0 }
      });

      const updatedNode = updateNodeStatus(node, NodeStatus.EXECUTING, 50);

      expect(updatedNode.data.status).toBe(NodeStatus.EXECUTING);
      expect(updatedNode.data.progress).toBe(50);
    });

    it('updates node with error', () => {
      const node = createNode({
        type: NodeType.EFFECT,
        position: { x: 0, y: 0 }
      });

      const updatedNode = updateNodeStatus(
        node,
        NodeStatus.ERROR,
        undefined,
        'Processing failed'
      );

      expect(updatedNode.data.status).toBe(NodeStatus.ERROR);
      expect(updatedNode.data.error).toBe('Processing failed');
    });
  });

  describe('updateNodeParameter', () => {
    it('updates top-level parameter', () => {
      const node = createNode({
        type: NodeType.AUDIO,
        position: { x: 0, y: 0 }
      });

      const updatedNode = updateNodeParameter(node, 'audioSource', 'generate');

      expect(updatedNode.data.audioSource).toBe('generate');
    });

    it('updates nested parameter', () => {
      const node = createNode({
        type: NodeType.EFFECT,
        position: { x: 0, y: 0 }
      });

      const updatedNode = updateNodeParameter(node, 'parameters.brightness', 50);

      expect(updatedNode.data.parameters.brightness).toBe(50);
    });

    it('updates deeply nested parameter', () => {
      const node = createNode({
        type: NodeType.COMPOSITE,
        position: { x: 0, y: 0 }
      });

      const layers = [{
        id: 'layer-1',
        name: 'Layer 1',
        visible: true,
        opacity: 1,
        blendMode: BlendMode.NORMAL,
        transform: { x: 0, y: 0, scale: 1, rotation: 0 }
      }];

      const updatedNode = updateNodeParameter(node, 'layers', layers);

      expect(updatedNode.data.layers).toEqual(layers);
    });
  });

  describe('isNodeReady', () => {
    it('returns true for audio node with file source', () => {
      const node: AuteurNode = {
        id: 'audio-1',
        type: NodeType.AUDIO,
        position: { x: 0, y: 0 },
        data: {
          label: 'Audio',
          status: NodeStatus.IDLE,
          inputs: [],
          outputs: [],
          parameters: {},
          audioSource: 'file'
        }
      };

      expect(isNodeReady(node)).toBe(true);
    });

    it('returns false for audio node with generate source but no text', () => {
      const node: AuteurNode = {
        id: 'audio-1',
        type: NodeType.AUDIO,
        position: { x: 0, y: 0 },
        data: {
          label: 'Audio',
          status: NodeStatus.IDLE,
          inputs: [],
          outputs: [],
          parameters: {},
          audioSource: 'generate'
        }
      };

      expect(isNodeReady(node)).toBe(false);
    });

    it('returns true for audio node with generate source and text', () => {
      const node: AuteurNode = {
        id: 'audio-1',
        type: NodeType.AUDIO,
        position: { x: 0, y: 0 },
        data: {
          label: 'Audio',
          status: NodeStatus.IDLE,
          inputs: [],
          outputs: [],
          parameters: {},
          audioSource: 'generate',
          text: 'Hello world'
        }
      };

      expect(isNodeReady(node)).toBe(true);
    });

    it('returns false for composite node with no layers', () => {
      const node: AuteurNode = {
        id: 'composite-1',
        type: NodeType.COMPOSITE,
        position: { x: 0, y: 0 },
        data: {
          label: 'Composite',
          status: NodeStatus.IDLE,
          inputs: [],
          outputs: [],
          parameters: {},
          layers: [],
          blendMode: BlendMode.NORMAL,
          outputFormat: 'image'
        }
      };

      expect(isNodeReady(node)).toBe(false);
    });

    it('returns false when required inputs are not connected', () => {
      const node: AuteurNode = {
        id: 'effect-1',
        type: NodeType.EFFECT,
        position: { x: 0, y: 0 },
        data: {
          label: 'Effect',
          status: NodeStatus.IDLE,
          inputs: [
            { id: 'input', name: 'Input', type: 'image', required: true, connected: false }
          ],
          outputs: [],
          parameters: {}
        }
      };

      expect(isNodeReady(node)).toBe(false);
    });
  });

  describe('getNodeExecutionParams', () => {
    it('returns execution parameters for audio node', () => {
      const node: AuteurNode = {
        id: 'audio-1',
        type: NodeType.AUDIO,
        position: { x: 0, y: 0 },
        data: {
          label: 'Audio',
          status: NodeStatus.IDLE,
          inputs: [],
          outputs: [],
          parameters: { pitch: 1.2 },
          audioSource: 'generate',
          text: 'Hello',
          voiceId: 'voice-123',
          volume: 0.8
        }
      };

      const params = getNodeExecutionParams(node);

      expect(params).toEqual({
        nodeId: 'audio-1',
        nodeType: NodeType.AUDIO,
        pitch: 1.2,
        audioSource: 'generate',
        text: 'Hello',
        voiceId: 'voice-123',
        volume: 0.8
      });
    });

    it('returns execution parameters for effect node', () => {
      const node: AuteurNode = {
        id: 'effect-1',
        type: NodeType.EFFECT,
        position: { x: 0, y: 0 },
        data: {
          label: 'Effect',
          status: NodeStatus.IDLE,
          inputs: [],
          outputs: [],
          parameters: { brightness: 20, contrast: 10 },
          effectType: 'color',
          intensity: 75
        }
      };

      const params = getNodeExecutionParams(node);

      expect(params).toEqual({
        nodeId: 'effect-1',
        nodeType: NodeType.EFFECT,
        brightness: 20,
        contrast: 10,
        effectType: 'color',
        intensity: 75
      });
    });

    it('returns execution parameters for composite node', () => {
      const layers = [{
        id: 'layer-1',
        name: 'Layer 1',
        visible: true,
        opacity: 0.8,
        blendMode: BlendMode.MULTIPLY,
        transform: { x: 0, y: 0, scale: 1, rotation: 0 }
      }];

      const node: AuteurNode = {
        id: 'composite-1',
        type: NodeType.COMPOSITE,
        position: { x: 0, y: 0 },
        data: {
          label: 'Composite',
          status: NodeStatus.IDLE,
          inputs: [],
          outputs: [],
          parameters: {},
          layers,
          blendMode: BlendMode.SCREEN,
          outputFormat: 'video'
        }
      };

      const params = getNodeExecutionParams(node);

      expect(params).toEqual({
        nodeId: 'composite-1',
        nodeType: NodeType.COMPOSITE,
        layers,
        blendMode: BlendMode.SCREEN,
        outputFormat: 'video'
      });
    });
  });
});