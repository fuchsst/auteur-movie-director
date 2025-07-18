import ActNode from '$lib/canvas/components/nodes/ActNode.svelte';
import SceneNode from '$lib/canvas/components/nodes/SceneNode.svelte';
import ShotNode from '$lib/canvas/components/nodes/ShotNode.svelte';

// Story structure node components
export const storyNodeComponents = {
  'story-act': ActNode,
  'story-scene': SceneNode,
  'story-shot': ShotNode,
  
  // Three-Act structure
  'three-act-setup': ActNode,
  'three-act-confrontation': ActNode,
  'three-act-resolution': ActNode,
  
  // Seven-Point structure
  'seven-point-hook': SceneNode,
  'seven-point-plot-turn-1': SceneNode,
  'seven-point-pin-1': SceneNode,
  'seven-point-midpoint': SceneNode,
  'seven-point-pin-2': SceneNode,
  'seven-point-plot-turn-2': SceneNode,
  'seven-point-resolution': SceneNode,
  
  // Blake Snyder structure
  'blake-opening-image': SceneNode,
  'blake-theme-stated': SceneNode,
  'blake-set-up': SceneNode,
  'blake-catalyst': SceneNode,
  'blake-debate': SceneNode,
  'blake-break-into-2': SceneNode,
  'blake-b-story': SceneNode,
  'blake-fun-and-games': SceneNode,
  'blake-midpoint': SceneNode,
  'blake-bad-guys-close-in': SceneNode,
  'blake-all-is-lost': SceneNode,
  'blake-dark-night-of-the-soul': SceneNode,
  'blake-break-into-3': SceneNode,
  'blake-finale': SceneNode,
  'blake-final-image': SceneNode
};

// Export all node types
export { ActNode, SceneNode, ShotNode };