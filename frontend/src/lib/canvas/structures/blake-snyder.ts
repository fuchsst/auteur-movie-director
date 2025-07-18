import type { Node, Edge } from '$lib/canvas/types/canvas';
import { createStoryNode } from '$lib/canvas/nodes/story-nodes';
import { v4 as uuidv4 } from 'uuid';

// Blake Snyder Beat Sheet (Save the Cat) implementation

export interface BlakeSnyderBeat {
  beat: string;
  title: string;
  description: string;
  page: number;
  percentage: number;
  category: 'setup' | 'confrontation' | 'resolution';
  emotionalArc: 'positive' | 'negative' | 'neutral';
  saveTheCat?: boolean; // Special beats that follow Save the Cat methodology
}

export interface BlakeSnyderStructure {
  beats: BlakeSnyderBeat[];
  theme: string;
  logline: string;
  genre: string;
  connections: Array<{
    source: string;
    target: string;
    type: 'story-flow' | 'theme-flow' | 'character-arc';
  }>;
}

export class BlakeSnyderStructureGenerator {
  private canvasWidth: number;
  private canvasHeight: number;
  private padding: number;

  constructor(
    canvasWidth: number = 1400,
    canvasHeight: number = 800,
    padding: number = 100
  ) {
    this.canvasWidth = canvasWidth;
    this.canvasHeight = canvasHeight;
    this.padding = padding;
  }

  // Complete 15-beat Blake Snyder structure
  private blakeSnyderBeats: BlakeSnyderBeat[] = [
    {
      beat: 'opening-image',
      title: 'Opening Image',
      description: 'The first impression - a visual representation of the "Before" state',
      page: 1,
      percentage: 0,
      category: 'setup',
      emotionalArc: 'neutral',
      saveTheCat: true
    },
    {
      beat: 'theme-stated',
      title: 'Theme Stated',
      description: 'What the story is about - stated as a question or challenge',
      page: 5,
      percentage: 4.5,
      category: 'setup',
      emotionalArc: 'neutral'
    },
    {
      beat: 'set-up',
      title: 'Setup',
      description: 'The first 10% - introduce world, characters, stakes, and flaws',
      page: 1,
      percentage: 10,
      category: 'setup',
      emotionalArc: 'neutral',
      saveTheCat: true
    },
    {
      beat: 'catalyst',
      title: 'Catalyst',
      description: 'The life-changing event - the telegram, the knock on the door',
      page: 12,
      percentage: 10.9,
      category: 'setup',
      emotionalArc: 'positive',
      saveTheCat: true
    },
    {
      beat: 'debate',
      title: 'Debate',
      description: 'The last chance to back out - "Should I go?"',
      page: 12,
      percentage: 20,
      category: 'setup',
      emotionalArc: 'negative'
    },
    {
      beat: 'break-into-2',
      title: 'Break into 2',
      description: 'The hero enters the upside-down world of Act 2',
      page: 25,
      percentage: 22.7,
      category: 'confrontation',
      emotionalArc: 'positive',
      saveTheCat: true
    },
    {
      beat: 'b-story',
      title: 'B Story',
      description: 'The love story or secondary plot - often the "helper" arrives',
      page: 30,
      percentage: 27.3,
      category: 'confrontation',
      emotionalArc: 'positive'
    },
    {
      beat: 'fun-and-games',
      title: 'Fun and Games',
      description: 'The promise of the premise - delivers on what the poster promised',
      page: 30,
      percentage: 50,
      category: 'confrontation',
      emotionalArc: 'positive',
      saveTheCat: true
    },
    {
      beat: 'midpoint',
      title: 'Midpoint',
      description: 'Either false victory or false defeat - stakes are raised',
      page: 55,
      percentage: 50,
      category: 'confrontation',
      emotionalArc: 'neutral',
      saveTheCat: true
    },
    {
      beat: 'bad-guys-close-in',
      title: 'Bad Guys Close In',
      description: 'The bad guys regroup and the hero\'s team starts to fall apart',
      page: 55,
      percentage: 68.2,
      category: 'confrontation',
      emotionalArc: 'negative'
    },
    {
      beat: 'all-is-lost',
      title: 'All Is Lost',
      description: 'The opposite of the Midpoint - the whiff of death',
      page: 75,
      percentage: 68.2,
      category: 'confrontation',
      emotionalArc: 'negative',
      saveTheCat: true
    },
    {
      beat: 'dark-night-of-the-soul',
      title: 'Dark Night of the Soul',
      description: 'The hero\'s darkest moment - "Why did this happen to me?"',
      page: 75,
      percentage: 77.3,
      category: 'confrontation',
      emotionalArc: 'negative'
    },
    {
      beat: 'break-into-3',
      title: 'Break into 3',
      description: 'The hero finds the solution - thanks to the B Story characters',
      page: 85,
      percentage: 77.3,
      category: 'resolution',
      emotionalArc: 'positive',
      saveTheCat: true
    },
    {
      beat: 'finale',
      title: 'Finale',
      description: 'The hero executes the plan - storming the castle',
      page: 85,
      percentage: 95.5,
      category: 'resolution',
      emotionalArc: 'positive',
      saveTheCat: true
    },
    {
      beat: 'final-image',
      title: 'Final Image',
      description: 'The opposite of the Opening Image - proof that change has occurred',
      page: 110,
      percentage: 100,
      category: 'resolution',
      emotionalArc: 'positive',
      saveTheCat: true
    }
  ];

