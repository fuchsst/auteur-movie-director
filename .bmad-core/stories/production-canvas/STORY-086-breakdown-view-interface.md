# User Story: STORY-086 - Breakdown View Interface

## Story Description
**As a** filmmaker familiar with traditional production workflows
**I want** an intuitive breakdown view interface that mirrors professional script breakdown software
**So that** I can tag and organize all production elements (props, wardrobe, vehicles, etc.) using familiar workflows while maintaining integration with the generative platform

## Acceptance Criteria

### Functional Requirements
- [ ] **Two-Panel Script Breakdown Layout** (script text + breakdown sheet)
- [ ] **Color-Coded Tagging System** following industry standards
- [ ] **Interactive Script Highlighting** for direct asset creation
- [ ] **Dynamic Breakdown Sheets** per scene with all elements
- [ ] **Asset Creation Dialogs** from script context menus
- [ ] **Real-time Synchronization** with Production Canvas
- [ ] **Multi-scene Navigation** with scene thumbnails
- [ ] **Export to Traditional Formats** (PDF breakdown sheets)

### Technical Requirements
- [ ] **Script Import/Parser** for standard screenplay formats (.fdx, .pdf, .txt)
- [ ] **Asset Tag Recognition** using NLP for automatic detection
- [ ] **Context Menu Integration** for asset creation and linking
- [ ] **Synchronized Data Model** with underlying project.json
- [ ] **Responsive Design** for various screen sizes
- [ ] **Keyboard Shortcuts** for efficient tagging workflow
- [ ] **Search and Filter** capabilities across all tagged elements
- [ ] **Undo/Redo System** for breakdown operations

### Quality Requirements
- [ ] **User Experience Testing** with film production professionals
- [ ] **Script Format Compatibility** testing across formats
- [ ] **Performance Testing** with large scripts (100+ scenes)
- [ ] **Accessibility Testing** (WCAG 2.1 AA compliance)
- [ ] **Cross-browser Compatibility** testing
- [ ] **Asset Consistency** validation across views

## Implementation Notes

### Interface Architecture
```typescript
interface BreakdownViewState {
  currentScene: Scene;
  scriptText: string;
  breakdownSheet: BreakdownSheet;
  selectedElements: BreakdownElement[];
  assetRegistry: AssetRegistry;
  syncStatus: SyncStatus;
}

interface BreakdownSheet {
  sceneId: string;
  sceneNumber: string;
  sceneHeading: string;
  synopsis: string;
  elements: {
    cast: CharacterAsset[];
    props: PropAsset[];
    wardrobe: WardrobeAsset[];
    vehicles: VehicleAsset[];
    setDressing: SetDressingAsset[];
    sfx: SpecialEffect[];
    sounds: SoundAsset[];
    music: MusicAsset[];
  };
  estimatedDuration: number;
  estimatedBudget: BudgetEstimate;
}
```

### Script Parser and Highlighter
```typescript
class ScriptParser {
  private parser: ScreenplayParser;
  private highlighter: SyntaxHighlighter;

  constructor() {
    this.parser = new ScreenplayParser();
    this.highlighter = new SyntaxHighlighter();
  }

  async parseScript(fileContent: string): Promise<ParsedScript> {
    const parsed = await this.parser.parse(fileContent);
    return {
      scenes: parsed.scenes,
      characters: parsed.characters,
      locations: parsed.locations,
      props: this.extractProps(parsed.text),
      wardrobe: this.extractWardrobe(parsed.text),
      timeline: this.buildTimeline(parsed.scenes)
    };
  }

  private extractProps(text: string): PropDetection[] {
    const propPatterns = [
      /\b(?:a|an|the)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g,
      /\b(?:holds|carries|uses|wields)\s+(?:the|a|an)?\s*([a-z]+(?:\s+[a-z]+)*)\b/gi
    ];
    
    const detectedProps: PropDetection[] = [];
    
    propPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        detectedProps.push({
          text: match[1],
          start: match.index,
          end: match.index + match[1].length,
          confidence: this.calculateConfidence(match[1])
        });
      }
    });
    
    return detectedProps;
  }

  private extractWardrobe(text: string): WardrobeDetection[] {
    const wardrobePatterns = [
      /(?:wearing|dressed in|wears)\s+(?:a|an|the)?\s*([a-z]+(?:\s+[a-z]+)*)\b/gi,
      /(?:t-shirt|jacket|coat|dress|suit|uniform|gown)\b/gi
    ];
    
    return this.extractElements(text, wardrobePatterns, "wardrobe");
  }
}
```

