# Types Directory

This directory contains TypeScript type definitions and interfaces for the Auteur Movie Director frontend.

## Type Files

### `index.ts`

Main type definitions and re-exports.

- `Task` - Task management types
- `Notification` - Notification system types
- `ViewTab` - Tab system types
- `ViewState` - View state management
- Re-exports all other type modules

### `nodes.ts`

Node-based canvas type definitions for the Production Canvas.

- `AuteurNode` - Custom node type extending base Node
- `AuteurEdge` - Custom edge type
- `NodeType` - Enumeration of node types (including AUDIO, EFFECT, COMPOSITE)
- `AuteurNodeData` - Base node data structure
- `NodeStatus` - Node execution states (IDLE, READY, EXECUTING, COMPLETE, ERROR)
- `DataType` - Connection data types
- `CharacterReference` - Character data flow interface
- `CharacterNodeData` - Character-specific node data
- `CHARACTER_NODE_DEFINITION` - Character node registry definition
- `CHARACTER_SOCKET_COLOR` - Character connection color constant

#### Advanced Node Types (Sprint 6)
- `AudioNodeData` - Audio node specific data (source, volume, waveform, etc.)
- `EffectNodeData` - Effect node specific data (effect type, intensity, parameters)
- `CompositeNodeData` - Composite node specific data (layers, blend modes)
- `CompositeLayer` - Layer structure for composite nodes
- `BlendMode` - Enumeration of blend modes

### `project.ts`

Project-related type definitions.

- `Project` - Main project interface
- `ProjectMetadata` - Project metadata
- `AssetCategory` - Asset categorization
- `AssetType` - Asset type enumeration
- `NarrativeStructure` - Story structure types
- `CharacterAssetReference` - Minimal character reference interface

### `properties.ts`

Properties inspector type definitions.

- `PropertyDefinition` - Property structure
- `PropertyType` - Property input types
- `PropertyGroup` - Property grouping
- `SelectionContext` - Selection state
- `PropertyValidator` - Validation functions

### `websocket.ts`

WebSocket communication types.

- `WebSocketMessage` - Base message structure
- `MessageType` - Message type enumeration
- `TaskProgressPayload` - Task progress updates
- `NodeExecutionPayload` - Node execution events
- `FileEventPayload` - File system events
- `GitEventPayload` - Git status events
- `WebSocketState` - Connection state

## Type Guidelines

### Interface Naming

- Use `I` prefix sparingly, only when needed to distinguish from classes
- Prefer descriptive names: `Project` over `IProject`

### Type vs Interface

- Use `interface` for object shapes that might be extended
- Use `type` for unions, primitives, and utility types

### Enums

- Use `enum` for fixed sets of named constants
- Consider const assertions for simple string literals

### Generic Types

- Use meaningful type parameter names: `TData` over `T`
- Document generic constraints clearly

### Import/Export

- Group related types in the same file
- Re-export commonly used types from `index.ts`
- Use type-only imports when possible: `import type`

## Character Node Types (Future Implementation)

Character node type definitions have been created in preparation for the Production Canvas (PRD-002). These are **type definitions only** - no implementation exists yet.

### Key Types

- **CharacterReference** - Interface for character data flowing through node connections
  - `assetId`: Unique character identifier
  - `name`: Display name
  - `triggerWord?`: Optional prompt trigger
  - `loraPath?`: Optional LoRA model path

- **CharacterNodeData** - Character-specific node data extending `AuteurNodeData`
  - `selectedCharacterId?`: Currently selected character

- **CHARACTER_NODE_DEFINITION** - Node registry definition for future implementation
  - Type: 'character_asset'
  - Category: 'assets'
  - No inputs (selection via properties)
  - Outputs: character reference, LoRA path, trigger word

- **CharacterAssetReference** - Minimal reference type in project.ts

### Future Data Flow

When implemented, character nodes will enable:

- Character selection from project assets
- LoRA path provision to image generation
- Trigger word supply for prompt building
- Multi-character scene composition

All character node types are marked as not implemented, awaiting PRD-002 Production Canvas development.
