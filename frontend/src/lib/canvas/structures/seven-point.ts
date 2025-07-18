import type { Node, Edge } from '$lib/canvas/types/canvas';
import { createStoryNode } from '$lib/canvas/nodes/story-nodes';
import { v4 as uuidv4 } from 'uuid';

// Seven-Point Structure implementation for Production Canvas

export interface SevenPointBeat {
  position: number; // 0-100 percentage
  title: string;
  description: string;
  emotionalArc: 'positive' | 'negative' | 'neutral';
  importance: 'high' | 'medium' | 'low';
  expectedDuration: number; // percentage of total
}

export interface SevenPointStructure {
  beats: SevenPointBeat[];
  connections: Array<{
    source: string;
    target: string;
    type: 'story-flow' | 'emotional-arc';
  }>;
}

export class SevenPointStructureGenerator {
  private canvasWidth: number;
  private canvasHeight: number;
  private padding: number;

  constructor(
    canvasWidth: number = 1200,
    canvasHeight: number = 600,
    padding: number = 80
  ) {
    this.canvasWidth = canvasWidth;
    this.canvasHeight = canvasHeight;
    this.padding = padding;
  }

  // Predefined seven-point beats
  private sevenPointBeats: SevenPointBeat[] = [
    {
      position: 0,
      title: 'Hook',
      description: 'Grab the audience\'s attention',
      emotionalArc: 'neutral',
      importance: 'high',
      expectedDuration: 5
    },
    {
      position: 25,
      title: 'Plot Turn 1',
      description: 'Call to adventure - story truly begins',
      emotionalArc: 'positive',
      importance: 'high',
      expectedDuration: 10
    },
    {
      position: 37.5,
      title: 'Pinch Point 1',
      description: 'First major pressure - forces action',
      emotionalArc: 'negative',
      importance: 'medium',
      expectedDuration: 5
    },
    {
      position: 50,
      title: 'Midpoint',
      description: 'Point of no return - character commits',
      emotionalArc: 'neutral',
      importance: 'high',
      expectedDuration: 10
    },
    {
      position: 62.5,
      title: 'Pinch Point 2',
      description: 'Major setback - all seems lost',
      emotionalArc: 'negative',
      importance: 'high',
      expectedDuration: 5
    },
    {
      position: 75,
      title: 'Plot Turn 2',
      description: 'Solution revealed - hope returns',
      emotionalArc: 'positive',
      importance: 'high',
      expectedDuration: 10
    },
    {
      position: 100,
      title: 'Resolution',
      description: 'Final confrontation and climax',
      emotionalArc: 'positive',
      importance: 'high',
      expectedDuration: 15
    }
  ];

  // Generate complete seven-point structure
  generateStructure(): { nodes: Node[]; edges: Edge[] } {
    const structure = this.createStructureLayout();
    const nodes = this.createBeatNodes(structure);
    const edges = this.createBeatConnections(structure);

    return { nodes, edges };
  }

  // Create seven-point structure layout
  private createStructureLayout(): SevenPointStructure {
    const availableWidth = this.canvasWidth - (2 * this.padding);
    const startX = this.padding;
    const centerY = this.canvasHeight / 2;

    return {
      beats: this.sevenPointBeats.map((beat, index) => ({
        ...beat,
        position: {
          x: startX + (beat.position / 100) * availableWidth,
          y: centerY + this.calculateEmotionalOffset(beat.emotionalArc, index)
        }
      })),
      connections: this.createConnections()
    };
  }

  // Calculate emotional arc offset
  private calculateEmotionalOffset(emotionalArc: string, index: number): number {
    const baseOffset = 0;
    const arcOffsets = {
      'positive': -80,
      'negative': 80,
      'neutral': 0
    };
    
    // Add some variation based on index for visual appeal
    const variation = Math.sin(index * 0.5) * 20;
    return baseOffset + arcOffsets[emotionalArc] + variation;
  }

  // Create beat connections
  private createConnections(): SevenPointStructure['connections'] {
    return [
      { source: 'hook', target: 'plot-turn-1', type: 'story-flow' },
      { source: 'plot-turn-1', target: 'pinch-1', type: 'story-flow' },
      { source: 'pinch-1', target: 'midpoint', type: 'story-flow' },
      { source: 'midpoint', target: 'pinch-2', type: 'story-flow' },
      { source: 'pinch-2', target: 'plot-turn-2', type: 'story-flow' },
      { source: 'plot-turn-2', target: 'resolution', type: 'story-flow' },
      
      // Emotional arc connections
      { source: 'hook', target: 'resolution', type: 'emotional-arc' }
    ];
  }

  // Create beat nodes
  private createBeatNodes(structure: SevenPointStructure): Node[] {
    return structure.beats.map((beat, index) => {
      const nodeType = this.getBeatNodeType(beat.title);
      const node = createStoryNode(nodeType, beat.position, {
        beatType: beat.title.toLowerCase().replace(/\s+/g, '-'),
        title: beat.title,
        description: beat.description,
        position: beat.position,
        emotionalArc: beat.emotionalArc,
        importance: beat.importance,
        expectedDuration: beat.expectedDuration
      });

      return {
        ...node,
        id: beat.title.toLowerCase().replace(/\s+/g, '-'),
        style: {
          ...node.style,
          backgroundColor: this.getBeatColor(beat.emotionalArc),
          borderRadius: '12px',
          padding: '12px',
          minWidth: '140px',
          textAlign: 'center'
        }
      };
    });
  }

