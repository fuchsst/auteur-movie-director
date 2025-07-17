# Story: Template Library & Sharing

**Story ID**: STORY-063  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: Medium  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker, I want to create, save, and share reusable story templates and workflow patterns so that I can quickly start new projects with proven structures and share my creative workflows with the community.

## Acceptance Criteria

### Template Library System
- [ ] **Template creation** from existing canvas configurations
- [ ] **Template categorization** by story type, genre, and complexity
- [ ] **Template search** with filters and tags
- [ ] **Template preview** with interactive thumbnails
- [ ] **Template versioning** for iterative improvements
- [ ] **Template import/export** for sharing and backup

### Template Types
- [ ] **Story structure templates** (Three-Act, Seven-Point, Blake Snyder)
- [ ] **Genre-specific templates** (Action, Romance, Horror, etc.)
- [ ] **Workflow templates** (Character development, scene generation)
- [ ] **Asset configuration templates** (Character + Style combinations)
- [ ] **Processing pipeline templates** (Quality tiers and optimization)
- [ ] **Custom templates** user-created combinations

### Sharing System
- [ ] **Community template library** with public templates
- [ ] **Private template sharing** with specific users
- [ ] **Template ratings** and reviews
- [ ] **Usage statistics** showing template popularity
- [ ] **Fork functionality** for customizing existing templates
- [ ] **Template attribution** crediting original creators

### Template Management
- [ ] **Template editor** for modifying existing templates
- [ ] **Template validation** ensuring compatibility
- [ ] **Template documentation** with usage instructions
- [ ] **Template dependencies** handling required assets
- [ ] **Template updates** notification system
- [ ] **Template deprecation** handling outdated templates

## Implementation Notes

### Technical Architecture
```typescript
// Template system interfaces
interface Template {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  tags: string[];
  complexity: ComplexityLevel;
  nodes: TemplateNode[];
  edges: TemplateEdge[];
  metadata: TemplateMetadata;
  version: string;
  author: User;
  isPublic: boolean;
  usage: TemplateUsage;
}

interface TemplateNode {
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
  properties: Record<string, any>;
}

interface TemplateEdge {
  source: string;
  target: string;
  type: string;
  data: Record<string, any>;
}

interface TemplateMetadata {
  genre: string[];
  storyStructure: string[];
  estimatedTime: string;
  difficulty: 'easy' | 'medium' | 'hard';
  requiredAssets: string[];
  description: string;
  thumbnail: string;
}

// Template management service
class TemplateService {
  async createTemplate(canvas: CanvasState, metadata: TemplateMetadata): Promise<Template> {
    const template: Template = {
      id: generateId(),
      name: metadata.name,
      description: metadata.description,
      category: metadata.category,
      tags: metadata.tags,
      complexity: this.determineComplexity(canvas),
      nodes: this.extractNodes(canvas),
      edges: this.extractEdges(canvas),
      metadata,
      version: '1.0.0',
      author: this.getCurrentUser(),
      isPublic: metadata.isPublic,
      usage: { uses: 0, rating: 0, reviews: [] }
    };

    await this.saveTemplate(template);
    return template;
  }

  async searchTemplates(query: string, filters: TemplateFilters): Promise<Template[]> {
    return await api.templates.search({
      query,
      filters: {
        category: filters.category,
        complexity: filters.complexity,
        tags: filters.tags,
        isPublic: filters.isPublic
      }
    });
  }

  async applyTemplate(template: Template, project: Project): Promise<CanvasState> {
    const populatedNodes = await this.populateTemplate(template, project);
    const connections = this.createTemplateConnections(template, populatedNodes);
    
    return {
      nodes: populatedNodes,
      edges: connections,
      viewport: this.calculateViewport(populatedNodes)
    };
  }
}
```