  // Generate complete Blake Snyder structure
  generateStructure(theme: string = '', logline: string = '', genre: string = 'drama'): { nodes: Node[]; edges: Edge[] } {
    const structure = this.createStructureLayout(theme, logline, genre);
    const nodes = this.createBeatNodes(structure);
    const edges = this.createBeatConnections(structure);

    return { nodes, edges };
  }

  // Create Blake Snyder structure layout
  private createStructureLayout(
    theme: string,
    logline: string,
    genre: string
  ): BlakeSnyderStructure {
    const availableWidth = this.canvasWidth - (2 * this.padding);
    const startX = this.padding;
    const centerY = this.canvasHeight / 2;

    // Position beats along timeline
    const positionedBeats = this.blakeSnyderBeats.map(beat => ({
      ...beat,
      position: {
        x: startX + (beat.percentage / 100) * availableWidth,
        y: this.calculateBeatY(beat, genre)
      }
    }));

    return {
      beats: positionedBeats,
      theme,
      logline,
      genre,
      connections: this.createConnections()
    };
  }

  // Calculate Y position based on beat type and genre
  private calculateBeatY(beat: BlakeSnyderBeat, genre: string): number {
    const baseY = this.canvasHeight / 2;
    const genreOffsets = {
      'comedy': { setup: -100, confrontation: 0, resolution: -50 },
      'drama': { setup: -80, confrontation: 0, resolution: -80 },
      'action': { setup: -120, confrontation: 20, resolution: -100 },
      'romance': { setup: -60, confrontation: 0, resolution: -120 },
      'thriller': { setup: -100, confrontation: 50, resolution: -80 }
    };

    const offset = genreOffsets[genre]?.[beat.category] || 0;
    const emotionalOffset = this.getEmotionalOffset(beat.emotionalArc);
    
    return baseY + offset + emotionalOffset;
  }

  // Get emotional arc offset
  private getEmotionalOffset(emotionalArc: string): number {
    const offsets = {
      'positive': -20,
      'negative': 20,
      'neutral': 0
    };
    return offsets[emotionalArc] || 0;
  }

  // Create beat connections
  private createConnections(): BlakeSnyderStructure['connections'] {
    return [
      // Story flow connections
      { source: 'opening-image', target: 'theme-stated', type: 'story-flow' },
      { source: 'theme-stated', target: 'set-up', type: 'story-flow' },
      { source: 'set-up', target: 'catalyst', type: 'story-flow' },
      { source: 'catalyst', target: 'debate', type: 'story-flow' },
      { source: 'debate', target: 'break-into-2', type: 'story-flow' },
      { source: 'break-into-2', target: 'b-story', type: 'story-flow' },
      { source: 'b-story', target: 'fun-and-games', type: 'story-flow' },
      { source: 'fun-and-games', target: 'midpoint', type: 'story-flow' },
      { source: 'midpoint', target: 'bad-guys-close-in', type: 'story-flow' },
      { source: 'bad-guys-close-in', target: 'all-is-lost', type: 'story-flow' },
      { source: 'all-is-lost', target: 'dark-night-of-the-soul', type: 'story-flow' },
      { source: 'dark-night-of-the-soul', target: 'break-into-3', type: 'story-flow' },
      { source: 'break-into-3', target: 'finale', type: 'story-flow' },
      { source: 'finale', target: 'final-image', type: 'story-flow' },
      
      // Theme flow connections
      { source: 'theme-stated', target: 'finale', type: 'theme-flow' },
      { source: 'opening-image', target: 'final-image', type: 'theme-flow' },
      
      // Character arc connections
      { source: 'set-up', target: 'break-into-3', type: 'character-arc' }
    ];
  }

