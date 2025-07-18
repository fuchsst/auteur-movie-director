import type { Node } from '$lib/canvas/types/canvas';

// Story structure node types for Production Canvas

export const storyNodeTypes = {
  // Act structure nodes
  'story-act': {
    component: 'ActNode',
    label: 'Act',
    category: 'story-structure',
    color: '#8b5cf6',
    icon: '🎬',
    defaultData: {
      act: 1,
      title: 'Act 1',
      description: 'Setup and introduction',
      duration: 25,
      scenes: []
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Scene structure nodes
  'story-scene': {
    component: 'SceneNode',
    label: 'Scene',
    category: 'story-structure',
    color: '#06b6d4',
    icon: '🎭',
    defaultData: {
      act: 1,
      scene: 1,
      title: 'Scene 1',
      description: 'Scene description',
      shots: [],
      characters: [],
      locations: []
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Shot structure nodes
  'story-shot': {
    component: 'ShotNode',
    label: 'Shot',
    category: 'story-structure',
    color: '#10b981',
    icon: '📹',
    defaultData: {
      act: 1,
      scene: 1,
      shot: 1,
      title: 'Shot 1',
      camera: 'wide',
      duration: 5,
      description: 'Shot description',
      takes: [],
      assets: []
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Beat structure nodes
  'story-beat': {
    component: 'BeatNode',
    label: 'Beat',
    category: 'story-structure',
    color: '#f59e0b',
    icon: '🎯',
    defaultData: {
      beatType: 'plot',
      title: 'Story Beat',
      description: 'Beat description',
      position: 0,
      emotionalArc: 'neutral',
      importance: 'medium'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Three-Act structure specific
  'three-act-setup': {
    component: 'ThreeActSetupNode',
    label: 'Setup (Act 1)',
    category: 'three-act',
    color: '#ef4444',
    icon: '🎪',
    defaultData: {
      act: 1,
      title: 'Setup',
      description: 'Establish characters, world, and stakes',
      duration: 25,
      keyMoments: ['hook', 'inciting_incident', 'first_plot_point'],
      scenes: []
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'three-act-confrontation': {
    component: 'ThreeActConfrontationNode',
    label: 'Confrontation (Act 2)',
    category: 'three-act',
    color: '#f97316',
    icon: '⚔️',
    defaultData: {
      act: 2,
      title: 'Confrontation',
      description: 'Rising action and complications',
      duration: 50,
      keyMoments: ['first_pinch_point', 'midpoint', 'second_pinch_point'],
      scenes: []
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'three-act-resolution': {
    component: 'ThreeActResolutionNode',
    label: 'Resolution (Act 3)',
    category: 'three-act',
    color: '#84cc16',
    icon: '🏁',
    defaultData: {
      act: 3,
      title: 'Resolution',
      description: 'Climax and resolution',
      duration: 25,
      keyMoments: ['climax', 'denouement'],
      scenes: []
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Seven-Point structure specific
  'seven-point-hook': {
    component: 'SevenPointHookNode',
    label: 'Hook',
    category: 'seven-point',
    color: '#8b5cf6',
    icon: '🪝',
    defaultData: {
      position: 0,
      title: 'Hook',
      description: 'Opening hook to grab attention',
      duration: 5,
      emotionalArc: 'neutral'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'seven-point-plot-turn-1': {
    component: 'SevenPointPlotTurn1Node',
    label: 'Plot Turn 1',
    category: 'seven-point',
    color: '#ef4444',
    icon: '↗️',
    defaultData: {
      position: 25,
      title: 'Plot Turn 1',
      description: 'Call to adventure',
      duration: 10,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'seven-point-pin-1': {
    component: 'SevenPointPin1Node',
    label: 'Pinch 1',
    category: 'seven-point',
    color: '#f59e0b',
    icon: '💥',
    defaultData: {
      position: 37.5,
      title: 'Pinch 1',
      description: 'Pressure increases',
      duration: 5,
      emotionalArc: 'negative'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'seven-point-midpoint': {
    component: 'SevenPointMidpointNode',
    label: 'Midpoint',
    category: 'seven-point',
    color: '#06b6d4',
    icon: '🎯',
    defaultData: {
      position: 50,
      title: 'Midpoint',
      description: 'Point of no return',
      duration: 10,
      emotionalArc: 'neutral'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'seven-point-pin-2': {
    component: 'SevenPointPin2Node',
    label: 'Pinch 2',
    category: 'seven-point',
    color: '#f59e0b',
    icon: '💥',
    defaultData: {
      position: 62.5,
      title: 'Pinch 2',
      description: 'Major setback',
      duration: 5,
      emotionalArc: 'negative'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'seven-point-plot-turn-2': {
    component: 'SevenPointPlotTurn2Node',
    label: 'Plot Turn 2',
    category: 'seven-point',
    color: '#10b981',
    icon: '↗️',
    defaultData: {
      position: 75,
      title: 'Plot Turn 2',
      description: 'Solution revealed',
      duration: 10,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'seven-point-resolution': {
    component: 'SevenPointResolutionNode',
    label: 'Resolution',
    category: 'seven-point',
    color: '#84cc16',
    icon: '🏁',
    defaultData: {
      position: 100,
      title: 'Resolution',
      description: 'Climax and resolution',
      duration: 10,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Blake Snyder beat sheet specific
  'blake-opening-image': {
    component: 'BlakeOpeningImageNode',
    label: 'Opening Image',
    category: 'blake-snyder',
    color: '#8b5cf6',
    icon: '🖼️',
    defaultData: {
      beat: 'opening_image',
      title: 'Opening Image',
      description: 'Visual representation of theme',
      page: 1,
      emotionalArc: 'neutral'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-theme-stated': {
    component: 'BlakeThemeStatedNode',
    label: 'Theme Stated',
    category: 'blake-snyder',
    color: '#06b6d4',
    icon: '💭',
    defaultData: {
      beat: 'theme_stated',
      title: 'Theme Stated',
      description: 'Theme is explicitly stated',
      page: 5,
      emotionalArc: 'neutral'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-set-up': {
    component: 'BlakeSetupNode',
    label: 'Set-up',
    category: 'blake-snyder',
    color: '#f59e0b',
    icon: '🏗️',
    defaultData: {
      beat: 'setup',
      title: 'Set-up',
      description: 'World and character introduction',
      page: 10,
      emotionalArc: 'neutral'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-catalyst': {
    component: 'BlakeCatalystNode',
    label: 'Catalyst',
    category: 'blake-snyder',
    color: '#ef4444',
    icon: '⚡',
    defaultData: {
      beat: 'catalyst',
      title: 'Catalyst',
      description: 'Life-changing event',
      page: 12,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-debate': {
    component: 'BlakeDebateNode',
    label: 'Debate',
    category: 'blake-snyder',
    color: '#f59e0b',
    icon: '🤔',
    defaultData: {
      beat: 'debate',
      title: 'Debate',
      description: 'Should I go?',
      page: 12,
      emotionalArc: 'negative'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-break-into-2': {
    component: 'BlakeBreakInto2Node',
    label: 'Break into 2',
    category: 'blake-snyder',
    color: '#10b981',
    icon: '🚪',
    defaultData: {
      beat: 'break_into_2',
      title: 'Break into 2',
      description: 'Enter new world',
      page: 25,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-b-story': {
    component: 'BlakeBStoryNode',
    label: 'B Story',
    category: 'blake-snyder',
    color: '#06b6d4',
    icon: '💕',
    defaultData: {
      beat: 'b_story',
      title: 'B Story',
      description: 'Love story or secondary plot',
      page: 30,
      emotionalArc: 'neutral'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-fun-and-games': {
    component: 'BlakeFunAndGamesNode',
    label: 'Fun and Games',
    category: 'blake-snyder',
    color: '#8b5cf6',
    icon: '🎪',
    defaultData: {
      beat: 'fun_and_games',
      title: 'Fun and Games',
      description: 'Promise of the premise',
      page: 30,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-midpoint': {
    component: 'BlakeMidpointNode',
    label: 'Midpoint',
    category: 'blake-snyder',
    color: '#f59e0b',
    icon: '🎯',
    defaultData: {
      beat: 'midpoint',
      title: 'Midpoint',
      description: 'False victory or false defeat',
      page: 55,
      emotionalArc: 'neutral'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-bad-guys-close-in': {
    component: 'BlakeBadGuysCloseInNode',
    label: 'Bad Guys Close In',
    category: 'blake-snyder',
    color: '#ef4444',
    icon: '😈',
    defaultData: {
      beat: 'bad_guys_close_in',
      title: 'Bad Guys Close In',
      description: 'Villains regroup',
      page: 55,
      emotionalArc: 'negative'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-all-is-lost': {
    component: 'BlakeAllIsLostNode',
    label: 'All Is Lost',
    category: 'blake-snyder',
    color: '#ef4444',
    icon: '💔',
    defaultData: {
      beat: 'all_is_lost',
      title: 'All Is Lost',
      description: 'Darkest moment',
      page: 75,
      emotionalArc: 'negative'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-dark-night-of-the-soul': {
    component: 'BlakeDarkNightOfTheSoulNode',
    label: 'Dark Night of the Soul',
    category: 'blake-snyder',
    color: '#6b7280',
    icon: '🌙',
    defaultData: {
      beat: 'dark_night_of_the_soul',
      title: 'Dark Night of the Soul',
      description: 'Moment of despair',
      page: 75,
      emotionalArc: 'negative'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-break-into-3': {
    component: 'BlakeBreakInto3Node',
    label: 'Break into 3',
    category: 'blake-snyder',
    color: '#10b981',
    icon: '🚪',
    defaultData: {
      beat: 'break_into_3',
      title: 'Break into 3',
      description: 'Solution found',
      page: 85,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-finale': {
    component: 'BlakeFinaleNode',
    label: 'Finale',
    category: 'blake-snyder',
    color: '#84cc16',
    icon: '🏆',
    defaultData: {
      beat: 'finale',
      title: 'Finale',
      description: 'Final showdown',
      page: 85,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  'blake-final-image': {
    component: 'BlakeFinalImageNode',
    label: 'Final Image',
    category: 'blake-snyder',
    color: '#8b5cf6',
    icon: '🖼️',
    defaultData: {
      beat: 'final_image',
      title: 'Final Image',
      description: 'Closing image',
      page: 110,
      emotionalArc: 'positive'
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  }
};

// Helper function to create story nodes
export function createStoryNode(type: string, position: { x: number; y: number }, data: any = {}): Omit<Node, 'id'> {
  const nodeType = storyNodeTypes[type];
  if (!nodeType) {
    throw new Error(`Unknown story node type: ${type}`);
  }

  return {
    type,
    position,
    data: { ...nodeType.defaultData, ...data },
    style: {
      background: nodeType.color,
      color: 'white',
      borderRadius: '8px',
      padding: '10px',
      fontSize: '12px',
      fontWeight: 'bold',
      border: '2px solid transparent',
      cursor: 'pointer'
    }
  };
}

// Helper function to get node type metadata
export function getStoryNodeMetadata(type: string) {
  return storyNodeTypes[type] || null;
}

// Helper function to get all nodes by category
export function getStoryNodesByCategory(category: string) {
  return Object.entries(storyNodeTypes)
    .filter(([_, config]) => config.category === category)
    .map(([type, config]) => ({ type, ...config }));
}

// Helper function to validate story structure
export function validateStoryStructure(nodes: Node[]): {
  isValid: boolean;
  errors: string[];
  warnings: string[];
} {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check for required structure nodes
  const actNodes = nodes.filter(n => n.type.includes('act'));
  const sceneNodes = nodes.filter(n => n.type.includes('scene'));
  const beatNodes = nodes.filter(n =\u003e n.type.includes('beat'));

  // Validate three-act structure
  const threeActNodes = nodes.filter(n => n.type.startsWith('three-act-'));
  if (threeActNodes.length > 0 && threeActNodes.length !== 3) {
    warnings.push('Three-act structure should have exactly 3 acts');
  }

  // Validate seven-point structure
  const sevenPointNodes = nodes.filter(n => n.type.startsWith('seven-point-'));
  if (sevenPointNodes.length > 0 && sevenPointNodes.length !== 7) {
    warnings.push('Seven-point structure should have exactly 7 points');
  }

  // Validate Blake Snyder structure
  const blakeSnyderNodes = nodes.filter(n => n.type.startsWith('blake-'));
  if (blakeSnyderNodes.length > 0 && blakeSnyderNodes.length !== 15) {
    warnings.push('Blake Snyder structure should have exactly 15 beats');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
}