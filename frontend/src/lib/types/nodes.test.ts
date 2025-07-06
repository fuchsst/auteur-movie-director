import { describe, it, expect } from 'vitest';
import type { CharacterReference, CharacterNodeData, AuteurNodeData, DataType } from './nodes';
import { CHARACTER_NODE_DEFINITION, CHARACTER_SOCKET_COLOR, NodeStatus } from './nodes';

describe('Character Node Type Definitions', () => {
  it('should define CharacterReference interface correctly', () => {
    const mockCharRef: CharacterReference = {
      assetId: 'char-001',
      name: 'Main Character',
      triggerWord: 'mainchar',
      loraPath: '/path/to/lora.safetensors'
    };

    expect(mockCharRef.assetId).toBe('char-001');
    expect(mockCharRef.name).toBe('Main Character');
    expect(mockCharRef.triggerWord).toBe('mainchar');
    expect(mockCharRef.loraPath).toBe('/path/to/lora.safetensors');
  });

  it('should define CHARACTER_NODE_DEFINITION correctly', () => {
    expect(CHARACTER_NODE_DEFINITION.type).toBe('character_asset');
    expect(CHARACTER_NODE_DEFINITION.category).toBe('assets');
    expect(CHARACTER_NODE_DEFINITION.label).toBe('Character');
    expect(CHARACTER_NODE_DEFINITION.description).toContain('Future');
    expect(CHARACTER_NODE_DEFINITION.inputs).toHaveLength(0);
    expect(CHARACTER_NODE_DEFINITION.outputs).toHaveLength(3);
    expect(CHARACTER_NODE_DEFINITION.implemented).toBe(false);

    // Check outputs
    const outputs = CHARACTER_NODE_DEFINITION.outputs;
    expect(outputs[0].id).toBe('character');
    expect(outputs[0].type).toBe('character_reference');
    expect(outputs[1].id).toBe('lora');
    expect(outputs[1].type).toBe('string');
    expect(outputs[2].id).toBe('trigger');
    expect(outputs[2].type).toBe('string');
  });

  it('should define CHARACTER_SOCKET_COLOR', () => {
    expect(CHARACTER_SOCKET_COLOR).toBe('#fbbf24');
  });

  it('should allow CharacterNodeData to extend AuteurNodeData', () => {
    const mockNodeData: CharacterNodeData = {
      label: 'Character Node',
      status: NodeStatus.IDLE,
      inputs: [],
      outputs: [],
      parameters: {},
      selectedCharacterId: 'char-001'
    };

    expect(mockNodeData.selectedCharacterId).toBe('char-001');
    expect(mockNodeData.label).toBe('Character Node');
    expect(mockNodeData.status).toBe(NodeStatus.IDLE);
  });

  it('should support optional fields in CharacterReference', () => {
    const minimalCharRef: CharacterReference = {
      assetId: 'char-002',
      name: 'Secondary Character'
      // triggerWord and loraPath are optional
    };

    expect(minimalCharRef.assetId).toBe('char-002');
    expect(minimalCharRef.name).toBe('Secondary Character');
    expect(minimalCharRef.triggerWord).toBeUndefined();
    expect(minimalCharRef.loraPath).toBeUndefined();
  });
});
