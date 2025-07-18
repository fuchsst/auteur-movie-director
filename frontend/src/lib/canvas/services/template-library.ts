import { writable, derived } from 'svelte/store';

export interface CanvasTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  thumbnail: string;
  data: {
    nodes: any[];
    edges: any[];
    viewport: any;
  };
  metadata: {
    author: string;
    created: string;
    updated: string;
    downloads: number;
    rating: number;
    version: string;
  };
  structure: 'three-act' | 'seven-point' | 'blake-snyder' | 'custom';
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
}

export interface TemplateCategory {
  id: string;
  name: string;
  description: string;
  count: number;
  icon: string;
}

interface TemplateLibraryState {
  templates: CanvasTemplate[];
  categories: TemplateCategory[];
  favorites: string[];
  searchQuery: string;
  selectedCategory: string;
  sortBy: 'name' | 'downloads' | 'rating' | 'created';
  sortOrder: 'asc' | 'desc';
  isLoading: boolean;
  error: string | null;
}

class TemplateLibraryService {
  private store = writable<TemplateLibraryState>({
    templates: [],
    categories: [],
    favorites: [],
    searchQuery: '',
    selectedCategory: 'all',
    sortBy: 'downloads',
    sortOrder: 'desc',
    isLoading: false,
    error: null
  });