  // Get beat node type
  private getBeatNodeType(title: string): string {
    const typeMap = {
      'Hook': 'seven-point-hook',
      'Plot Turn 1': 'seven-point-plot-turn-1',
      'Pinch Point 1': 'seven-point-pin-1',
      'Midpoint': 'seven-point-midpoint',
      'Pinch Point 2': 'seven-point-pin-2',
      'Plot Turn 2': 'seven-point-plot-turn-2',
      'Resolution': 'seven-point-resolution'
    };
    return typeMap[title] || 'story-beat';
  }

  // Get color based on emotional arc
  private getBeatColor(emotionalArc: string): string {
    const colors = {
      'positive': '#10b981',
      'negative': '#ef4444',
      'neutral': '#3b82f6'
    };
    return colors[emotionalArc] || '#6b7280';
  }

  // Create beat connections
  private createBeatConnections(structure: SevenPointStructure): Edge[] {
    const edges: Edge[] = [];

    structure.connections.forEach(connection => {
      const edge: Edge = {
        id: uuidv4(),
        source: connection.source,
        target: connection.target,
        type: connection.type === 'emotional-arc' ? 'straight' : 'smoothstep',
        animated: connection.type === 'emotional-arc',
        style: {
          stroke: connection.type === 'emotional-arc' ? '#8b5cf6' : '#3b82f6',
          strokeWidth: connection.type === 'emotional-arc' ? 1 : 2,
          strokeDasharray: connection.type === 'emotional-arc' ? '5,5' : undefined
        }
      };

      edges.push(edge);
    });

    return edges;
  }

  // Calculate emotional arc visualization
  generateEmotionalArc(): {
    points: Array<{
      x: number;
      y: number;
      beat: string;
      emotionalArc: string;
    }>;
    path: string;
  } {
    const availableWidth = this.canvasWidth - (2 * this.padding);
    const startX = this.padding;
    const centerY = this.canvasHeight / 2;

    const points = this.sevenPointBeats.map(beat => ({
      x: startX + (beat.position / 100) * availableWidth,
      y: centerY + this.getEmotionalY(beat.emotionalArc),
      beat: beat.title,
      emotionalArc: beat.emotionalArc
    }));

    // Create SVG path
    const path = this.createSmoothPath(points);

    return { points, path };
  }

  // Get Y position based on emotional arc
  private getEmotionalY(emotionalArc: string): number {
    const positions = {
      'positive': -60,
      'negative': 60,
      'neutral': 0
    };
    return positions[emotionalArc] || 0;
  }

  // Create smooth SVG path
  private createSmoothPath(points: Array<{ x: number; y: number }>): string {
    if (points.length < 2) return '';

    let path = `M ${points[0].x} ${points[0].y}`;
    
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      
      // Create smooth curve
      const controlX = (prev.x + curr.x) / 2;
      path += ` Q ${controlX} ${prev.y} ${curr.x} ${curr.y}`;
    }
    
