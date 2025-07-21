import { canvasStore } from '$lib/canvas/core/canvas-store';
import { ThreeActStructureGenerator } from '$lib/canvas/structures/three-act';
import { SevenPointStructureGenerator } from '$lib/canvas/structures/seven-point';
import { BlakeSnyderStructureGenerator } from '$lib/canvas/structures/blake-snyder';
import type { ProjectData } from '$lib/types/project';
import type { Node, Edge } from '$lib/canvas/types/canvas';

export interface PopulationOptions {
  structureType: 'three-act' | 'seven-point' | 'blake-snyder' | 'auto';
  includeAssets: boolean;
  includeScenes: boolean;
  includeShots: boolean;
  autoLayout: boolean;
  startPosition: { x: number; y: number };
  quality: 'low' | 'standard' | 'high';
}

export interface PopulationResult {
  nodes: Node[];
  edges: Edge[];
  warnings: string[];
  metadata: {
    structureType: string;
    nodeCount: number;
    assetCount: number;
    sceneCount: number;
    shotCount: number;
  };
}

export class CanvasPopulationService {
  private structureGenerators = {
    'three-act': new ThreeActStructureGenerator(),
    'seven-point': new SevenPointStructureGenerator(),
    'blake-snyder': new BlakeSnyderStructureGenerator()
  };

  async populateFromProject(
    project: ProjectData,
    options: PopulationOptions
  ): Promise<PopulationResult> {
    const warnings: string[] = [];
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    try {
      // Determine structure type if auto
      const structureType = options.structureType === 'auto' 
        ? this.detectStructureType(project)
        : options.structureType;

      // Generate story structure
      const structureResult = await this.generateStoryStructure(
        project,
        structureType,
        options.startPosition
      );
      
      nodes.push(...structureResult.nodes);
      edges.push(...structureResult.edges);

      // Add assets if requested
      if (options.includeAssets) {
        const assetResult = await this.addAssetNodes(project, structureResult.nodes);
        nodes.push(...assetResult.nodes);
        edges.push(...assetResult.edges);
      }

      // Add scenes if requested
      if (options.includeScenes) {
        const sceneResult = await this.addSceneNodes(project, structureResult.nodes);
        nodes.push(...sceneResult.nodes);
        edges.push(...sceneResult.edges);
      }

      // Add shots if requested
      if (options.includeShots) {
        const shotResult = await this.addShotNodes(project, structureResult.nodes);
        nodes.push(...shotResult.nodes);
        edges.push(...shotResult.edges);
      }

      // Auto-layout if requested
      if (options.autoLayout) {
        const layoutResult = await this.autoLayout(nodes, edges);
        return {
          nodes: layoutResult.nodes,
          edges: layoutResult.edges,
          warnings,
          metadata: {
            structureType,
            nodeCount: nodes.length,
            assetCount: assetResult?.nodes.length || 0,
            sceneCount: sceneResult?.nodes.length || 0,
            shotCount: shotResult?.nodes.length || 0
          }
        };
      }

      return {
        nodes,
        edges,
        warnings,
        metadata: {
          structureType,
          nodeCount: nodes.length,
          assetCount: 0,
          sceneCount: 0,
          shotCount: 0
        }
      };

    } catch (error) {
      warnings.push(`Population failed: ${error.message}`);
      return {
        nodes: [],
        edges: [],
        warnings,
        metadata: {
          structureType: 'none',
          nodeCount: 0,
          assetCount: 0,
          sceneCount: 0,
          shotCount: 0
        }
      };
    }
  }

  private detectStructureType(project: ProjectData): 'three-act' | 'seven-point' | 'blake-snyder' {
    // Analyze project structure to determine best fit
    const storyData = project.story || {};
    
    // Check for Blake Snyder indicators
    if (storyData.blakeSnyderBeats && Object.keys(storyData.blakeSnyderBeats).length > 0) {
      return 'blake-snyder';
    }
    
    // Check for Seven Point indicators
    if (storyData.sevenPointStructure && storyData.sevenPointStructure.length >= 7) {
      return 'seven-point';
    }
    
    // Default to Three Act
    return 'three-act';
  }

  private async generateStoryStructure(
    project: ProjectData,
    structureType: string,
    startPosition: { x: number; y: number }
  ): Promise<{ nodes: Node[]; edges: Edge[] }> {
    const generator = this.structureGenerators[structureType];
    if (!generator) {
      throw new Error(`Unknown structure type: ${structureType}`);
    }

    const result = generator.generateStructure({
      title: project.title,
      genre: project.genre || 'Drama',
      theme: project.theme || '',
      logline: project.logline || '',
      startPosition
    });

    return result;
  }