### Breakdown View Component
```svelte
<!-- BreakdownView.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import ScriptPanel from './ScriptPanel.svelte';
  import BreakdownPanel from './BreakdownPanel.svelte';
  import SceneNavigator from './SceneNavigator.svelte';
  import { breakdownStore } from '$lib/stores/breakdown';
  
  let currentScene = null;
  let scriptContent = '';
  let breakdownData = null;
  
  onMount(async () => {
    await breakdownStore.loadProject($page.params.projectId);
    breakdownStore.subscribe(state => {
      currentScene = state.currentScene;
      scriptContent = state.scriptContent;
      breakdownData = state.breakdownData;
    });
  });
</script>

<div class="breakdown-view">
  <SceneNavigator 
    scenes={$breakdownStore.scenes}
    currentScene={$breakdownStore.currentScene}
    on:sceneSelect={(e) => breakdownStore.setCurrentScene(e.detail)}
  />
  
  <div class="main-content">
    <div class="script-panel">
      <ScriptPanel
        content={scriptContent}
        currentScene={currentScene}
        on:elementDetected={(e) => handleElementDetection(e.detail)}
        on:elementTagged={(e) => handleElementTagging(e.detail)}
      />
    </div>
    
    <div class="breakdown-panel">
      <BreakdownPanel
        scene={currentScene}
        breakdown={breakdownData}
        on:assetCreated={(e) => handleAssetCreation(e.detail)}
        on:assetLinked={(e) => handleAssetLinking(e.detail)}
      />
    </div>
  </div>
</div>
<style>
  .breakdown-view {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }
  
  .main-content {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 1rem;
    flex: 1;
    padding: 1rem;
  }
  
  .script-panel {
    border-right: 1px solid #e5e7eb;
    padding-right: 1rem;
  }
</style>
```

### Interactive Script Panel
```typescript
// ScriptPanel.svelte
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { marked } from 'marked';
  
  export let content: string;
  export let currentScene: Scene;
  
  const dispatch = createEventDispatcher();
  
  let selectedText = '';
  let contextMenu = null;
  let highlightedElements = [];
  
  function handleTextSelection(event) {
    const selection = window.getSelection();
    selectedText = selection.toString().trim();
    
    if (selectedText) {
      showContextMenu(event, selectedText);
    }
  }
  
  function showContextMenu(event, text) {
    contextMenu = {
      x: event.clientX,
      y: event.clientY,
      text: text,
      elementTypes: [
        { type: 'prop', label: 'Prop', icon: '🎭' },
        { type: 'wardrobe', label: 'Wardrobe', icon: '👔' },
        { type: 'vehicle', label: 'Vehicle', icon: '🚗' },
        { type: 'set_dressing', label: 'Set Dressing', icon: '🏠' }
      ]
    };
  }
  
  function handleElementCreation(type: string) {
    dispatch('elementDetected', {
      type: type,
      text: selectedText,
      position: contextMenu,
      sceneId: currentScene.id
    });
    
    contextMenu = null;
  }
  
  function highlightScriptElements() {
    // Implementation for highlighting tagged elements
    highlightedElements = breakdownStore.getHighlightedElements();
  }
</script>

<div class="script-panel">
  <div class="script-content"
    on:mouseup={handleTextSelection}
    bind:this={scriptElement}
  >
    {@html marked(content)}
  </div>
  
  {#if contextMenu}
    <div class="context-menu" style="left: {contextMenu.x}px; top: {contextMenu.y}px">
      <div class="menu-title">Tag "{contextMenu.text}" as:</div>
      {#each contextMenu.elementTypes as type}
        <button class="menu-item" on:click={() => handleElementCreation(type.type)}>
          <span class="icon">{type.icon}</span>
          {type.label}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .script-panel {
    height: 100%;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    line-height: 1.6;
  }
  
  .script-content {
    padding: 2rem;
    white-space: pre-wrap;
    font-size: 14px;
  }
  
  .context-menu {
    position: fixed;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    z-index: 1000;
    padding: 0.5rem 0;
  }
  
  .menu-title {
    padding: 0.5rem 1rem;
    font-weight: bold;
    border-bottom: 1px solid #eee;
  }
  
  .menu-item {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    border: none;
    background: none;
    cursor: pointer;
    width: 100%;
    text-align: left;
  }
  
  .menu-item:hover {
    background: #f5f5f5;
  }
  
  .icon {
    margin-right: 0.5rem;
  }
</style>
```

