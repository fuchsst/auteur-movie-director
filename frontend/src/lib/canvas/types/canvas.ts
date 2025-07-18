// Core canvas types for Production Canvas

export interface Position {
  x: number;
  y: number;
}

export interface Dimensions {
  width: number;
  height: number;
}

export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}

export interface Node {
  id: string;
  type: string;
  position: Position;
  data: Record<string, any>;
  selected?: boolean;
  dragging?: boolean;
  measured?: Dimensions;
  style?: Record<string, string | number>;
  className?: string;
  parentNode?: string;
  extent?: 'parent' | Position[];
  zIndex?: number;
  deletable?: boolean;
  connectable?: boolean;
  draggable?: boolean;
  selectable?: boolean;
}

export interface Edge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: string;
  data?: Record<string, any>;
  selected?: boolean;
  animated?: boolean;
  style?: Record<string, string | number>;
  label?: string;
  labelStyle?: Record<string, string | number>;
  labelBgStyle?: Record<string, string | number>;
  labelBgPadding?: [number, number];
  labelBgBorderRadius?: number;
  markerStart?: string;
  markerEnd?: string;
  zIndex?: number;
  deletable?: boolean;
  updatable?: boolean;
}

export interface CanvasState {
  nodes: Node[];
  edges: Edge[];
  viewport: Viewport;
}

export interface CanvasActions {
  addNode: (node: Omit<Node, 'id'>) => void;
  updateNode: (id: string, updates: Partial<Node>) => void;
  removeNode: (id: string) => void;
  addEdge: (edge: Omit<Edge, 'id'>) => void;
  updateEdge: (id: string, updates: Partial<Edge>) => void;
  removeEdge: (id: string) => void;
  selectNode: (id: string, multi?: boolean) => void;
  selectEdge: (id: string, multi?: boolean) => void;
  clearSelection: () => void;
  setViewport: (viewport: Viewport) => void;
  undo: () => void;
  redo: () => void;
  loadProject: (projectId: string) => Promise<void>;
  saveProject: () => Promise<void>;
  clearCanvas: () => void;
  reset: () => void;
}

export interface CanvasProps {
  nodes: Node[];
  edges: Edge[];
  viewport?: Viewport;
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
  onViewportChange?: (viewport: Viewport) => void;
  onNodeDragStart?: (event: any, node: Node) => void;
  onNodeDrag?: (event: any, node: Node) => void;
  onNodeDragStop?: (event: any, node: Node) => void;
  onNodeClick?: (event: any, node: Node) => void;
  onEdgeClick?: (event: any, edge: Edge) => void;
  onConnect?: (connection: any) => void;
  onConnectStart?: (event: any, node: Node, handle: string) => void;
  onConnectEnd?: (event: any) => void;
  onSelectionChange?: (selected: { nodes: Node[], edges: Edge[] }) => void;
  onSelectionDragStart?: (event: any, nodes: Node[]) => void;
  onSelectionDrag?: (event: any, nodes: Node[]) => void;
  onSelectionDragStop?: (event: any, nodes: Node[]) => void;
  onPaneClick?: (event: any) => void;
  onPaneScroll?: (event: any) => void;
  onPaneContextMenu?: (event: any) => void;
}

// Story-specific node types
export interface StoryNodeData {
  title: string;
  description?: string;
  duration?: number;
  act?: number;
  scene?: number;
  beat?: string;
  characters?: string[];
  locations?: string[];
  assets?: string[];
}

export interface ActNodeData extends StoryNodeData {
  act: number;
  duration: number;
  scenes: string[];
}

export interface SceneNodeData extends StoryNodeData {
  act: number;
  scene: number;
  shots: string[];
}

export interface ShotNodeData extends StoryNodeData {
  act: number;
  scene: number;
  shot: number;
  camera?: string;
  duration?: number;
  takes: string[];
}

export interface BeatNodeData extends StoryNodeData {
  beatType: string;
  position: number;
  emotionalArc?: 'positive' | 'negative' | 'neutral';
}

// Asset node types
export interface AssetNodeData {
  assetId: string;
  assetType: 'character' | 'style' | 'location' | 'prop';
  assetName: string;
  thumbnail?: string;
  metadata?: Record<string, any>;
}

// Connection types
export interface Connection {
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type: 'story-flow' | 'asset-link' | 'dependency';
}

// Canvas events
export interface CanvasEvent {
  type: string;
  data: any;
  timestamp: number;
  userId?: string;
}

// Real-time collaboration types
export interface CollaborationState {
  users: User[];
  cursors: Cursor[];
  selection: string[];
  isEditing: boolean;
}

export interface User {
  id: string;
  name: string;
  color: string;
  cursor?: Position;
  selectedNodes: string[];
}

export interface Cursor {
  userId: string;
  position: Position;
  visible: boolean;
}

// Template types
export interface CanvasTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  nodes: Node[];
  edges: Edge[];
  tags: string[];
  author: string;
  version: string;
  created: Date;
  updated: Date;
  rating: number;
  usageCount: number;
}

// Export types
export interface CanvasExport {
  format: 'json' | 'png' | 'svg' | 'pdf';
  data: any;
  metadata: {
    projectId: string;
    version: string;
    created: Date;
    userId: string;
  };
}

// Performance types
export interface PerformanceMetrics {
  fps: number;
  renderTime: number;
  memoryUsage: number;
  nodeCount: number;
  edgeCount: number;
}

// Configuration types
export interface CanvasConfig {
  snapToGrid: boolean;
  gridSize: number;
  showGrid: boolean;
  showMinimap: boolean;
  showControls: boolean;
  zoomOnScroll: boolean;
  zoomOnPinch: boolean;
  panOnScroll: boolean;
  panOnDrag: boolean;
  fitView: boolean;
  minZoom: number;
  maxZoom: number;
  defaultZoom: number;
  defaultPosition: Position;
}

// Error types
export interface CanvasError {
  type: 'validation' | 'network' | 'rendering' | 'collaboration';
  message: string;
  details?: any;
  timestamp: Date;
}

// Validation types
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  type: string;
  message: string;
  nodeId?: string;
  edgeId?: string;
}

export interface ValidationWarning {
  type: string;
  message: string;
  nodeId?: string;
  edgeId?: string;
}