### Template Categories
```typescript
const TEMPLATE_CATEGORIES = {
  'story-structure': {
    name: 'Story Structure',
    description: 'Pre-built story frameworks and narrative structures',
    subcategories: ['three-act', 'seven-point', 'blake-snyder', 'hero-journey']
  },
  
  'genre-specific': {
    name: 'Genre Templates',
    description: 'Templates tailored for specific genres',
    subcategories: ['action', 'romance', 'horror', 'comedy', 'drama', 'sci-fi']
  },
  
  'workflow': {
    name: 'Workflow Templates',
    description: 'Complete production workflows',
    subcategories: ['character-dev', 'scene-gen', 'batch-processing', 'quality-pipeline']
  },
  
  'asset-config': {
    name: 'Asset Configuration',
    description: 'Pre-configured asset combinations',
    subcategories: ['character-sets', 'style-packs', 'location-combos']
  },
  
  'custom': {
    name: 'Custom Templates',
    description: 'User-created custom templates',
    subcategories: ['user-created', 'community-shared']
  }
};

// Built-in templates
const BUILT_IN_TEMPLATES = [
  {
    id: 'three-act-basic',
    name: 'Basic Three-Act Structure',
    category: 'story-structure',
    complexity: ComplexityLevel.BEGINNER,
    nodes: [
      { type: 'story-act-1', position: { x: 100, y: 100 }, data: { label: 'Act 1: Setup' } },
      { type: 'story-act-2', position: { x: 400, y: 100 }, data: { label: 'Act 2: Confrontation' } },
      { type: 'story-act-3', position: { x: 700, y: 100 }, data: { label: 'Act 3: Resolution' } }
    ],
    edges: [
      { source: 'act-1', target: 'act-2' },
      { source: 'act-2', target: 'act-3' }
    ],
    metadata: {
      genre: ['universal'],
      storyStructure: ['three-act'],
      estimatedTime: '30 minutes',
      difficulty: 'easy',
      requiredAssets: [],
      description: 'A basic three-act structure template for any story'
    }
  },
  
  {
    id: 'character-dev-workflow',
    name: 'Character Development Workflow',
    category: 'workflow',
    complexity: ComplexityLevel.INTERMEDIATE,
    nodes: [
      { type: 'asset-character', position: { x: 100, y: 100 } },
      { type: 'process-generate', position: { x: 300, y: 100 } },
      { type: 'process-enhance', position: { x: 500, y: 100 } },
      { type: 'process-upscale', position: { x: 700, y: 100 } }
    ],
    edges: [
      { source: 'character', target: 'generate' },
      { source: 'generate', target: 'enhance' },
      { source: 'enhance', target: 'upscale' }
    ],
    metadata: {
      genre: ['character-focused'],
      storyStructure: ['character-driven'],
      estimatedTime: '45 minutes',
      difficulty: 'medium',
      requiredAssets: ['character-concept'],
      description: 'Complete character development from concept to final render'
    }
  },
  
  {
    id: 'romance-scene-generator',
    name: 'Romance Scene Generator',
    category: 'genre-specific',
    complexity: ComplexityLevel.ADVANCED,
    nodes: [
      { type: 'story-scene', position: { x: 100, y: 100 }, data: { type: 'romance' } },
      { type: 'asset-character-1', position: { x: 200, y: 200 } },
      { type: 'asset-character-2', position: { x: 200, y: 300 } },
      { type: 'asset-style', position: { x: 200, y: 400 } },
      { type: 'asset-location', position: { x: 200, y: 500 } },
      { type: 'process-generate', position: { x: 400, y: 300 } },
      { type: 'process-enhance', position: { x: 600, y: 300 } }
    ],
    edges: [
      { source: 'scene', target: 'character-1' },
      { source: 'scene', target: 'character-2' },
      { source: 'scene', target: 'style' },
      { source: 'scene', target: 'location' },
      { source: 'character-1', target: 'generate' },
      { source: 'character-2', target: 'generate' },
      { source: 'style', target: 'generate' },
      { source: 'location', target: 'generate' },
      { source: 'generate', target: 'enhance' }
    ],
    metadata: {
      genre: ['romance'],
      storyStructure: ['romance-arc'],
      estimatedTime: '60 minutes',
      difficulty: 'hard',
      requiredAssets: ['character-1', 'character-2', 'romance-style', 'intimate-location'],
      description: 'Complete romance scene generation with dual characters and atmospheric styling'
    }
  }
];
```

### Template Browser Component
```svelte
<!-- TemplateBrowser component -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { templateStore } from '$lib/stores/templates';
  
  let templates: Template[] = [];
  let searchQuery = '';
  let selectedCategory = 'all';
  let selectedComplexity = 'all';
  
  onMount(async () => {
    templates = await templateStore.getTemplates();
  });
  
  $: filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesComplexity = selectedComplexity === 'all' || template.complexity === selectedComplexity;
    
    return matchesSearch && matchesCategory && matchesComplexity;
  });
  
  async function applyTemplate(template: Template): Promise<void> {
    await templateStore.applyTemplate(template);
  }
</script>

<div class="template-browser">
  <div class="search-filters">
    <input type="text" bind:value={searchQuery} placeholder="Search templates..." />
    
    <select bind:value={selectedCategory}>
      <option value="all">All Categories</option>
      {#each Object.keys(TEMPLATE_CATEGORIES) as category}
        <option value={category}>{TEMPLATE_CATEGORIES[category].name}</option>
      {/each}
    </select>
    
    <select bind:value={selectedComplexity}>
      <option value="all">All Levels</option>
      <option value="beginner">Beginner</option>
      <option value="intermediate">Intermediate</option>
      <option value="advanced">Advanced</option>
      <option value="expert">Expert</option>
    </select>
  </div>
  
  <div class="template-grid">
    {#each filteredTemplates as template}
      <TemplateCard {template} on:apply={applyTemplate} />
    {/each}
  </div>
</div>
```