  // Create beat nodes
  private createBeatNodes(structure: BlakeSnyderStructure): Node[] {
    return structure.beats.map(beat => {
      const nodeType = this.getBeatNodeType(beat.beat);
      const node = createStoryNode(nodeType, beat.position, {
        beat: beat.beat,
        title: beat.title,
        description: beat.description,
        page: beat.page,
        percentage: beat.percentage,
        category: beat.category,
        emotionalArc: beat.emotionalArc,
        saveTheCat: beat.saveTheCat || false
      });

      return {
        ...node,
        id: beat.beat,
        style: {
          ...node.style,
          backgroundColor: this.getBeatColor(beat),
          borderRadius: '12px',
          padding: '10px',
          minWidth: '120px',
          textAlign: 'center',
          border: beat.saveTheCat ? '2px solid #f59e0b' : 'none'
        }
      };
    });
  }

  // Get beat node type
  private getBeatNodeType(beat: string): string {
    return `blake-${beat}`;
  }

  // Get color based on beat type and category
  private getBeatColor(beat: BlakeSnyderBeat): string {
    const categoryColors = {
      'setup': '#8b5cf6',
      'confrontation': '#f97316',
      'resolution': '#10b981'
    };
    
    const emotionalColors = {
      'positive': '#10b981',
      'negative': '#ef4444',
      'neutral': '#3b82f6'
    };

    // Use category color as base, emotional color as accent
    const baseColor = categoryColors[beat.category] || '#6b7280';
    return baseColor;
  }

  // Create beat connections
  private createBeatConnections(structure: BlakeSnyderStructure): Edge[] {
    const edges: Edge[] = [];

    structure.connections.forEach(connection => {
      const edge: Edge = {
        id: uuidv4(),
        source: connection.source,
        target: connection.target,
        type: this.getConnectionType(connection.type),
        animated: connection.type === 'story-flow',
        style: {
          stroke: this.getConnectionColor(connection.type),
          strokeWidth: this.getConnectionWidth(connection.type),
          strokeDasharray: this.getConnectionDash(connection.type)
        },
        data: {
          type: connection.type,
          label: this.getConnectionLabel(connection.type)
        }
      };

      edges.push(edge);
    });

    return edges;
  }

  // Get connection type
  private getConnectionType(type: string): string {
    const typeMap = {
      'story-flow': 'smoothstep',
      'theme-flow': 'straight',
      'character-arc': 'step'
    };
    return typeMap[type] || 'smoothstep';
  }

  // Get connection color
  private getConnectionColor(type: string): string {
    const colors = {
      'story-flow': '#3b82f6',
      'theme-flow': '#8b5cf6',
      'character-arc': '#10b981'
    };
    return colors[type] || '#6b7280';
  }

  // Get connection width
  private getConnectionWidth(type: string): number {
    const widths = {
      'story-flow': 2,
      'theme-flow': 1,
      'character-arc': 1
    };
    return widths[type] || 1;
  }

  // Get connection dash pattern
  private getConnectionDash(type: string): string | undefined {
    const dashes = {
      'story-flow': undefined,
      'theme-flow': '5,5',
      'character-arc': '10,5'
    };
    return dashes[type];
  }

  // Get connection label
  private getConnectionLabel(type: string): string {
    const labels = {
      'story-flow': 'Story Flow',
      'theme-flow': 'Theme',
      'character-arc': 'Character Arc'
    };
    return labels[type] || '';
  }

  // Generate Save the Cat worksheet
  generateWorksheet(): {
    beats: Array<{
      beat: string;
      page: number;
      question: string;
      example: string;
    }>;
    genreGuidelines: Record<string, Array<string>>;
  } {
    const worksheet = this.blakeSnyderBeats.map(beat => ({
      beat: beat.title,
      page: beat.page,
      question: this.getBeatQuestion(beat.beat),
      example: this.getBeatExample(beat.beat)
    }));

    const genreGuidelines = {
      'comedy': ['Use humor in setup', 'Heighten absurdity in confrontation', 'Restore order in resolution'],
      'drama': ['Establish emotional stakes', 'Deepen conflict', 'Provide catharsis'],
      'action': ['Set up stakes quickly', 'Escalate threats', 'Deliver satisfying climax'],
      'romance': ['Meet cute', 'Complications', 'Happy ever after'],
      'thriller': ['Establish tension', 'Increase danger', 'Reveal truth']
    };

    return { beats: worksheet, genreGuidelines };
  }

