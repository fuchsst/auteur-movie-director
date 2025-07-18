export interface DisclosureLevel {
  id: string;
  name: string;
  description: string;
  minZoom: number;
  maxZoom: number;
  features: string[];
  nodeVisibility: Record<string, boolean>;
  edgeVisibility: Record<string, boolean>;
  uiElements: string[];
}

export interface ProgressiveDisclosureConfig {
  levels: DisclosureLevel[];
  currentLevel: string;
  autoAdjust: boolean;
  customRules: Record<string, any>;
}

export class ProgressiveDisclosureService {
  private config: ProgressiveDisclosureConfig;
  private listeners: Array<(level: DisclosureLevel) => void> = [];

  constructor() {
    this.config = {
      levels: [
        {
          id: 'beginner',
          name: 'Beginner',
          description: 'Simple story structure with basic nodes',
          minZoom: 0.1,
          maxZoom: 0.5,
          features: ['basic-nodes', 'simple-edges', 'drag-drop'],
          nodeVisibility: {
            'act': true,
            'scene': true,
            'character-asset': false,
            'style-asset': false,
            'shot': false,
            'effect': false,
            'audio': false
          },
          edgeVisibility: {
            'default': true,
            'animated': false,
            'custom': false
          },
          uiElements: ['toolbar', 'minimap', 'basic-controls']
        },
        {
          id: 'intermediate',
          name: 'Intermediate',
          description: 'Standard story structure with assets',
          minZoom: 0.3,
          maxZoom: 1.0,
          features: ['all-nodes', 'custom-edges', 'properties-panel', 'undo-redo'],
          nodeVisibility: {
            'act': true,
            'scene': true,
            'character-asset': true,
            'style-asset': true,
            'shot': true,
            'effect': false,
            'audio': false
          },
          edgeVisibility: {
            'default': true,
            'animated': true,
            'custom': true
          },
          uiElements: ['toolbar', 'minimap', 'controls', 'properties-panel']
        },
        {
          id: 'advanced',
          name: 'Advanced',
          description: 'Full feature set with advanced tools',
          minZoom: 0.5,
          maxZoom: 2.0,
          features: ['all-nodes', 'all-edges', 'advanced-tools', 'customization'],
          nodeVisibility: {
            'act': true,
            'scene': true,
            'character-asset': true,
            'style-asset': true,
            'shot': true,
            'effect': true,
            'audio': true
          },
          edgeVisibility: {
            'default': true,
            'animated': true,
            'custom': true
          },
          uiElements: ['toolbar', 'minimap', 'controls', 'properties-panel', 'advanced-panel']
        },
        {
          id: 'expert',
          name: 'Expert',
          description: 'Complete feature set with debugging and customization',
          minZoom: 0.8,
          maxZoom: 3.0,
          features: ['all-features', 'debug-tools', 'custom-plugins', 'performance-monitor'],
          nodeVisibility: {
            'act': true,
            'scene': true,
            'character-asset': true,
            'style-asset': true,
            'shot': true,
            'effect': true,
            'audio': true
          },
          edgeVisibility: {
            'default': true,
            'animated': true,
            'custom': true
          },
          uiElements: ['toolbar', 'minimap', 'controls', 'properties-panel', 'advanced-panel', 'debug-panel']
        }
      ],
      currentLevel: 'intermediate',
      autoAdjust: true,
      customRules: {}
    };
  }

  getCurrentLevel(): DisclosureLevel {
    return this.config.levels.find(level => level.id === this.config.currentLevel) || this.config.levels[1];
  }

  getAllLevels(): DisclosureLevel[] {
    return [...this.config.levels];
  }

  setLevel(levelId: string): void {
    const level = this.config.levels.find(l => l.id === levelId);
    if (level) {
      this.config.currentLevel = levelId;
      this.notifyListeners();
    }
  }

  setAutoAdjust(enabled: boolean): void {
    this.config.autoAdjust = enabled;
  }

  determineLevelForZoom(zoom: number): string {
    if (!this.config.autoAdjust) {
      return this.config.currentLevel;
    }

    for (const level of this.config.levels) {
      if (zoom >= level.minZoom && zoom <= level.maxZoom) {
        return level.id;
      }
    }

    // Default to intermediate if no level matches
    return 'intermediate';
  }

  filterNodesByLevel(nodes: any[], levelId?: string): any[] {
    const targetLevel = levelId ? this.config.levels.find(l => l.id === levelId) : this.getCurrentLevel();
    if (!targetLevel) return nodes;

    return nodes.filter(node => {
      const nodeType = node.type || node.data?.type;
      return targetLevel.nodeVisibility[nodeType] !== false;
    });
  }

  filterEdgesByLevel(edges: any[], levelId?: string): any[] {
    const targetLevel = levelId ? this.config.levels.find(l => l.id === levelId) : this.getCurrentLevel();
    if (!targetLevel) return edges;

    return edges.filter(edge => {
      const edgeType = edge.type || 'default';
      return targetLevel.edgeVisibility[edgeType] !== false;
    });
  }

  shouldShowUIElement(elementName: string, levelId?: string): boolean {
    const targetLevel = levelId ? this.config.levels.find(l => l.id === levelId) : this.getCurrentLevel();
    if (!targetLevel) return true;

    return targetLevel.uiElements.includes(elementName);
  }

  getFeaturesForLevel(levelId?: string): string[] {
    const targetLevel = levelId ? this.config.levels.find(l => l.id === levelId) : this.getCurrentLevel();
    if (!targetLevel) return [];

    return [...targetLevel.features];
  }

  addCustomRule(ruleName: string, rule: any): void {
    this.config.customRules[ruleName] = rule;
  }

  removeCustomRule(ruleName: string): void {
    delete this.config.customRules[ruleName];
  }

  onLevelChange(callback: (level: DisclosureLevel) => void): () => void {
    this.listeners.push(callback);
    return () => {
      const index = this.listeners.indexOf(callback);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners(): void {
    const currentLevel = this.getCurrentLevel();
    this.listeners.forEach(callback => callback(currentLevel));
  }

  exportConfig(): ProgressiveDisclosureConfig {
    return {
      levels: [...this.config.levels],
      currentLevel: this.config.currentLevel,
      autoAdjust: this.config.autoAdjust,
      customRules: { ...this.config.customRules }
    };
  }

  importConfig(config: ProgressiveDisclosureConfig): void {
    this.config = {
      ...config,
      levels: [...config.levels],
      customRules: { ...config.customRules }
    };
    this.notifyListeners();
  }

  resetToDefaults(): void {
    this.config.currentLevel = 'intermediate';
    this.config.autoAdjust = true;
    this.config.customRules = {};
    this.notifyListeners();
  }

  // Helper methods for specific scenarios
  getBeginnerLevel(): DisclosureLevel {
    return this.config.levels.find(l => l.id === 'beginner')!;
  }

  getIntermediateLevel(): DisclosureLevel {
    return this.config.levels.find(l => l.id === 'intermediate')!;
  }

  getAdvancedLevel(): DisclosureLevel {
    return this.config.levels.find(l => l.id === 'advanced')!;
  }

  getExpertLevel(): DisclosureLevel {
    return this.config.levels.find(l => l.id === 'expert')!;
  }
}

export const progressiveDisclosureService = new ProgressiveDisclosureService();