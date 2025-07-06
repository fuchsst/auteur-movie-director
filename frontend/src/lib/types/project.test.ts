import { describe, it, expect } from 'vitest';
import type { CharacterAssetReference } from './project';

describe('Character Asset Reference Type', () => {
  it('should define CharacterAssetReference interface correctly', () => {
    const charRef: CharacterAssetReference = {
      assetId: 'char-asset-001'
    };

    expect(charRef.assetId).toBe('char-asset-001');
  });

  it('should allow type assignment', () => {
    const mockReference: CharacterAssetReference = {
      assetId: 'test-character-123'
    };

    // Type checking - this would fail at compile time if types were wrong
    const id: string = mockReference.assetId;
    expect(id).toBe('test-character-123');
  });

  it('should be minimal as specified in comments', () => {
    const ref: CharacterAssetReference = {
      assetId: 'minimal-ref'
    };

    // Should only have assetId property
    expect(Object.keys(ref)).toHaveLength(1);
    expect(Object.keys(ref)[0]).toBe('assetId');
  });
});