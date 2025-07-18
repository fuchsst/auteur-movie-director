import { writable, derived, get } from 'svelte/store';
import type { Node, Edge, Viewport, CanvasState, CanvasActions } from '$lib/canvas/types/canvas';
import { v4 as uuidv4 } from 'uuid';

// Canvas store implementation following Svelte Flow patterns
interface CanvasStore {
  nodes: Node[];
  edges: Edge[];
  viewport: Viewport;
  selectedNodes: string[];
  selectedEdges: string[];
  history: CanvasState[];
  historyIndex: number;
  projectId: string | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: CanvasStore = {
  nodes: [],
  edges: [],
  viewport: { x: 0, y: 0, zoom: 1 },
  selectedNodes: [],
  selectedEdges: [],
  history: [],
  historyIndex: -1,
  projectId: null,
  isLoading: false,
  error: null
};

function createCanvasStore() {
  const { subscribe, set, update } = writable<CanvasStore>(initialState);

  // Core canvas actions
  const actions: CanvasActions = {
    // Node management
    addNode: (node: Omit<Node, 'id'>) => {
      update(state => {
        const newNode: Node = {
          ...node,
          id: uuidv4(),
          selected: false,
          dragging: false,
          measured: { width: 150, height: 50 }
        };
        
        const newState = {
          ...state,
          nodes: [...state.nodes, newNode]
        };
        
        return addToHistory(newState);
      });
    },

    updateNode: (id: string, updates: Partial<Node>) => {
      update(state => {
        const newState = {
          ...state,
          nodes: state.nodes.map(node => 
            node.id === id ? { ...node, ...updates } : node
          )
        };
        
        return addToHistory(newState);
      });
    },

    removeNode: (id: string) => {
      update(state => {
        const newState = {
          ...state,
          nodes: state.nodes.filter(node => node.id !== id),
          edges: state.edges.filter(edge => 
            edge.source !== id && edge.target !== id
          )
        };
        
        return addToHistory(newState);
      });
    },

    // Edge management
    addEdge: (edge: Omit<Edge, 'id'>) => {
      update(state => {
        const newEdge: Edge = {
          ...edge,
          id: uuidv4(),
          animated: false,
          selected: false
        };
        
        const newState = {
          ...state,
          edges: [...state.edges, newEdge]
        };
        
        return addToHistory(newState);
      });
    },

    updateEdge: (id: string, updates: Partial<Edge>) => {
      update(state => {
        const newState = {
          ...state,
          edges: state.edges.map(edge => 
            edge.id === id ? { ...edge, ...updates } : edge
          )
        };
        
        return addToHistory(newState);
      });
    },

    removeEdge: (id: string) => {
      update(state => {
        const newState = {
          ...state,
          edges: state.edges.filter(edge => edge.id !== id)
        };
        
        return addToHistory(newState);
      });
    },

    // Selection management
    selectNode: (id: string, multi: boolean = false) => {
      update(state => {
        const selectedNodes = multi
          ? state.selectedNodes.includes(id)
            ? state.selectedNodes.filter(n => n !== id)
            : [...state.selectedNodes, id]
          : [id];

        return {
          ...state,
          selectedNodes,
          nodes: state.nodes.map(node => ({
            ...node,
            selected: selectedNodes.includes(node.id)
          }))
        };
      });
    },

    selectEdge: (id: string, multi: boolean = false) => {
      update(state => {
        const selectedEdges = multi
          ? state.selectedEdges.includes(id)
            ? state.selectedEdges.filter(e => e !== id)
            : [...state.selectedEdges, id]
          : [id];

        return {
          ...state,
          selectedEdges,
          edges: state.edges.map(edge => ({
            ...edge,
            selected: selectedEdges.includes(edge.id)
          }))
        };
      });
    },

    clearSelection: () => {
      update(state => ({
        ...state,
        selectedNodes: [],
        selectedEdges: [],
        nodes: state.nodes.map(node => ({ ...node, selected: false })),
        edges: state.edges.map(edge => ({ ...edge, selected: false }))
      }));
    },

    // Viewport management
    setViewport: (viewport: Viewport) => {
      update(state => ({ ...state, viewport }));
    },

    // History management
    undo: () => {
      update(state => {
        if (state.historyIndex <= 0) return state;
        
        const newIndex = state.historyIndex - 1;
        const previousState = state.history[newIndex];
        
        return {
          ...state,
          ...previousState,
          historyIndex: newIndex
        };
      });
    },

    redo: () => {
      update(state => {
        if (state.historyIndex >= state.history.length - 1) return state;
        
        const newIndex = state.historyIndex + 1;
        const nextState = state.history[newIndex];
        
        return {
          ...state,
          ...nextState,
          historyIndex: newIndex
        };
      });
    },

    // Project management
    loadProject: async (projectId: string) => {
      update(state => ({ ...state, isLoading: true, error: null }));
      
      try {
        const response = await fetch(`/api/v1/canvas/${projectId}`);
        const data = await response.json();
        
        update(state => ({
          ...state,
          isLoading: false,
          projectId,
          nodes: data.nodes || [],
          edges: data.edges || [],
          viewport: data.viewport || { x: 0, y: 0, zoom: 1 },
          history: [],
          historyIndex: -1
        }));
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message
        }));
      }
    },

    populateFromProject: async (project: any, options: any) => {
      const { canvasPopulationService } = await import('$lib/canvas/services/canvas-population');
      update(state => ({ ...state, isLoading: true, error: null }));
      
      try {
        const result = await canvasPopulationService.populateFromProject(project, options);
        
        update(state => ({
          ...state,
          isLoading: false,
          projectId: project.id,
          nodes: result.nodes,
          edges: result.edges,
          history: [],
          historyIndex: -1
        }));
        
        return result;
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message
        }));
        throw error;
      }
    },

    saveProject: async () => {
      const state = get(canvasStore);
      
      try {
        await fetch(`/api/v1/canvas/${state.projectId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nodes: state.nodes,
            edges: state.edges,
            viewport: state.viewport
          })
        });
      } catch (error) {
        update(state => ({ ...state, error: error.message }));
      }
    },

    // Canvas state management
    clearCanvas: () => {
      update(state => addToHistory({
        ...state,
        nodes: [],
        edges: [],
        selectedNodes: [],
        selectedEdges: []
      }));
    },

    reset: () => set(initialState)
  };

  // History utility
  function addToHistory(state: CanvasStore): CanvasStore {
    const newHistory = state.history.slice(0, state.historyIndex + 1);
    const newState = {
      ...state,
      history: [...newHistory, {
        nodes: state.nodes,
        edges: state.edges,
        viewport: state.viewport
      }],
      historyIndex: newHistory.length
    };

    // Limit history to 50 states
    if (newState.history.length > 50) {
      newState.history = newState.history.slice(-50);
      newState.historyIndex = 49;
    }

    return newState;
  }

  // Derived stores for computed values
  const nodeCount = derived(canvasStore, $store => $store.nodes.length);
  const selectedNodeCount = derived(canvasStore, $store => $store.selectedNodes.length);
  const canUndo = derived(canvasStore, $store => $store.historyIndex > 0);
  const canRedo = derived(canvasStore, $store => $store.historyIndex < $store.history.length - 1);

  return {
    subscribe,
    ...actions,
    nodeCount,
    selectedNodeCount,
    canUndo,
    canRedo
  };
}

export const canvasStore = createCanvasStore();