  // Get beat-specific questions
  private getBeatQuestion(beat: string): string {
    const questions = {
      'opening-image': 'What visual instantly shows your hero\'s "before" state?',
      'theme-stated': 'What is your story\'s central question or moral?',
      'set-up': 'What are your hero\'s flaws and the stakes?',
      'catalyst': 'What life-changing event occurs?',
      'debate': 'What internal conflict does your hero face?',
      'break-into-2': 'What choice does your hero make to enter the new world?',
      'b-story': 'Who/what is your love story/helper?',
      'fun-and-games': 'What\'s the promise of your premise?',
      'midpoint': 'What false victory or defeat occurs?',
      'bad-guys-close-in': 'How do the antagonists regroup?',
      'all-is-lost': 'What is the hero\'s darkest moment?',
      'dark-night-of-the-soul': 'What realization does the hero have?',
      'break-into-3': 'What solution does the hero find?',
      'finale': 'How does the hero execute the final plan?',
      'final-image': 'What visual shows the hero\'s "after" state?'
    };
    return questions[beat] || 'What happens here?';
  }

  // Get beat examples
  private getBeatExample(beat: string): string {
    const examples = {
      'opening-image': 'Indiana Jones running from the boulder',
      'theme-stated': '\"With great power comes great responsibility\"',
      'set-up': 'Luke Skywalker on Tatooine, wanting adventure',
      'catalyst': 'Princess Leia\'s message',
      'debate': 'Luke\'s reluctance to leave home',
      'break-into-2': 'Luke decides to join Obi-Wan',
      'b-story': 'Han Solo and Leia\'s relationship',
      'fun-and-games': 'The Millennium Falcon chase',
      'midpoint': 'Escape from the trash compactor',
      'bad-guys-close-in': 'Vader\'s pursuit of the Falcon',
      'all-is-lost': 'Obi-Wan\'s death',
      'dark-night-of-the-soul': 'Luke\'s grief over Obi-Wan',
      'break-into-3': 'Luke trusts the Force',
      'finale': 'The Death Star trench run',
      'final-image': 'Luke, Han, and Leia receiving medals'
    };
    return examples[beat] || 'Example needed';
  }