### Breakdown Panel Component
```typescript
// BreakdownPanel.svelte
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import ElementList from './ElementList.svelte';
  import AssetCreator from './AssetCreator.svelte';
  
  export let scene: Scene;
  export let breakdown: BreakdownSheet;
  
  const dispatch = createEventDispatcher();
  
  let activeTab = 'elements';
  let selectedElement = null;
  
  const tabs = [
    { id: 'elements', label: 'Elements', icon: '📝' },
    { id: 'assets', label: 'Assets', icon: '🎭' },
    { id: 'summary', label: 'Summary', icon: '📊' }
  ];
  
  function handleElementSelect(element) {
    selectedElement = element;
  }
  
  function handleAssetCreate(assetData) {
    dispatch('assetCreated', {
      ...assetData,
      sceneId: scene.id
    });
  }
</script>

<div class="breakdown-panel">
  <div class="panel-header">
    <h3>{scene.number}: {scene.heading}</h3>
    <p class="synopsis">{scene.synopsis}</p>
  </div>
  
  <div class="tabs">
    {#each tabs as tab}
      <button 
        class="tab {activeTab === tab.id ? 'active' : ''}"
        on:click={() => activeTab = tab.id}
      >
        <span class="icon">{tab.icon}</span>
        {tab.label}
      </button>
    {/each}
  </div>
  
  <div class="tab-content">
    {#if activeTab === 'elements'}
      <ElementList
        elements={breakdown.elements}
        on:elementSelect={handleElementSelect}
      />
    
    {:else if activeTab === 'assets'}
      <AssetCreator
        scene={scene}
        on:assetCreate={handleAssetCreate}
      />
    
    {:else if activeTab === 'summary'}
      <div class="summary">
        <div class="summary-item">
          <strong>Duration:</strong> {breakdown.estimatedDuration} seconds
        </div>
        <div class="summary-item">
          <strong>Cast:</strong> {breakdown.elements.cast.length} characters
        </div>
        <div class="summary-item">
          <strong>Props:</strong> {breakdown.elements.props.length} items
        </div>
        <div class="summary-item">
          <strong>Budget:</strong> ${breakdown.estimatedBudget.total}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .breakdown-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .panel-header {
    padding: 1rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .panel-header h3 {
    margin: 0 0 0.5rem 0;
    color: #374151;
  }
  
  .synopsis {
    margin: 0;
    color: #6b7280;
    font-size: 0.875rem;
  }
  
  .tabs {
    display: flex;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .tab {
    flex: 1;
    padding: 0.75rem;
    border: none;
    background: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }
  
  .tab.active {
    border-bottom: 2px solid #3b82f6;
    color: #3b82f6;
  }
  
  .tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .summary-item {
    margin-bottom: 0.5rem;
  }
</style>
```

### Synchronization with Production Canvas
```typescript
class BreakdownCanvasSync {
  private projectStore: ProjectStore;
  private canvasStore: CanvasStore;
  
  constructor(projectStore: ProjectStore, canvasStore: CanvasStore) {
    this.projectStore = projectStore;
    this.canvasStore = canvasStore;
  }
  
  async syncBreakdownToCanvas(breakdownData: BreakdownSheet) {
    // Sync assets to canvas nodes
    for (const asset of breakdownData.assets) {
      await this.createOrUpdateAssetNode(asset);
    }
    
    // Sync shot sequences
    for (const shot of breakdownData.shots) {
      await this.createShotNode(shot);
    }
    
    // Update project.json
    await this.updateProjectManifest(breakdownData);
  }
  
  async syncCanvasToBreakdown(canvasData: CanvasData) {
    // Transform canvas nodes to breakdown format
    const breakdownSheet = this.transformCanvasToBreakdown(canvasData);
    
    // Update breakdown store
    await breakdownStore.updateFromCanvas(breakdownSheet);
  }
}
```

