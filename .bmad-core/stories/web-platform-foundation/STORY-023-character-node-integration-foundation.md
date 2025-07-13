# STORY-023: Character-Node Integration Foundation (Type Definitions Only)

**Story ID**: STORY-023  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 1 (Small)  
**Priority**: Low  
**Status**: ✅ Completed (January 2025)

## Story
As a developer, I need to create TypeScript type definitions and interfaces that will prepare for future Character Asset Nodes in the Production Canvas (PRD-002). This story only creates type scaffolding - actual node implementation will be done when the canvas is built.

## Important Note
This is a **foundation story only**. We are creating TypeScript types to support future features, but NOT implementing:
- Actual Character Asset Node component
- Node rendering or execution
- Canvas integration
- Node-to-sheet communication
- Any visual components

The actual node implementation will be done in PRD-002 (Production Canvas).

## Acceptance Criteria
- [ ] TypeScript interfaces for future Character Asset Node
- [ ] Type definitions added to existing node types file
- [ ] Socket types defined for character data flow
- [ ] Documentation of intended data flow patterns
- [ ] No actual implementation - types only

## Technical Details

### Add Character Node Types to Existing Types File

```typescript
// frontend/src/lib/types/nodes.ts - ADD these types

// Character-specific socket types (for future use)
export interface CharacterReference {
  assetId: string;
  name: string;
  triggerWord?: string;
  loraPath?: string;
}

export interface CharacterNodeData {
  selectedCharacterId?: string;
  // Future: variation selection, expression, etc.
}

// Node type definition (for future node registry)
export const CHARACTER_NODE_DEFINITION = {
  type: 'character_asset',
  category: 'assets',
  label: 'Character',
  description: 'Reference a character asset (Future)',
  inputs: [],  // No inputs - selection via properties
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
export const CHARACTER_SOCKET_COLOR = '#fbbf24';  // Amber
```

### Documentation of Future Data Flow

```typescript
// frontend/src/lib/types/nodes.ts - ADD documentation

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
```

### Update Project Types

```typescript
// frontend/src/lib/types/project.ts - ADD character reference type

export interface CharacterAssetReference {
  assetId: string;
  // Minimal reference for type safety
  // Full implementation in PRD-004
}
```

## What This Story Does NOT Include

1. **Character Node Component** - Will be created in PRD-002
2. **Node Rendering Logic** - Part of Production Canvas (PRD-002)
3. **Canvas Integration** - Requires canvas to exist first
4. **Visual Node Design** - Future UI work
5. **Node Execution Logic** - Part of Function Runner (PRD-003)
6. **Character Sheet Integration** - Part of PRD-004

## Dependencies
- STORY-007: SvelteKit Setup (for TypeScript types location)
- STORY-023: Character Asset Data Model (for data structure)

## Notes
This story only adds TypeScript type definitions to prepare for future character node implementation. When PRD-002 (Production Canvas) is implemented, these types will be used to create actual Character Asset Nodes. The types are added to existing files to avoid creating unused code.

## Implementation Status (January 2025)

### ✅ Completed Components (100% Complete)

All required type definitions have been implemented in the codebase:

1. **In `frontend/src/lib/types/nodes.ts`**:
   - ✅ `CharacterReference` interface with all fields (assetId, name, triggerWord, loraPath)
   - ✅ `CharacterNodeData` interface with selectedCharacterId
   - ✅ `CHARACTER_NODE_DEFINITION` constant with full node specification
   - ✅ `CHARACTER_SOCKET_COLOR` constant set to amber (#fbbf24)
   - ✅ Comprehensive documentation comment explaining future data flow

2. **In `frontend/src/lib/types/project.ts`**:
   - ✅ `CharacterAssetReference` interface for minimal references
   - ✅ Additional `CharacterAsset` interface from STORY-022 integration

3. **Additional Implementation**:
   - ✅ `NodeType.CHARACTER` enum value added
   - ✅ `CharacterNodeProps` interface extending NodeProps
   - ✅ Proper integration with xyflow/svelte type system
   - ✅ Node marked as `implemented: false` as specified

### Summary
This foundation story is fully complete. All TypeScript type definitions have been properly added to existing type files, preparing the codebase for future Character Asset Node implementation in PRD-002. The implementation correctly provides only type definitions without any actual node components, exactly as specified in the story requirements.