  // Validate Blake Snyder structure
  validateStructure(nodes: Node[]): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
    metrics: {
      totalBeats: number;
      missingBeats: string[];
      pageDistribution: Array<{
        beat: string;
        actualPage: number;
        expectedPage: number;
        deviation: number;
      }>;
      saveTheCatCompletion: number;
    };
  } {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    const beatNodes = nodes.filter(n => n.type.startsWith('blake-'));
    const requiredBeats = this.blakeSnyderBeats.map(b => b.beat);
    const existingBeats = beatNodes.map(n => n.id);
    const missingBeats = requiredBeats.filter(b => !existingBeats.includes(b));

    // Check for required beats
    if (missingBeats.length > 0) {
      warnings.push(`Missing beats: ${missingBeats.join(', ')}`);
    }

    // Check page distribution
    const pageDistribution = beatNodes.map(node => {
      const expectedBeat = this.blakeSnyderBeats.find(b => b.beat === node.id);
      if (!expectedBeat) return null;

      const actualPage = node.data.page || expectedBeat.page;
      const deviation = Math.abs(actualPage - expectedBeat.page);

      return {
        beat: expectedBeat.title,
        actualPage,
        expectedPage: expectedBeat.page,
        deviation
      };
    }).filter(Boolean);

    // Check for large deviations
    pageDistribution.forEach(dist => {
      if (dist.deviation > 5) {
        warnings.push(`${dist.beat} deviates ${dist.deviation} pages from expected position`);
      }
    });

    // Calculate Save the Cat completion
    const saveTheCatBeats = this.blakeSnyderBeats.filter(b => b.saveTheCat).map(b => b.beat);
    const presentSaveTheCatBeats = saveTheCatBeats.filter(b => existingBeats.includes(b));
    const saveTheCatCompletion = (presentSaveTheCatBeats.length / saveTheCatBeats.length) * 100;

    return {
      isValid: missingBeats.length === 0,
      errors,
      warnings,
      metrics: {
        totalBeats: existingBeats.length,
        missingBeats,
        pageDistribution: pageDistribution as any,
        saveTheCatCompletion
      }
    };
  }

  // Auto-complete Blake Snyder structure
  autoCompleteStructure(
    nodes: Node[],
    theme: string = '',
    logline: string = '',
    genre: string = 'drama'
  ): { nodes: Node[]; edges: Edge[] } {
    const existingBeats = nodes.filter(n => n.type.startsWith('blake-'));
    const requiredBeats = this.blakeSnyderBeats;

    if (existingBeats.length === 15) {
      return { nodes: [], edges: [] };
    }

    const structure = this.createStructureLayout(theme, logline, genre);
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    // Find missing beats
    const existingIds = existingBeats.map(b => b.id);
    const missingBeats = structure.beats.filter(b => !existingIds.includes(b.beat));

    // Create missing beats
    missingBeats.forEach(beat => {
      const nodeType = this.getBeatNodeType(beat.beat);
      const node = createStoryNode(nodeType, beat.position, {
        beat: beat.beat,
        title: beat.title,
        description: beat.description,
        page: beat.page,
        percentage: beat.percentage,
        category: beat.category,
        emotionalArc: beat.emotionalArc,
        saveTheCat: beat.saveTheCat || false
      });

      newNodes.push({ ...node, id: beat.beat });
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

  // Interactive Blake Snyder editor
  createInteractiveEditor(): {
    nodes: Node[];
    editor: {
      canAddBeat: boolean;
      canRemoveBeat: boolean;
      canAdjustPages: boolean;
      hasThemeSupport: boolean;
    };
  } {
    const structure = this.createStructureLayout('', '', 'drama');
    const nodes = this.createBeatNodes(structure);

    return {
      nodes,
      editor: {
        canAddBeat: false, // All 15 beats are required
        canRemoveBeat: false, // All 15 beats are required
        canAdjustPages: true,
        hasThemeSupport: true
      }
    };
  }

  // Get Blake Snyder template
  getTemplate(theme?: string, logline?: string, genre?: string): BlakeSnyderStructure {
    return this.createStructureLayout(theme || '', logline || '', genre || 'drama');
  }

  // Generate genre-specific guidelines
  generateGenreGuidelines(genre: string): {
    beats: Array<{
      beat: string;
      genreSpecific: string;
      examples: string[];
    }>;
    tips: string[];
  } {
    const genreGuidelines = {
      'comedy': {
        'opening-image': 'Set up the comedic world - establish the "normal" that will be disrupted',
        'theme-stated': 'State the moral as a joke or ironic observation',
        'fun-and-games': 'Heighten the absurdity - deliver on the comedy premise',
        'finale': 'Resolve with maximum comedic payoff'
      },
      'action': {
        'opening-image': 'Start with action - establish the hero\'s skills',
        'catalyst': 'Raise the stakes immediately',
        'fun-and-games': 'Showcase action sequences',
        'finale': 'Climax with the biggest action set piece'
      },
      'romance': {
        'opening-image': 'Establish the "single" world',
        'b-story': 'Introduce the love interest',
        'midpoint': 'First kiss or major romantic development',
        'final-image': 'Happy couple together'
      },
      'thriller': {
        'opening-image': 'Create immediate tension',
        'bad-guys-close-in': 'Escalate the danger',
        'all-is-lost': 'Maximum threat level',
        'finale': 'Hero outsmarts the antagonist'
      }
    };

    const guidelines = genreGuidelines[genre] || {};
    const beats = Object.entries(guidelines).map(([beat, guide]) => ({
      beat: this.blakeSnyderBeats.find(b => b.beat === beat)?.title || beat,
      genreSpecific: guide,
      examples: this.getGenreExamples(beat, genre)
    }));

    const tips = this.getGenreTips(genre);

    return { beats, tips };
  }

  private getGenreExamples(beat: string, genre: string): string[] {
    const examples = {
      'comedy': {
        'fun-and-games': ['Montage of failed attempts', 'Fish-out-of-water scenarios', 'Running gags'],
        'finale': ['Wedding chaos', 'Race against time', 'Big reveal']
      },
      'action': {
        'fun-and-games': ['Training sequences', 'Minor victories', 'Cool gadgets'],
        'finale': ['Final showdown', 'One-liner moments', 'Explosive climax']
      }
    };

    return examples[genre]?.[beat] || ['Scene examples needed'];
  }

  private getGenreTips(genre: string): string[] {
    const tips = {
      'comedy': [
        'Use the "fun and games" section for maximum laughs',
        'Make the stakes personal and relatable',
        'End with emotional truth beneath the humor'
      ],
      'action': [
        'Start with a bang',
        'Escalate threats progressively',
        'Give the hero personal stakes'
      ],
      'romance': [
        'Chemistry is key in the B-story',
        'Use external conflict to test the relationship',
        'Earn your happy ending'
      ],
      'thriller': [
        'Keep the audience guessing',
        'Use misdirection wisely',
        'Tighten the screws gradually'
      ]
    };

    return tips[genre] || ['Follow standard Save the Cat structure'];
  }

  // Calculate story arc visualization
  generateArcVisualization(): {
    path: string;
    peaks: Array<{
      beat: string;
      x: number;
      y: number;
      intensity: number;
    }>;
  } {
    const availableWidth = this.canvasWidth - (2 * this.padding);
    const startX = this.padding;
    const centerY = this.canvasHeight / 2;

    const peaks = this.blakeSnyderBeats.map(beat => ({
      beat: beat.title,
      x: startX + (beat.percentage / 100) * availableWidth,
      y: centerY + this.getIntensityY(beat),
      intensity: this.getIntensity(beat)
    }));

    const path = this.createDramaticArc(peaks);

    return { path, peaks };
  }

  private getIntensityY(beat: BlakeSnyderBeat): number {
    const intensities = {
      'opening-image': -30,
      'theme-stated': -20,
      'set-up': -40,
      'catalyst': 20,
      'debate': 10,
      'break-into-2': 30,
      'b-story': 20,
      'fun-and-games': 40,
      'midpoint': 60,
      'bad-guys-close-in': 50,
      'all-is-lost': -60,
      'dark-night-of-the-soul': -50,
      'break-into-3': 20,
      'finale': 80,
      'final-image': -20
    };
    return intensities[beat.beat] || 0;
  }

  private getIntensity(beat: BlakeSnyderBeat): number {
    const intensities = {
      'opening-image': 2,
      'theme-stated': 1,
      'set-up': 3,
      'catalyst': 7,
      'debate': 5,
      'break-into-2': 8,
      'b-story': 4,
      'fun-and-games': 6,
      'midpoint': 9,
      'bad-guys-close-in': 7,
      'all-is-lost': 10,
      'dark-night-of-the-soul': 8,
      'break-into-3': 9,
      'finale': 10,
      'final-image': 3
    };
    return intensities[beat.beat] || 5;
  }

  private createDramaticArc(peaks: Array<{ x: number; y: number }>): string {
    if (peaks.length < 2) return '';

    let path = `M ${peaks[0].x} ${peaks[0].y}`;
    
    for (let i = 1; i < peaks.length; i++) {
      const prev = peaks[i - 1];
      const curr = peaks[i];
      
      // Create smooth curve with control points
      const cp1x = prev.x + (curr.x - prev.x) * 0.3;
      const cp1y = prev.y;
      const cp2x = prev.x + (curr.x - prev.x) * 0.7;
      const cp2y = curr.y;
      
      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
    }
    
    return path;
  }
}

// Export utility functions
export const blakeSnyderUtils = {
  // Quick Blake Snyder structure creation
  createQuickStructure: (
    theme: string = '',
    logline: string = '',
    genre: string = 'drama'
  ) => {
    const generator = new BlakeSnyderStructureGenerator();
    return generator.generateStructure(theme, logline, genre);
  },

  // Validate existing structure
  validateExisting: (nodes: Node[]) => {
    const generator = new BlakeSnyderStructureGenerator();
    return generator.validateStructure(nodes);
  },

  // Auto-complete missing parts
  autoComplete: (
    nodes: Node[],
    theme: string = '',
    logline: string = '',
    genre: string = 'drama'
  ) => {
    const generator = new BlakeSnyderStructureGenerator();
    return generator.autoCompleteStructure(nodes, theme, logline, genre);
  },

  // Get genre-specific guidelines
  getGenreGuidelines: (genre: string) => {
    const generator = new BlakeSnyderStructureGenerator();
    return generator.generateGenreGuidelines(genre);
  },

  // Get Save the Cat worksheet
  getWorksheet: () => {
    const generator = new BlakeSnyderStructureGenerator();
    return generator.generateWorksheet();
  }
};