### Template Creation Workflow
```svelte
<!-- TemplateCreationDialog component -->
<script lang="ts">
  import { canvasStore } from '$lib/stores/canvas';
  import { templateStore } from '$lib/stores/templates';
  
  let templateName = '';
  let templateDescription = '';
  let templateCategory = 'story-structure';
  let templateTags = '';
  let isPublic = false;
  
  async function createTemplate(): Promise<void> {
    const canvasState = $canvasStore.currentState;
    const template = await templateStore.createTemplate(canvasState, {
      name: templateName,
      description: templateDescription,
      category: templateCategory,
      tags: templateTags.split(',').map(t => t.trim()),
      isPublic
    });
    
    // Show success message
  }
</script>

<div class="template-creation-dialog">
  <form on:submit|preventDefault={createTemplate}>
    <div class="form-group">
      <label>Template Name</label>
      <input type="text" bind:value={templateName} required />
    </div>
    
    <div class="form-group">
      <label>Description</label>
      <textarea bind:value={templateDescription} required/>
    </div>
    
    <div class="form-group">
      <label>Category</label>
      <select bind:value={templateCategory}>
        {#each Object.keys(TEMPLATE_CATEGORIES) as category}
          <option value={category}>{TEMPLATE_CATEGORIES[category].name}</option>
        {/each}
      </select>
    </div>
    
    <div class="form-group">
      <label>Tags (comma-separated)</label>
      <input type="text" bind:value={templateTags} placeholder="romance, character-driven, modern" />
    </div>
    
    <div class="form-group">
      <label>
        <input type="checkbox" bind:checked={isPublic} /> Make template public
      </label>
    </div>
    
    <button type="submit">Create Template</button>
  </form>
</div>
```

### Sharing and Community Features
```typescript
class TemplateSharingService {
  async shareWithUser(templateId: string, userId: string): Promise<void> {
    await api.templates.share(templateId, {
      userId,
      permission: 'view',
      expiresAt: null
    });
  }

  async publishTemplate(templateId: string): Promise<void> {
    await api.templates.update(templateId, { isPublic: true });
  }

  async rateTemplate(templateId: string, rating: number, review?: string): Promise<void> {
    await api.templates.rate(templateId, {
      rating,
      review,
      userId: this.getCurrentUserId()
    });
  }

  async forkTemplate(templateId: string, newName: string): Promise<Template> {
    const original = await api.templates.get(templateId);
    const forked = {
      ...original,
      id: generateId(),
      name: newName,
      author: this.getCurrentUser(),
      parentTemplate: templateId,
      version: '1.0.0'
    };
    
    await api.templates.create(forked);
    return forked;
  }
}
```

### Template Validation
```typescript
class TemplateValidator {
  validateTemplate(template: Template): ValidationResult {
    const errors: string[] = [];
    
    // Validate node connections
    const connectionErrors = this.validateConnections(template);
    errors.push(...connectionErrors);
    
    // Validate required assets
    const assetErrors = this.validateRequiredAssets(template);
    errors.push(...assetErrors);
    
    // Validate complexity consistency
    const complexityErrors = this.validateComplexity(template);
    errors.push(...complexityErrors);
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings: this.generateWarnings(template)
    };
  }

  private validateConnections(template: Template): string[] {
    const errors: string[] = [];
    
    template.edges.forEach(edge => {
      const sourceNode = template.nodes.find(n => n.id === edge.source);
      const targetNode = template.nodes.find(n => n.id === edge.target);
      
      if (!sourceNode || !targetNode) {
        errors.push(`Invalid edge connection: ${edge.source} -> ${edge.target}`);
      }
    });
    
    return errors;
  }
}
```

### Testing Requirements

#### Unit Tests
- [ ] Template creation from canvas state
- [ ] Template application to new projects
- [ ] Template search and filtering
- [ ] Template validation
- [ ] Sharing functionality

#### Integration Tests
- [ ] Complete template workflow
- [ ] Template library integration
- [ ] Community template features
- [ ] Template versioning
- [ ] Import/export functionality

#### E2E Tests
- [ ] Template creation and sharing workflow
- [ ] Community template discovery
- [ ] Template application to projects
- [ ] Rating and review system
- [ ] Fork and customization workflow

### Dependencies
- **STORY-053-062**: All previous implementations (for template content)
- **EPIC-001**: Project persistence for template storage
- **EPIC-002**: Asset system for template dependencies
- **EPIC-003**: User management for sharing and attribution

### Definition of Done
- [ ] Template creation working correctly
- [ ] Template library with search and filtering
- [ ] Template application to projects
- [ ] Sharing system functional
- [ ] Community features active
- [ ] Template validation working
- [ ] Import/export capabilities
- [ ] Documentation with examples provided
- [ ] Ready for STORY-064 (Performance Optimization) implementation