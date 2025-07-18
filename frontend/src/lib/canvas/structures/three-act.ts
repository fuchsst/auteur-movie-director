import type { Node, Edge } from '$lib/canvas/types/canvas';
import { createStoryNode } from '$lib/canvas/nodes/story-nodes';
import { v4 as uuidv4 } from 'uuid';

// Three-Act Structure implementation for Production Canvas

export interface ThreeActStructure {
  acts: Array<{
    act: number;
    title: string;
    description: string;
    duration: number;
    position: { x: number; y: number };
    scenes: Array<{
      scene: number;
      title: string;
      description: string;
      position: { x: number; y: number };
    }>;
  }>;
  connections: Array<{
    source: string;
    target: string;
  }>;
}

export class ThreeActStructureGenerator {
  private canvasWidth: number;
  private canvasHeight: number;
  private padding: number;

  constructor(
    canvasWidth: number = 1200,
    canvasHeight: number = 600,
    padding: number = 100
  ) {
    this.canvasWidth = canvasWidth;
    this.canvasHeight = canvasHeight;
    this.padding = padding;
  }

  // Generate complete three-act structure
  generateStructure(): { nodes: Node[]; edges: Edge[] } {
    const structure = this.createStructureLayout();
    const nodes = this.createActNodes(structure);
    const edges = this.createActConnections(structure);

    return { nodes, edges };
  }

  // Create the three-act structure layout
  private createStructureLayout(): ThreeActStructure {
    const availableWidth = this.canvasWidth - (2 * this.padding);
    const actWidth = availableWidth / 3;
    const centerY = this.canvasHeight / 2;

    return {
      acts: [
        {
          act: 1,
          title: 'Act 1: Setup',
          description: 'Establish characters, world, and stakes',
          duration: 25,
          position: { x: this.padding + actWidth/2, y: centerY },
          scenes: [
            {
              scene: 1,
              title: 'Opening Scene',
              description: 'Hook the audience',
              position: { x: this.padding + actWidth/4, y: centerY - 100 }
            },
            {
              scene: 2,
              title: 'Inciting Incident',
              description: 'Disrupt the status quo',
              position: { x: this.padding + (actWidth * 3)/4, y: centerY - 100 }
            }
          ]
        },
        {
          act: 2,
          title: 'Act 2: Confrontation',
          description: 'Rising action and complications',
          duration: 50,
          position: { x: this.padding + actWidth + actWidth/2, y: centerY },
          scenes: [
            {
              scene: 1,
              title: 'First Pinch Point',
              description: 'Increase pressure',
              position: { x: this.padding + actWidth + actWidth/4, y: centerY - 100 }
            },
            {
              scene: 2,
              title: 'Midpoint',
              description: 'Point of no return',
              position: { x: this.padding + actWidth + actWidth/2, y: centerY - 100 }
            },
            {
              scene: 3,
              title: 'Second Pinch Point',
              description: 'Major setback',
              position: { x: this.padding + actWidth + (actWidth * 3)/4, y: centerY - 100 }
            }
          ]
        },
        {
          act: 3,
          title: 'Act 3: Resolution',
          description: 'Climax and resolution',
          duration: 25,
          position: { x: this.padding + (2 * actWidth) + actWidth/2, y: centerY },
          scenes: [
            {
              scene: 1,
              title: 'Climax',
              description: 'Final confrontation',
              position: { x: this.padding + (2 * actWidth) + actWidth/4, y: centerY - 100 }
            },
            {
              scene: 2,
              title: 'Denouement',
              description: 'Wrap up loose ends',
              position: { x: this.padding + (2 * actWidth) + (actWidth * 3)/4, y: centerY - 100 }
            }
          ]
        }
      ],
      connections: [
        { source: 'act-1', target: 'act-2' },
        { source: 'act-2', target: 'act-3' }
      ]
    };
  }

  // Create act nodes
  private createActNodes(structure: ThreeActStructure): Node[] {
    const nodes: Node[] = [];

    structure.acts.forEach(act => {
      // Create act node
      const actNode = createStoryNode('three-act-setup', act.position, {
        act: act.act,
        title: act.title,
        description: act.description,
        duration: act.duration,
        scenes: act.scenes.map(s => s.title)
      });
      
      nodes.push({
        ...actNode,
        id: `act-${act.act}`,
        type: `three-act-${act.act === 1 ? 'setup' : act.act === 2 ? 'confrontation' : 'resolution'}`
      });

      // Create scene nodes for each act
      act.scenes.forEach(scene => {
        const sceneNode = createStoryNode('story-scene', scene.position, {
          act: act.act,
          scene: scene.scene,
          title: scene.title,
          description: scene.description
        });

        nodes.push({
          ...sceneNode,
          id: `scene-${act.act}-${scene.scene}`,
          parentNode: `act-${act.act}`
        });
      });
    });

    return nodes;
  }

  // Create connections between acts and scenes
  private createActConnections(structure: ThreeActStructure): Edge[] {
    const edges: Edge[] = [];

    // Connect acts
    structure.connections.forEach(connection => {
      edges.push({
        id: uuidv4(),
        source: connection.source,
        target: connection.target,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#3b82f6', strokeWidth: 2 }
      });
    });

    // Connect scenes within each act
    structure.acts.forEach(act => {
      act.scenes.forEach((scene, index) => {
        if (index < act.scenes.length - 1) {
          edges.push({
            id: uuidv4(),
            source: `scene-${act.act}-${scene.scene}`,
            target: `scene-${act.act}-${act.scenes[index + 1].scene}`,
            type: 'smoothstep',
            style: { stroke: '#64748b', strokeWidth: 1 }
          });
        }
      });

      // Connect last scene to next act (if not last act)
      if (act.act < 3 && act.scenes.length > 0) {
        edges.push({
          id: uuidv4(),
          source: `scene-${act.act}-${act.scenes[act.scenes.length - 1].scene}`,
          target: `scene-${act.act + 1}-1`,
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#3b82f6', strokeWidth: 2 }
        });
      }
    });

    return edges;
  }