    return path;
  }

  // Validate seven-point structure
  validateStructure(nodes: Node[]): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
    metrics: {
      totalBeats: number;
      missingBeats: string[];
      emotionalBalance: number;
      coveragePercentage: number;
    };
  } {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    const beatNodes = nodes.filter(n => n.type.startsWith('seven-point-'));
    const requiredBeats = this.sevenPointBeats.map(b => b.title.toLowerCase().replace(/\s+/g, '-'));
    const existingBeats = beatNodes.map(n => n.id);
    const missingBeats = requiredBeats.filter(b => !existingBeats.includes(b));

    // Check for required beats
    if (missingBeats.length > 0) {
      warnings.push(`Missing beats: ${missingBeats.join(', ')}`);
    }

    // Check beat positions
    beatNodes.forEach(node => {
      const expectedBeat = this.sevenPointBeats.find(b => b.title.toLowerCase().replace(/\s+/g, '-') === node.id);
      if (expectedBeat) {
        const actualPosition = node.data.position || 0;
        if (Math.abs(actualPosition - expectedBeat.position) > 2) {
          warnings.push(`${expectedBeat.title} position should be ~${expectedBeat.position}%, got ${actualPosition}%`);
        }
      }
    });

    // Calculate emotional balance
    const positiveBeats = beatNodes.filter(n => n.data.emotionalArc === 'positive').length;
    const negativeBeats = beatNodes.filter(n => n.data.emotionalArc === 'negative').length;
    const emotionalBalance = positiveBeats - negativeBeats;

    // Calculate coverage
    const coveragePercentage = (existingBeats.length / requiredBeats.length) * 100;

    return {
      isValid: missingBeats.length === 0,
      errors,
      warnings,
      metrics: {
        totalBeats: existingBeats.length,
        missingBeats,
        emotionalBalance,
        coveragePercentage
      }
    };
  }

  // Auto-complete seven-point structure
  autoCompleteStructure(nodes: Node[]): { nodes: Node[]; edges: Edge[] } {
    const existingBeats = nodes.filter(n => n.type.startsWith('seven-point-'));
    const requiredBeats = this.sevenPointBeats;

    if (existingBeats.length === 7) {
      return { nodes: [], edges: [] };
    }

    const structure = this.createStructureLayout();
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    // Find missing beats
    const existingIds = existingBeats.map(b => b.id);
    const missingBeats = structure.beats.filter(b => !existingIds.includes(b.title.toLowerCase().replace(/\s+/g, '-')));

    // Create missing beats
    missingBeats.forEach(beat => {
      const nodeType = this.getBeatNodeType(beat.title);
      const node = createStoryNode(nodeType, beat.position, {
        beatType: beat.title.toLowerCase().replace(/\s+/g, '-'),
        title: beat.title,
        description: beat.description,
        position: beat.position,
        emotionalArc: beat.emotionalArc,
        importance: beat.importance
      });

      newNodes.push({ ...node, id: beat.title.toLowerCase().replace(/\s+/g, '-') });
    });

    // Create connections for new nodes
    if (newNodes.length > 0) {
      const connections = this.createBeatConnections(structure);
      newEdges.push(...connections.filter(edge => 
        newNodes.some(node => node.id === edge.source || node.id === edge.target)
      ));
    }

    return { nodes: newNodes, edges: newEdges };
  }

  // Interactive seven-point editor
  createInteractiveEditor(): {
    nodes: Node[];
    editor: {
      canAddBeat: boolean;
      canRemoveBeat: boolean;
      canModifyPosition: boolean;
    };
  } {
    const structure = this.createStructureLayout();
    const nodes = this.createBeatNodes(structure);

    return {
      nodes,
      editor: {
        canAddBeat: true,
        canRemoveBeat: true,
        canModifyPosition: true
      }
    };
  }

  // Get seven-point template
  getTemplate(): SevenPointStructure {
    return {
      beats: this.sevenPointBeats,
      connections: this.createConnections()
    };
  }

  // Calculate story pacing
  calculatePacing(nodes: Node[]): {
    pacing: Array<{
      beat: string;
      position: number;
      intensity: number;
      emotionalValue: number;
    }>;
    recommendedAdjustments: string[];
  } {
    const beatNodes = nodes.filter(n => n.type.startsWith('seven-point-'));
    const pacing = beatNodes.map(node => {
      const beat = this.sevenPointBeats.find(b => b.title.toLowerCase().replace(/\s+/g, '-') === node.id);
      if (!beat) return null;

      const intensity = this.calculateIntensity(beat);
      const emotionalValue = this.getEmotionalValue(beat.emotionalArc);

      return {
        beat: beat.title,
        position: node.data.position || beat.position,
        intensity,
        emotionalValue
      };
    }).filter(Boolean);

    const recommendedAdjustments = this.generatePacingRecommendations(pacing);

    return { pacing, recommendedAdjustments };
  }

  private calculateIntensity(beat: SevenPointBeat): number {
    const baseIntensity = {
      'Hook': 3,
      'Plot Turn 1': 7,
      'Pinch Point 1': 6,
      'Midpoint': 8,
      'Pinch Point 2': 6,
      'Plot Turn 2': 7,
      'Resolution': 10
    };
    
    return baseIntensity[beat.title] || 5;
  }

  private getEmotionalValue(emotionalArc: string): number {
    const values = {
      'positive': 1,
      'negative': -1,
      'neutral': 0
    };
    return values[emotionalArc] || 0;
  }

  private generatePacingRecommendations(pacing: any[]): string[] {
    const recommendations: string[] = [];
    
    if (pacing.length < 7) {
      recommendations.push('Consider adding missing beats for complete structure');
    }

    // Check for even distribution
    const positions = pacing.map(p => p.position).sort((a, b) => a - b);
    for (let i = 1; i < positions.length; i++) {
      const gap = positions[i] - positions[i - 1];
      if (gap < 10) {
        recommendations.push(`Consider spacing between ${pacing[i - 1].beat} and ${pacing[i].beat}`);
      }
    }

    return recommendations;
  }
}

// Export utility functions
export const sevenPointUtils = {
  // Quick seven-point structure creation
  createQuickStructure: (startPosition: { x: number; y: number }) => {
    const generator = new SevenPointStructureGenerator();
    return generator.generateStructure();
  },

  // Validate existing structure
  validateExisting: (nodes: Node[]) => {
    const generator = new SevenPointStructureGenerator();
    return generator.validateStructure(nodes);
  },

  // Auto-complete missing parts
  autoComplete: (nodes: Node[]) => {
    const generator = new SevenPointStructureGenerator();
    return generator.autoCompleteStructure(nodes);
  },

  // Get pacing analysis
  analyzePacing: (nodes: Node[]) => {
    const generator = new SevenPointStructureGenerator();
    return generator.calculatePacing(nodes);
  }
};