  private async addAssetNodes(
    project: ProjectData,
    storyNodes: Node[]
  ): Promise<{ nodes: Node[]; edges: Edge[] }> {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Add character assets
    if (project.characters && project.characters.length > 0) {
      project.characters.forEach((character, index) => {
        const characterNode: Node = {
          id: `character-${character.id}`,
          type: 'character-asset',
          position: { x: -300, y: 100 + (index * 100) },
          data: {
            character,
            name: character.name,
            imageUrl: character.thumbnail,
            type: 'character'
          },
          selected: false,
          dragging: false,
          measured: { width: 200, height: 120 }
        };
        nodes.push(characterNode);
      });
    }

    // Add style assets
    if (project.styles && project.styles.length > 0) {
      project.styles.forEach((style, index) => {
        const styleNode: Node = {
          id: `style-${style.id}`,
          type: 'style-asset',
          position: { x: -300, y: 400 + (index * 100) },
          data: {
            style,
            name: style.name,
            preview: style.preview,
            type: 'style'
          },
          selected: false,
          dragging: false,
          measured: { width: 200, height: 120 }
        };
        nodes.push(styleNode);
      });
    }

    return { nodes, edges };
  }

  private async addSceneNodes(
    project: ProjectData,
    storyNodes: Node[]
  ): Promise<{ nodes: Node[]; edges: Edge[] }> {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // This would integrate with scene data from the project
    // For now, create placeholder scenes based on story structure
    const actNodes = storyNodes.filter(node => node.type === 'act');
    
    actNodes.forEach((actNode, actIndex) => {
      // Create 2-3 scenes per act
      for (let i = 0; i < 3; i++) {
        const sceneNode: Node = {
          id: `scene-${actIndex}-${i}`,
          type: 'scene',
          position: {
            x: actNode.position.x + 200,
            y: actNode.position.y + (i * 150)
          },
          data: {
            title: `Scene ${i + 1}`,
            description: `Scene ${i + 1} of Act ${actIndex + 1}`,
            actId: actNode.id
          },
          selected: false,
          dragging: false,
          measured: { width: 180, height: 100 }
        };
        nodes.push(sceneNode);

        // Connect to act
        edges.push({
          id: `edge-act-${actNode.id}-scene-${sceneNode.id}`,
          source: actNode.id,
          target: sceneNode.id,
          type: 'smoothstep',
          animated: false,
          selected: false
        });
      }
    });

    return { nodes, edges };
  }

  private async addShotNodes(
    project: ProjectData,
    storyNodes: Node[]
  ): Promise<{ nodes: Node[]; edges: Edge[] }> {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    const sceneNodes = storyNodes.filter(node => node.type === 'scene');
    
    sceneNodes.forEach((sceneNode) => {
      // Create 2-4 shots per scene
      const shotCount = Math.floor(Math.random() * 3) + 2;
      for (let i = 0; i < shotCount; i++) {
        const shotNode: Node = {
          id: `shot-${sceneNode.id}-${i}`,
          type: 'shot',
          position: {
            x: sceneNode.position.x + 250,
            y: sceneNode.position.y + (i * 80)
          },
          data: {
            title: `Shot ${i + 1}`,
            description: `Shot ${i + 1} of ${sceneNode.data.title}`,
            sceneId: sceneNode.id,
            duration: Math.floor(Math.random() * 30) + 10
          },
          selected: false,
          dragging: false,
          measured: { width: 160, height: 60 }
        };
        nodes.push(shotNode);

        // Connect to scene
        edges.push({
          id: `edge-scene-${sceneNode.id}-shot-${shotNode.id}`,
          source: sceneNode.id,
          target: shotNode.id,
          type: 'smoothstep',
          animated: false,
          selected: false
        });
      }
    });

    return { nodes, edges };
  }

  private async autoLayout(
    nodes: Node[],
    edges: Edge[]
  ): Promise<{ nodes: Node[]; edges: Edge[] }> {
    // Simple hierarchical layout
    const levels = this.calculateLevels(nodes, edges);
    const spacing = { x: 300, y: 150 };
    const startX = 100;
    const startY = 100;

    const updatedNodes = nodes.map(node => {
      const level = levels.get(node.id) || 0;
      const siblings = Array.from(levels.entries())
        .filter(([_, l]) => l === level)
        .map(([id]) => id);
      const index = siblings.indexOf(node.id);

      return {
        ...node,
        position: {
          x: startX + (level * spacing.x),
          y: startY + (index * spacing.y)
        }
      };
    });

    return { nodes: updatedNodes, edges };
  }

  private calculateLevels(nodes: Node[], edges: Edge[]): Map<string, number> {
    const levels = new Map<string, number>();
    const visited = new Set<string>();
    const adjacencyList = new Map<string, string[]>();

    // Build adjacency list
    edges.forEach(edge => {
      if (!adjacencyList.has(edge.source)) {
        adjacencyList.set(edge.source, []);
      }
      adjacencyList.get(edge.source)!.push(edge.target);
    });

    // Find root nodes (nodes with no incoming edges)
    const rootNodes = nodes.filter(node => 
      !edges.some(edge => edge.target === node.id)
    );

    // Perform level assignment
    const queue: Array<{ id: string; level: number }> = [];
    rootNodes.forEach(node => {
      queue.push({ id: node.id, level: 0 });
      levels.set(node.id, 0);
    });

    while (queue.length > 0) {
      const { id, level } = queue.shift()!;
      if (visited.has(id)) continue;
      visited.add(id);

      const children = adjacencyList.get(id) || [];
      children.forEach(childId => {
        if (!visited.has(childId)) {
          levels.set(childId, level + 1);
          queue.push({ id: childId, level: level + 1 });
        }
      });
    }

    return levels;
  }
}

export const canvasPopulationService = new CanvasPopulationService();