  // Validate three-act structure
  validateStructure(nodes: Node[]): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
    metrics: {
      totalDuration: number;
      actDurations: number[];
      sceneCounts: number[];
    };
  } {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    const actNodes = nodes.filter(n => n.type.startsWith('three-act-'));
    const sceneNodes = nodes.filter(n => n.type === 'story-scene');

    // Check for required acts
    if (actNodes.length !== 3) {
      errors.push('Three-act structure must have exactly 3 act nodes');
    }

    // Check act durations
    const actDurations = actNodes.map(node => node.data.duration || 0);
    const totalDuration = actDurations.reduce((sum, duration) => sum + duration, 0);

    if (totalDuration !== 100) {
      warnings.push(`Total duration should be 100%, got ${totalDuration}%`);
    }

    // Check individual act durations
    const expectedDurations = [25, 50, 25];
    actDurations.forEach((duration, index) => {
      if (Math.abs(duration - expectedDurations[index]) > 5) {
        warnings.push(`Act ${index + 1} duration should be ~${expectedDurations[index]}%, got ${duration}%`);
      }
    });

    // Check scene distribution
    const sceneCounts = [0, 0, 0];
    sceneNodes.forEach(node => {
      const act = node.data.act;
      if (act >= 1 && act <= 3) {
        sceneCounts[act - 1]++;
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      metrics: {
        totalDuration,
        actDurations,
        sceneCounts
      }
    };
  }

  // Auto-complete three-act structure
  autoCompleteStructure(nodes: Node[]): { nodes: Node[]; edges: Edge[] } {
    const existingActs = nodes.filter(n => n.type.startsWith('three-act-'));
    const existingScenes = nodes.filter(n => n.type === 'story-scene');

    // If structure already exists, return empty
    if (existingActs.length === 3) {
      return { nodes: [], edges: [] };
    }

    // Calculate existing structure metrics
    const metrics = this.validateStructure([...existingActs, ...existingScenes]);
    const structure = this.createStructureLayout();

    // Merge existing with new structure
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    // Add missing acts
    structure.acts.forEach((act, actIndex) => {
      const existingAct = existingActs.find(a => a.data.act === act.act);
      if (!existingAct) {
        const actNode = createStoryNode(
          `three-act-${act.act === 1 ? 'setup' : act.act === 2 ? 'confrontation' : 'resolution'}`,
          act.position,
          {
            act: act.act,
            title: act.title,
            description: act.description,
            duration: act.duration,
            scenes: act.scenes.map(s => s.title)
          }
        );

        newNodes.push({ ...actNode, id: `act-${act.act}` });
      }
    });

    // Add missing scenes
    structure.acts.forEach(act => {
      act.scenes.forEach(scene => {
        const existingScene = existingScenes.find(s => s.data.act === act.act && s.data.scene === scene.scene);
        if (!existingScene) {
          const sceneNode = createStoryNode('story-scene', scene.position, {
            act: act.act,
            scene: scene.scene,
            title: scene.title,
            description: scene.description
          });

          newNodes.push({ ...sceneNode, id: `scene-${act.act}-${scene.scene}`, parentNode: `act-${act.act}` });
        }
      });
    });

    // Create connections for new nodes
    if (newNodes.length > 0) {
      const connections = this.createActConnections(structure);
      newEdges.push(...connections.filter(edge => 
        newNodes.some(node => node.id === edge.source || node.id === edge.target)
      ));
    }

    return { nodes: newNodes, edges: newEdges };
  }

  // Get three-act template
  getTemplate(): ThreeActStructure {
    return this.createStructureLayout();
  }

  // Visual timeline for three-act structure
  generateTimeline(): {
    positions: Array<{
      act: number;
      title: string;
      start: number;
      end: number;
      color: string;
    }>;
    totalDuration: number;
  } {
    const timeline = [
      { act: 1, title: 'Setup', start: 0, end: 25, color: '#ef4444' },
      { act: 2, title: 'Confrontation', start: 25, end: 75, color: '#f97316' },
      { act: 3, title: 'Resolution', start: 75, end: 100, color: '#84cc16' }
    ];

    return {
      positions: timeline,
      totalDuration: 100
    };
  }

  // Interactive timeline component
  createInteractiveTimeline(): {
    nodes: Node[];
    timeline: any;
  } {
    const timeline = this.generateTimeline();
    const nodes: Node[] = [];

    // Create timeline markers
    timeline.positions.forEach((position, index) => {
      const node = createStoryNode('story-beat', {
        x: this.padding + (position.start + position.end) / 2 * (this.canvasWidth - 2 * this.padding) / 100,
        y: this.canvasHeight - 50
      }, {
        beatType: 'act-marker',
        title: position.title,
        position: position.start,
        duration: position.end - position.start
      });

      nodes.push({ ...node, id: `timeline-${index}` });
    });

    return { nodes, timeline };
  }
}

// Export utility functions
export const threeActUtils = {
  // Quick three-act structure creation
  createQuickStructure: (startPosition: { x: number; y: number }) => {
    const generator = new ThreeActStructureGenerator();
    return generator.generateStructure();
  },

  // Validate existing structure
  validateExisting: (nodes: Node[]) => {
    const generator = new ThreeActStructureGenerator();
    return generator.validateStructure(nodes);
  },

  // Auto-complete missing parts
  autoComplete: (nodes: Node[]) => {
    const generator = new ThreeActStructureGenerator();
    return generator.autoCompleteStructure(nodes);
  }
};