### Export Capabilities
```typescript
class BreakdownExporter {
  exportToPDF(breakdownData: BreakdownSheet[]): Promise<Blob> {
    const doc = new jsPDF();
    
    breakdownData.forEach((sheet, index) => {
      doc.text(`Scene ${sheet.sceneNumber}: ${sheet.sceneHeading}`, 20, 20);
      doc.text(`Synopsis: ${sheet.synopsis}`, 20, 30);
      
      // Create breakdown table
      const tableData = this.createBreakdownTable(sheet.elements);
      doc.table(20, 40, tableData);
      
      if (index < breakdownData.length - 1) {
        doc.addPage();
      }
    });
    
    return doc.output('blob');
  }
  
  exportToCSV(breakdownData: BreakdownSheet[]): string {
    const headers = ['Scene', 'Element Type', 'Description', 'Quantity', 'Notes'];
    const rows = [];
    
    breakdownData.forEach(sheet => {
      Object.entries(sheet.elements).forEach(([type, elements]) => {
        elements.forEach(element => {
          rows.push([
            sheet.sceneNumber,
            type,
            element.name || element.description,
            element.quantity || 1,
            element.notes || ''
          ]);
        });
      });
    });
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }
}
```

### Testing Strategy

#### User Experience Testing
```typescript
class BreakdownViewTests {
  async testScriptParsing() {
    const parser = new ScriptParser();
    const script = `
      INT. WAREHOUSE - NIGHT
      
      JOHN, wearing a tattered trench coat, examines an ancient bronze sword.
      The flickering light reveals his weathered face.
    `;
    
    const result = await parser.parseScript(script);
    
    expect(result.scenes).toHaveLength(1);
    expect(result.characters).toContain('JOHN');
    expect(result.props).toContain('ancient bronze sword');
    expect(result.wardrobe).toContain('tattered trench coat');
  }
  
  async testAssetCreation() {
    const view = new BreakdownView();
    
    // Simulate user selecting text and creating asset
    const selection = 'ancient bronze sword';
    const asset = await view.createAssetFromSelection(selection, 'prop');
    
    expect(asset.name).toBe('Ancient Bronze Sword');
    expect(asset.type).toBe('prop');
    expect(asset.sceneId).toBeDefined();
  }
  
  async testCanvasSync() {
    const sync = new BreakdownCanvasSync();
    const scene = {
      id: 'scene-001',
      number: '1',
      heading: 'INT. WAREHOUSE - NIGHT',
      synopsis: 'John examines the sword'
    };
    
    await sync.syncBreakdownToCanvas({
      scene,
      elements: {
        props: [{ name: 'Ancient Sword' }],
        characters: [{ name: 'John' }]
      }
    });
    
    // Verify canvas has corresponding nodes
    const canvasNodes = await sync.getCanvasNodes();
    expect(canvasNodes).toHaveLength(2);
  }
}
```

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 5-6 (Phase 3)**

## Dependencies
- **STORY-083**: Expanded Asset System for asset management
- **STORY-084**: Structured GenerativeShotList for shot data
- **Script Parser**: Screenplay format parsing capabilities
- **UI Framework**: Svelte components for interface
- **Asset Registry**: Asset storage and retrieval
- **Canvas Sync**: Real-time synchronization system

## Success Criteria
- Professional script breakdown interface implemented
- Industry-standard color coding system active
- Interactive asset creation from script context working
- Real-time sync with Production Canvas verified
- Multi-format script import supported (.fdx, .pdf, .txt)
- Export to PDF breakdown sheets functional
- Performance tested with 100+ scene scripts
- User acceptance testing passed with film professionals
- Accessibility compliance (WCAG 2.1 AA) achieved
- Cross-browser compatibility verified

## Future Enhancements
- **AI Script Analysis**: Automated element detection
- **Collaborative Editing**: Multi-user breakdown sessions
- **Mobile Breakdown**: Tablet-friendly interface
- **Voice Commands**: Speech-to-text asset creation
- **Integration APIs**: Third-party script software connections
- **Template Library**: Industry-specific breakdown templates