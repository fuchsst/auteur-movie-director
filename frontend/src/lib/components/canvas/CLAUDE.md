# Production Canvas Components

The Production Canvas is a node-based visual workflow system for creating cinematic sequences. It allows users to build complex production pipelines by connecting various node types.

## Node Types

### Advanced Nodes (Sprint 6)

#### Audio Node (`AudioNode.svelte`)

Handles audio generation, processing, and file management.

**Features:**

- Audio source selection (file/generate/record)
- Voice synthesis with text input
- Waveform visualization
- Volume control
- Duration display

**Data Structure:**

```typescript
interface AudioNodeData {
  audioSource?: 'file' | 'generate' | 'record';
  audioFile?: string;
  duration?: number;
  voiceId?: string;
  text?: string;
  waveform?: Float32Array;
  volume?: number;
  startTime?: number;
}
```

#### Effect Node (`EffectNode.svelte`)

Applies visual effects and post-processing to images/videos.

**Features:**

- Multiple effect types (blur, color, filter, sharpen, denoise, custom)
- Effect-specific parameters
- Intensity control
- Preview display
- Custom shader support

**Effect Types:**

- **Blur**: Gaussian, motion, box blur with radius control
- **Color**: Brightness, contrast, saturation, hue adjustment
- **Filter**: Preset filters (vintage, noir, sepia, cool, warm)
- **Sharpen**: Amount and radius control
- **Denoise**: Strength and detail preservation
- **Custom**: User-defined shader code

#### Composite Node (`CompositeNode.svelte`)

Combines multiple layers into a single output.

**Features:**

- Layer management (add/remove/reorder)
- Per-layer controls:
  - Visibility toggle
  - Opacity adjustment
  - Blend mode selection
  - Transform properties
- Drag-and-drop layer reordering
- Multiple input handles for different layers
- Output format selection (image/video)

**Blend Modes:**

- Normal, Multiply, Screen, Overlay
- Soft Light, Hard Light
- Color Dodge, Color Burn
- Darken, Lighten
- Difference, Exclusion

## Node Factory

The node factory (`nodeFactory.ts`) provides utilities for creating and managing nodes:

### Functions

#### `createNode(options)`

Creates a new node with default values.

```typescript
const audioNode = createNode({
  type: NodeType.AUDIO,
  position: { x: 100, y: 200 },
  data: { volume: 0.8 }
});
```

#### `updateNodeStatus(node, status, progress?, error?)`

Updates node execution status.

```typescript
const updatedNode = updateNodeStatus(
  node,
  NodeStatus.EXECUTING,
  50 // progress percentage
);
```

#### `updateNodeParameter(node, parameter, value)`

Updates node parameters, supporting nested paths.

```typescript
// Top-level parameter
const updated = updateNodeParameter(node, 'volume', 0.5);

// Nested parameter
const updated = updateNodeParameter(node, 'parameters.brightness', 20);
```

#### `isNodeReady(node)`

Validates if a node has all requirements to execute.

#### `getNodeExecutionParams(node)`

Extracts parameters for Function Runner execution.

## Node Registry

The node registry (`nodes/index.ts`) exports:

- `nodeTypes`: Component mapping for React Flow
- `nodeDefinitions`: Node creation menu definitions
- `connectionRules`: Valid connection types
- `nodeCategories`: UI grouping

## Integration with Function Runner

Nodes integrate with the backend Function Runner through:

1. **Parameter Extraction**: `getNodeExecutionParams()` formats node data for execution
2. **Status Updates**: WebSocket messages update node status during execution
3. **Progress Tracking**: Real-time progress visualization
4. **Result Handling**: Preview images and output data display

## Usage Example

```typescript
import { createNode } from '$lib/utils/nodeFactory';
import { NodeType } from '$lib/types/nodes';

// Create an audio generation node
const audioNode = createNode({
  type: NodeType.AUDIO,
  position: { x: 100, y: 100 },
  data: {
    audioSource: 'generate',
    text: 'Welcome to the show',
    voiceId: 'voice-123'
  }
});

// Create an effect node
const effectNode = createNode({
  type: NodeType.EFFECT,
  position: { x: 300, y: 100 },
  data: {
    effectType: 'color',
    intensity: 80
  }
});

// Create a composite node
const compositeNode = createNode({
  type: NodeType.COMPOSITE,
  position: { x: 500, y: 100 }
});
```

## Styling

Nodes use CSS variables for theming:

- `--node-bg`: Background color
- `--node-border`: Border color
- `--node-selected`: Selected state color
- `--text-primary/secondary`: Text colors
- `--input-bg/border`: Form control colors

Each node type has a distinct handle color for visual differentiation:

- Audio: Blue (#3b82f6)
- Effect: Purple (#8b5cf6)
- Composite: Amber (#f59e0b)

## Testing

Comprehensive test suites cover:

- Component rendering and interaction
- Parameter updates and event handling
- Node factory functions
- Connection validation
- State management

Run tests with:

```bash
npm test src/lib/components/canvas/nodes/
npm test src/lib/utils/nodeFactory.test.ts
```