  public templates = derived(this.store, $store => {
    let filtered = $store.templates;

    // Filter by category
    if ($store.selectedCategory !== 'all') {
      filtered = filtered.filter(t => t.category === $store.selectedCategory);
    }

    // Filter by search query
    if ($store.searchQuery.trim()) {
      const query = $store.searchQuery.toLowerCase();
      filtered = filtered.filter(t => 
        t.name.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query) ||
        t.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // Sort
    filtered.sort((a, b) => {
      const aVal = a[$store.sortBy as keyof CanvasTemplate] as any;
      const bVal = b[$store.sortBy as keyof CanvasTemplate] as any;
      
      if (typeof aVal === 'string') {
        return $store.sortOrder === 'asc' 
          ? aVal.localeCompare(bVal as string)
          : (bVal as string).localeCompare(aVal);
      }
      
      return $store.sortOrder === 'asc' 
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });

    return filtered;
  });

  public categories = derived(this.store, $store => $store.categories);
  public isLoading = derived(this.store, $store => $store.isLoading);
  public error = derived(this.store, $store => $store.error);

  constructor() {
    this.initializeDefaultTemplates();
    this.initializeCategories();
  }

  private initializeDefaultTemplates() {
    const defaultTemplates: CanvasTemplate[] = [
      {
        id: 'three-act-basic',
        name: 'Three-Act Structure (Basic)',
        description: 'Classic three-act structure for beginners',
        category: 'story-structure',
        tags: ['three-act', 'beginner', 'story'],
        thumbnail: '/templates/three-act-basic.png',
        data: {
          nodes: [
            {
              id: 'act1',
              type: 'act',
              position: { x: 100, y: 100 },
              data: { title: 'Act 1', description: 'Setup', percentage: 25 }
            },
            {
              id: 'act2',
              type: 'act',
              position: { x: 400, y: 100 },
              data: { title: 'Act 2', description: 'Confrontation', percentage: 50 }
            },
            {
              id: 'act3',
              type: 'act',
              position: { x: 700, y: 100 },
              data: { title: 'Act 3', description: 'Resolution', percentage: 25 }
            }
          ],
          edges: [
            { id: 'e1', source: 'act1', target: 'act2', type: 'smoothstep' },
            { id: 'e2', source: 'act2', target: 'act3', type: 'smoothstep' }
          ],
          viewport: { x: 0, y: 0, zoom: 1 }
        },
        metadata: {
          author: 'System',
          created: new Date().toISOString(),
          updated: new Date().toISOString(),
          downloads: 1250,
          rating: 4.8,
          version: '1.0.0'
        },
        structure: 'three-act',
        difficulty: 'beginner'
      },
      {
        id: 'seven-point-method',
        name: 'Seven-Point Method',
        description: 'Complete seven-point story structure',
        category: 'story-structure',
        tags: ['seven-point', 'intermediate', 'plot-points'],
        thumbnail: '/templates/seven-point-method.png',
        data: {
          nodes: [
            { id: 'hook', type: 'plot-point', position: { x: 100, y: 100 }, data: { title: 'Hook', description: '0%', position: 0 } },
            { id: 'plot-turn-1', type: 'plot-point', position: { x: 250, y: 100 }, data: { title: 'Plot Turn 1', description: '25%', position: 25 } },
            { id: 'pinch-1', type: 'plot-point', position: { x: 400, y: 100 }, data: { title: 'Pinch 1', description: '37.5%', position: 37.5 } },
            { id: 'midpoint', type: 'plot-point', position: { x: 550, y: 100 }, data: { title: 'Midpoint', description: '50%', position: 50 } },
            { id: 'pinch-2', type: 'plot-point', position: { x: 700, y: 100 }, data: { title: 'Pinch 2', description: '62.5%', position: 62.5 } },
            { id: 'plot-turn-2', type: 'plot-point', position: { x: 850, y: 100 }, data: { title: 'Plot Turn 2', description: '75%', position: 75 } },
            { id: 'resolution', type: 'plot-point', position: { x: 1000, y: 100 }, data: { title: 'Resolution', description: '100%', position: 100 } }
          ],
          edges: [
            { id: 'e1', source: 'hook', target: 'plot-turn-1', type: 'smoothstep' },
            { id: 'e2', source: 'plot-turn-1', target: 'pinch-1', type: 'smoothstep' },
            { id: 'e3', source: 'pinch-1', target: 'midpoint', type: 'smoothstep' },
            { id: 'e4', source: 'midpoint', target: 'pinch-2', type: 'smoothstep' },
            { id: 'e5', source: 'pinch-2', target: 'plot-turn-2', type: 'smoothstep' },
            { id: 'e6', source: 'plot-turn-2', target: 'resolution', type: 'smoothstep' }
          ],
          viewport: { x: 0, y: 0, zoom: 0.8 }
        },
        metadata: {
          author: 'System',
          created: new Date().toISOString(),
          updated: new Date().toISOString(),
          downloads: 890,
          rating: 4.7,
          version: '1.0.0'
        },
        structure: 'seven-point',
        difficulty: 'intermediate'
      },
      {
        id: 'blake-snyder-beat-sheet',
        name: 'Blake Snyder Beat Sheet',
        description: 'Save the Cat beat sheet with all 15 beats',
        category: 'story-structure',
        tags: ['save-the-cat', 'blake-snyder', 'advanced', 'beats'],
        thumbnail: '/templates/blake-snyder-beat-sheet.png',
        data: {
          nodes: [
            { id: 'opening-image', type: 'beat', position: { x: 100, y: 100 }, data: { title: 'Opening Image', description: '0% - 1%', percentage: 1 } },
            { id: 'theme-stated', type: 'beat', position: { x: 200, y: 100 }, data: { title: 'Theme Stated', description: '5%', percentage: 5 } },
            { id: 'setup', type: 'beat', position: { x: 300, y: 100 }, data: { title: 'Setup', description: '1-10%', percentage: 10 } },
            { id: 'catalyst', type: 'beat', position: { x: 400, y: 100 }, data: { title: 'Catalyst', description: '10%', percentage: 10 } },
            { id: 'debate', type: 'beat', position: { x: 500, y: 100 }, data: { title: 'Debate', description: '10-20%', percentage: 20 } },
            { id: 'break-into-two', type: 'beat', position: { x: 600, y: 100 }, data: { title: 'Break into Two', description: '20%', percentage: 20 } },
            { id: 'b-story', type: 'beat', position: { x: 700, y: 100 }, data: { title: 'B Story', description: '22%', percentage: 22 } },
            { id: 'fun-and-games', type: 'beat', position: { x: 800, y: 100 }, data: { title: 'Fun and Games', description: '20-50%', percentage: 50 } },
            { id: 'midpoint', type: 'beat', position: { x: 900, y: 100 }, data: { title: 'Midpoint', description: '50%', percentage: 50 } },
            { id: 'bad-guys-close-in', type: 'beat', position: { x: 1000, y: 100 }, data: { title: 'Bad Guys Close In', description: '50-75%', percentage: 75 } },
            { id: 'all-is-lost', type: 'beat', position: { x: 1100, y: 100 }, data: { title: 'All is Lost', description: '75%', percentage: 75 } },
            { id: 'dark-night', type: 'beat', position: { x: 1200, y: 100 }, data: { title: 'Dark Night of the Soul', description: '75-80%', percentage: 80 } },
            { id: 'break-into-three', type: 'beat', position: { x: 1300, y: 100 }, data: { title: 'Break into Three', description: '80%', percentage: 80 } },
            { id: 'finale', type: 'beat', position: { x: 1400, y: 100 }, data: { title: 'Finale', description: '80-99%', percentage: 99 } },
            { id: 'final-image', type: 'beat', position: { x: 1500, y: 100 }, data: { title: 'Final Image', description: '100%', percentage: 100 } }
          ],
          edges: [
            { id: 'e1', source: 'opening-image', target: 'theme-stated', type: 'smoothstep' },
            { id: 'e2', source: 'theme-stated', target: 'setup', type: 'smoothstep' },
            { id: 'e3', source: 'setup', target: 'catalyst', type: 'smoothstep' },
            { id: 'e4', source: 'catalyst', target: 'debate', type: 'smoothstep' },
            { id: 'e5', source: 'debate', target: 'break-into-two', type: 'smoothstep' },
            { id: 'e6', source: 'break-into-two', target: 'b-story', type: 'smoothstep' },
            { id: 'e7', source: 'b-story', target: 'fun-and-games', type: 'smoothstep' },
            { id: 'e8', source: 'fun-and-games', target: 'midpoint', type: 'smoothstep' },
            { id: 'e9', source: 'midpoint', target: 'bad-guys-close-in', type: 'smoothstep' },
            { id: 'e10', source: 'bad-guys-close-in', target: 'all-is-lost', type: 'smoothstep' },
            { id: 'e11', source: 'all-is-lost', target: 'dark-night', type: 'smoothstep' },
            { id: 'e12', source: 'dark-night', target: 'break-into-three', type: 'smoothstep' },
            { id: 'e13', source: 'break-into-three', target: 'finale', type: 'smoothstep' },
            { id: 'e14', source: 'finale', target: 'final-image', type: 'smoothstep' }
          ],
          viewport: { x: 0, y: 0, zoom: 0.5 }
        },
        metadata: {
          author: 'System',
          created: new Date().toISOString(),
          updated: new Date().toISOString(),
          downloads: 650,
          rating: 4.9,
          version: '1.0.0'
        },
        structure: 'blake-snyder',
        difficulty: 'advanced'
      }
    ];

    this.store.update(state => ({
      ...state,
      templates: [...state.templates, ...defaultTemplates]
    }));
  }

  private initializeCategories() {
    const categories: TemplateCategory[] = [
      { id: 'all', name: 'All Templates', description: 'All available templates', count: 0, icon: '📋' },
      { id: 'story-structure', name: 'Story Structure', description: 'Pre-built story structures', count: 0, icon: '🏗️' },
      { id: 'genre-specific', name: 'Genre Specific', description: 'Templates for specific genres', count: 0, icon: '🎬' },
      { id: 'complexity-based', name: 'Complexity Based', description: 'Templates organized by complexity', count: 0, icon: '📊' },
      { id: 'user-created', name: 'User Created', description: 'Templates created by users', count: 0, icon: '👤' },
      { id: 'favorites', name: 'Favorites', description: 'Your favorite templates', count: 0, icon: '⭐' }
    ];

    this.store.update(state => ({
      ...state,
      categories
    }));

    this.updateCategoryCounts();
  }

  private updateCategoryCounts() {
    this.store.update(state => {
      const counts = {
        'all': state.templates.length,
        'story-structure': state.templates.filter(t => ['three-act', 'seven-point', 'blake-snyder'].includes(t.structure)).length,
        'genre-specific': state.templates.filter(t => t.category === 'genre-specific').length,
        'complexity-based': state.templates.filter(t => t.category === 'complexity-based').length,
        'user-created': state.templates.filter(t => t.category === 'user-created').length,
        'favorites': state.templates.filter(t => state.favorites.includes(t.id)).length
      };

      const updatedCategories = state.categories.map(category => ({
        ...category,
        count: counts[category.id] || 0
      }));

      return {
        ...state,
        categories: updatedCategories
      };
    });
  }

  async searchTemplates(query: string): Promise<void> {
    this.store.update(state => ({ ...state, searchQuery: query }));
  }

  async filterByCategory(category: string): Promise<void> {
    this.store.update(state => ({ ...state, selectedCategory: category }));
  }

  async sortTemplates(sortBy: 'name' | 'downloads' | 'rating' | 'created', sortOrder: 'asc' | 'desc'): Promise<void> {
    this.store.update(state => ({ ...state, sortBy, sortOrder }));
  }

  async toggleFavorite(templateId: string): Promise<void> {
    this.store.update(state => {
      const favorites = state.favorites.includes(templateId)
        ? state.favorites.filter(id => id !== templateId)
        : [...state.favorites, templateId];

      return { ...state, favorites };
    });

    this.updateCategoryCounts();
  }

  async getTemplate(templateId: string): Promise<CanvasTemplate | undefined> {
    const state = this.store.get();
    return state.templates.find(t => t.id === templateId);
  }

  async createTemplate(template: Omit<CanvasTemplate, 'id' | 'metadata.created' | 'metadata.updated'>): Promise<CanvasTemplate> {
    const newTemplate: CanvasTemplate = {
      ...template,
      id: this.generateId(),
      metadata: {
        ...template.metadata,
        created: new Date().toISOString(),
        updated: new Date().toISOString()
      }
    };

    this.store.update(state => ({
      ...state,
      templates: [...state.templates, newTemplate]
    }));

    this.updateCategoryCounts();
    return newTemplate;
  }

  async updateTemplate(templateId: string, updates: Partial<CanvasTemplate>): Promise<void> {
    this.store.update(state => ({
      ...state,
      templates: state.templates.map(template => 
        template.id === templateId
          ? { ...template, ...updates, metadata: { ...template.metadata, updated: new Date().toISOString() } }
          : template
      )
    }));
  }

  async deleteTemplate(templateId: string): Promise<void> {
    this.store.update(state => ({
      ...state,
      templates: state.templates.filter(t => t.id !== templateId),
      favorites: state.favorites.filter(id => id !== templateId)
    }));

    this.updateCategoryCounts();
  }

  async exportTemplate(templateId: string): Promise<string> {
    const template = await this.getTemplate(templateId);
    if (!template) throw new Error('Template not found');

    return JSON.stringify(template, null, 2);
  }

  async importTemplate(jsonData: string): Promise<CanvasTemplate> {
    try {
      const template = JSON.parse(jsonData) as CanvasTemplate;
      
      // Validate template structure
      if (!template.name || !template.data || !template.category) {
        throw new Error('Invalid template format');
      }

      // Create new template with updated metadata
      const newTemplate: CanvasTemplate = {
        ...template,
        id: this.generateId(),
        metadata: {
          ...template.metadata,
          author: 'Imported',
          created: new Date().toISOString(),
          updated: new Date().toISOString(),
          downloads: 0
        }
      };

      this.store.update(state => ({
        ...state,
        templates: [...state.templates, newTemplate]
      }));

      this.updateCategoryCounts();
      return newTemplate;
    } catch (error) {
      throw new Error(`Failed to import template: ${error.message}`);
    }
  }

  async shareTemplate(templateId: string): Promise<string> {
    const template = await this.getTemplate(templateId);
    if (!template) throw new Error('Template not found');

    // In a real app, this would generate a shareable URL
    const shareUrl = `${window.location.origin}/templates/shared/${templateId}`;
    
    // Copy to clipboard
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(shareUrl);
    }

    return shareUrl;
  }

  private generateId(): string {
    return `template-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Store getters
  getStore() {
    return this.store;
  }
}

export const templateLibraryService = new TemplateLibraryService();