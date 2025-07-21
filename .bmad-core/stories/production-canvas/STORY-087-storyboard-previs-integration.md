# User Story: STORY-087 - Storyboard/Pre-vis Integration

## Story Description
**As a** director and storyboard artist
**I want** to upload storyboard panels, concept art, and pre-vis elements directly to shots in the Production Canvas
**So that** visual references guide the generative AI to match my exact creative vision and maintain shot-to-shot continuity

## Acceptance Criteria

### Functional Requirements
- [ ] **Storyboard Panel Upload** with drag-and-drop interface
- [ ] **Concept Art Attachment** to specific shots and sequences
- [ ] **Visual Context Display** on Production Canvas nodes
- [ ] **Shot-to-Shot Continuity** tracking with visual references
- [ ] **Annotation System** for director's notes on storyboards
- [ ] **Version Management** for storyboard iterations
- [ ] **Pre-vis Video Support** for animatic uploads
- [ ] **Visual Reference Propagation** across related shots

### Technical Requirements
- [ ] **Image Processing Pipeline** for storyboard optimization
- [ ] **Thumbnail Generation** for canvas node display
- [ ] **Visual Similarity Detection** for continuity checking
- [ ] **Metadata Embedding** (framing, composition notes)
- [ ] **Multi-format Support** (JPG, PNG, PDF, MP4)
- [ **Cloud Storage Integration** for large files
- [ ] **Compression Optimization** for web display
- [ ] **Visual Search** across storyboard library

### Quality Requirements
- [ ] **Image Quality Validation** (resolution, format)
- [ ] **Continuity Consistency** testing across sequences
- [ ] **Performance Testing** with large storyboard sets (1000+ panels)
- [ ] **User Experience Testing** with directors and storyboard artists
- [ ] **Cross-platform Compatibility** testing
- [ ] **Accessibility Testing** for visual elements

## Implementation Notes

### Storyboard Architecture
```typescript
interface StoryboardSystem {
  storyboards: Storyboard[];
  previsElements: PrevisElement[];
  visualContext: VisualContext;
  continuityEngine: ContinuityEngine;
}

interface Storyboard {
  id: string;
  shotId: string;
  sceneId: string;
  sequenceId: string;
  panels: StoryboardPanel[];
  animatic?: PrevisVideo;
  metadata: StoryboardMetadata;
  continuity: ContinuityData;
}

interface StoryboardPanel {
  id: string;
  imageUrl: string;
  thumbnailUrl: string;
  frameNumber: number;
  annotations: Annotation[];
  framingData: FramingData;
  composition: CompositionData;
  version: number;
  createdAt: Date;
  updatedAt: Date;
}

interface FramingData {
  shotSize: 'extreme_close_up' | 'close_up' | 'medium_shot' | 'long_shot' | 'extreme_long_shot';
  angle: 'eye_level' | 'high_angle' | 'low_angle' | 'overhead' | 'dutch_angle';
  movement: 'static' | 'pan_left' | 'pan_right' | 'tilt_up' | 'tilt_down' | 'zoom_in' | 'zoom_out';
  focalLength?: number;
  depthOfField: 'shallow' | 'medium' | 'deep';
}

interface CompositionData {
  ruleOfThirds: boolean;
  leadingLines: string[];
  foregroundElements: string[];
  backgroundElements: string[];
  lightingDirection: string;
  colorPalette: string[];
}
```

### Upload and Processing Pipeline
```typescript
class StoryboardProcessor {
  private imageProcessor: ImageProcessor;
  private thumbnailGenerator: ThumbnailGenerator;
  private metadataExtractor: MetadataExtractor;

  constructor() {
    this.imageProcessor = new ImageProcessor();
    this.thumbnailGenerator = new ThumbnailGenerator();
    this.metadataExtractor = new MetadataExtractor();
  }

  async processStoryboardUpload(
    file: File,
    shotId: string,
    options: ProcessingOptions
  ): Promise<ProcessedStoryboard> {
    // Validate file
    await this.validateFile(file);
    
    // Generate unique ID
    const storyboardId = this.generateStoryboardId(shotId);
    
    // Process image
    const processedImage = await this.imageProcessor.process(file, options);
    
    // Generate thumbnails
    const thumbnails = await this.thumbnailGenerator.generate(processedImage);
    
    // Extract metadata
    const metadata = await this.metadataExtractor.extract(file);
    
    // Store in cloud
    const storageUrls = await this.storeInCloud(storyboardId, processedImage, thumbnails);
    
    return {
      id: storyboardId,
      shotId,
      originalUrl: storageUrls.original,
      thumbnailUrl: storageUrls.thumbnail,
      metadata,
      processingStatus: 'completed'
    };
  }

  private async validateFile(file: File): Promise<void> {
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    if (!validTypes.includes(file.type)) {
      throw new Error(`Invalid file type: ${file.type}`);
    }
    
    if (file.size > maxSize) {
      throw new Error('File size exceeds 50MB limit');
    }
  }

  async processPDFStoryboard(pdfFile: File): Promise<StoryboardPanel[]> {
    const pdfPages = await this.extractPDFPages(pdfFile);
    const panels: StoryboardPanel[] = [];
    
    for (let i = 0; i < pdfPages.length; i++) {
      const page = pdfPages[i];
      const processed = await this.processStoryboardUpload(
        page,
        'generated-shot-id',
        { frameNumber: i + 1 }
      );
      
      panels.push({
        id: processed.id,
        imageUrl: processed.originalUrl,
        thumbnailUrl: processed.thumbnailUrl,
        frameNumber: i + 1,
        annotations: [],
        version: 1
      });
    }
    
    return panels;
  }
}
```

### Visual Context Integration
```typescript
class VisualContextEngine {
  private similarityDetector: VisualSimilarityDetector;
  private continuityChecker: ContinuityChecker;
  private styleTransfer: StyleTransferEngine;

  constructor() {
    this.similarityDetector = new VisualSimilarityDetector();
    this.continuityChecker = new ContinuityChecker();
    this.styleTransfer = new StyleTransferEngine();
  }

  async analyzeVisualContext(storyboard: Storyboard): Promise<VisualAnalysis> {
    const analysis = {
      visualStyle: await this.analyzeStyle(storyboard),
      continuity: await this.checkContinuity(storyboard),
      recommendations: await this.generateRecommendations(storyboard)
    };

    return analysis;
  }

  async checkContinuity(storyboard: Storyboard): Promise<ContinuityReport> {
    const shots = storyboard.shots;
    const continuityIssues = [];

    // Check lighting continuity
    const lightingConsistency = await this.checkLightingConsistency(shots);
    if (!lightingConsistency.isConsistent) {
      continuityIssues.push({
        type: 'lighting',
        severity: 'medium',
        description: 'Lighting direction changes between shots',
        recommendations: lightingConsistency.recommendations
      });
    }

    // Check character positioning
    const positioningConsistency = await this.checkCharacterPositioning(shots);
    if (!positioningConsistency.isConsistent) {
      continuityIssues.push({
        type: 'positioning',
        severity: 'high',
        description: 'Character position jumps between shots',
        recommendations: positioningConsistency.recommendations
      });
    }

    return {
      isConsistent: continuityIssues.length === 0,
      issues: continuityIssues,
      suggestions: this.generateContinuitySuggestions(continuityIssues)
    };
  }

  async generateStyleRecommendations(storyboard: Storyboard): Promise<StyleRecommendation[]> {
    const styleAnalysis = await this.analyzeVisualStyle(storyboard);
    
    return [
      {
        category: 'color_palette',
        recommendation: `Use ${styleAnalysis.dominantColors.join(', ')} throughout sequence`,
        confidence: 0.92
      },
      {
        category: 'lighting',
        recommendation: `Maintain ${styleAnalysis.lightingStyle} for emotional consistency`,
        confidence: 0.88
      },
      {
        category: 'composition',
        recommendation: `Apply ${styleAnalysis.compositionStyle} framing for visual flow`,
        confidence: 0.85
      }
    ];
  }
}
```

### Canvas Integration
```typescript
class CanvasStoryboardIntegration {
  private canvasStore: CanvasStore;
  private nodeManager: NodeManager;
  private visualRenderer: VisualRenderer;

  constructor(canvasStore: CanvasStore) {
    this.canvasStore = canvasStore;
    this.nodeManager = new NodeManager();
    this.visualRenderer = new VisualRenderer();
  }

  async attachStoryboardToNode(
    nodeId: string,
    storyboard: Storyboard
  ): Promise<void> {
    const node = this.canvasStore.getNode(nodeId);
    
    if (!node || node.type !== 'shot') {
      throw new Error('Invalid node type for storyboard attachment');
    }

    // Update node with storyboard data
    const updatedNode = {
      ...node,
      data: {
        ...node.data,
        storyboard: {
          id: storyboard.id,
          thumbnailUrl: storyboard.panels[0]?.thumbnailUrl,
          panelCount: storyboard.panels.length,
          hasAnimatic: !!storyboard.animatic
        }
      }
    };

    await this.canvasStore.updateNode(updatedNode);
    
    // Generate thumbnail for canvas display
    await this.generateNodeThumbnail(nodeId, storyboard.panels[0]);
  }

  async createVisualReferenceNode(
    position: Position,
    storyboardPanel: StoryboardPanel
  ): Promise<string> {
    const node = await this.nodeManager.createNode({
      type: 'visual_reference',
      position,
      data: {
        imageUrl: storyboardPanel.thumbnailUrl,
        originalUrl: storyboardPanel.imageUrl,
        annotations: storyboardPanel.annotations,
        framingData: storyboardPanel.framingData,
        compositionData: storyboardPanel.compositionData
      }
    });

    return node.id;
  }

  async syncStoryboardChanges(storyboard: Storyboard): Promise<void> {
    // Find all nodes using this storyboard
    const affectedNodes = this.canvasStore.findNodesByStoryboard(storyboard.id);
    
    for (const node of affectedNodes) {
      await this.updateNodeThumbnail(node.id, storyboard.panels[0]);
    }
  }
}
```

### Annotation System
```typescript
class AnnotationEngine {
  private annotationStore: AnnotationStore;
  private drawingCanvas: DrawingCanvas;

  constructor() {
    this.annotationStore = new AnnotationStore();
    this.drawingCanvas = new DrawingCanvas();
  }

  async createAnnotation(
    storyboardPanel: StoryboardPanel,
    annotation: AnnotationRequest
  ): Promise<Annotation> {
    const annotationData = {
      id: uuid.v4(),
      type: annotation.type,
      position: annotation.position,
      text: annotation.text,
      drawing: annotation.drawing,
      meta: annotation.meta,
      createdAt: new Date(),
      author: annotation.author
    };

    await this.annotationStore.save(storyboardPanel.id, annotationData);
    
    return annotationData;
  }

  async renderAnnotations(
    storyboardPanel: StoryboardPanel,
    container: HTMLElement
  ): Promise<void> {
    const annotations = await this.annotationStore.get(storyboardPanel.id);
    
    annotations.forEach(annotation => {
      this.renderAnnotation(annotation, container);
    });
  }

  private renderAnnotation(annotation: Annotation, container: HTMLElement): void {
    const annotationElement = document.createElement('div');
    annotationElement.className = `annotation annotation-${annotation.type}`;
    annotationElement.style.left = `${annotation.position.x}%`;
    annotationElement.style.top = `${annotation.position.y}%`;
    
    if (annotation.type === 'text') {
      annotationElement.textContent = annotation.text;
    } else if (annotation.type === 'drawing') {
      this.drawingCanvas.render(annotation.drawing, annotationElement);
    }
    
    container.appendChild(annotationElement);
  }
}

interface Annotation {
  id: string;
  type: 'text' | 'drawing' | 'arrow' | 'highlight' | 'measurement';
  position: { x: number; y: number };
  text?: string;
  drawing?: DrawingData;
  meta: {
    color: string;
    size: number;
    opacity: number;
  };
  createdAt: Date;
  author: string;
}
```

### Continuity Engine
```typescript
class ContinuityEngine {
  private visualAnalyzer: VisualAnalyzer;
  private styleTransfer: StyleTransferEngine;

  constructor() {
    this.visualAnalyzer = new VisualAnalyzer();
    this.styleTransfer = new StyleTransferEngine();
  }

  async analyzeSequenceContinuity(
    storyboards: Storyboard[]
  ): Promise<ContinuityReport> {
    const report: ContinuityReport = {
      isConsistent: true,
      issues: [],
      suggestions: []
    };

    const issues = await this.detectContinuityIssues(storyboards);
    
    if (issues.length > 0) {
      report.isConsistent = false;
      report.issues = issues;
      report.suggestions = await this.generateContinuitySuggestions(issues);
    }

    return report;
  }

  private async detectContinuityIssues(
    storyboards: Storyboard[]
  ): Promise<ContinuityIssue[]> {
    const issues: ContinuityIssue[] = [];

    // Check lighting continuity
    const lightingIssues = await this.checkLightingContinuity(storyboards);
    issues.push(...lightingIssues);

    // Check character positioning
    const positioningIssues = await this.checkCharacterPositioning(storyboards);
    issues.push(...positioningIssues);

    // Check prop placement
    const propIssues = await this.checkPropPlacement(storyboards);
    issues.push(...propIssues);

    return issues;
  }

  private async checkLightingContinuity(
    storyboards: Storyboard[]
  ): Promise<ContinuityIssue[]> {
    const issues: ContinuityIssue[] = [];
    
    for (let i = 1; i < storyboards.length; i++) {
      const prev = storyboards[i - 1];
      const curr = storyboards[i];
      
      const prevLighting = await this.analyzeLighting(prev.panels[0]);
      const currLighting = await this.analyzeLighting(curr.panels[0]);
      
      if (this.hasSignificantLightingChange(prevLighting, currLighting)) {
        issues.push({
          type: 'lighting',
          severity: 'medium',
          description: `Lighting direction changes from ${prevLighting.direction} to ${currLighting.direction}`,
          affectedShots: [prev.id, curr.id],
          recommendations: [
            'Adjust lighting to maintain consistency',
            'Consider transition shot for lighting change'
          ]
        });
      }
    }
    
    return issues;
  }
}

interface ContinuityReport {
  isConsistent: boolean;
  issues: ContinuityIssue[];
  suggestions: ContinuitySuggestion[];
}

interface ContinuityIssue {
  type: 'lighting' | 'positioning' | 'prop-placement' | 'color' | 'style';
  severity: 'low' | 'medium' | 'high';
  description: string;
  affectedShots: string[];
  recommendations: string[];
}
```

### API Endpoints

#### Storyboard Management
```python
POST /api/v1/storyboards/upload
{
  "shot_id": "shot-123",
  "file": "base64_encoded_image",
  "type": "storyboard",
  "metadata": {
    "frame_number": 1,
    "framing_data": {...},
    "composition_data": {...}
  }
}

POST /api/v1/storyboards/{storyboard_id}/annotations
{
  "type": "text",
  "position": {"x": 0.5, "y": 0.3},
  "text": "Focus on character's expression",
  "color": "#ff0000"
}

GET /api/v1/storyboards/continuity/{sequence_id}

PUT /api/v1/storyboards/{storyboard_id}/panels/{panel_id}
{
  "framing_data": {
    "shot_size": "close_up",
    "angle": "low_angle"
  }
}
```

### Version Management
```typescript
class StoryboardVersionManager {
  private versionStore: VersionStore;
  private diffEngine: DiffEngine;

  constructor() {
    this.versionStore = new VersionStore();
    this.diffEngine = new DiffEngine();
  }

  async createVersion(
    storyboard: Storyboard,
    changes: Partial<Storyboard>,
    author: string
  ): Promise<StoryboardVersion> {
    const newVersion = {
      id: uuid.v4(),
      storyboardId: storyboard.id,
      versionNumber: storyboard.version + 1,
      changes,
      author,
      createdAt: new Date(),
      diff: await this.diffEngine.calculate(storyboard, changes)
    };

    await this.versionStore.save(newVersion);
    return newVersion;
  }

  async getVersionHistory(storyboardId: string): Promise<StoryboardVersion[]> {
    return await this.versionStore.getHistory(storyboardId);
  }

  async rollbackToVersion(
    storyboardId: string,
    versionNumber: number
  ): Promise<Storyboard> {
    const versions = await this.getVersionHistory(storyboardId);
    const targetVersion = versions.find(v => v.versionNumber === versionNumber);
    
    if (!targetVersion) {
      throw new Error('Version not found');
    }

    return await this.applyVersion(storyboardId, targetVersion);
  }
}
```

### Testing Strategy

#### Visual Analysis Testing
```typescript
class StoryboardTests {
  async testVisualAnalysis() {
    const engine = new VisualContextEngine();
    const storyboard = {
      id: 'test-123',
      panels: [
        {
          imageUrl: 'test-panel-1.jpg',
          framingData: {
            shotSize: 'close_up',
            angle: 'low_angle'
          }
        }
      ]
    };

    const analysis = await engine.analyzeVisualContext(storyboard);
    
    expect(analysis.visualStyle).toBeDefined();
    expect(analysis.continuity).toBeDefined();
    expect(analysis.recommendations).toBeInstanceOf(Array);
  }

  async testContinuityDetection() {
    const engine = new ContinuityEngine();
    const storyboards = [
      {
        id: 'shot-1',
        panels: [{ lighting: { direction: 'left', intensity: 0.8 } }]
      },
      {
        id: 'shot-2', 
        panels: [{ lighting: { direction: 'right', intensity: 0.3 } }]
      }
    ];

    const report = await engine.analyzeSequenceContinuity(storyboards);
    
    expect(report.issues).toHaveLength(1);
    expect(report.issues[0].type).toBe('lighting');
    expect(report.suggestions).toHaveLength(1);
  }

  async testCanvasIntegration() {
    const integration = new CanvasStoryboardIntegration();
    const storyboard = {
      id: 'storyboard-123',
      panels: [
        {
          thumbnailUrl: 'test-thumb.jpg',
          imageUrl: 'test-original.jpg'
        }
      ]
    };

    await integration.attachStoryboardToNode('shot-node-1', storyboard);
    
    const node = await integration.getNode('shot-node-1');
    expect(node.data.storyboard).toBeDefined();
    expect(node.data.storyboard.thumbnailUrl).toBe('test-thumb.jpg');
  }
}
```

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 5-6 (Phase 3)**

## Dependencies
- **STORY-083**: Expanded Asset System for asset management
- **STORY-084**: Structured GenerativeShotList for shot data
- **STORY-086**: Breakdown View Interface for workflow integration
- **Image Processing**: Processing pipeline for storyboards
- **Canvas Integration**: Node-based display system
- **Cloud Storage**: File storage and retrieval
- **Visual Analysis**: AI-powered visual understanding

## Success Criteria
- Storyboard upload working for all supported formats
- Visual context display on canvas nodes functional
- Continuity analysis accuracy 90%+
- Annotation system supports all annotation types
- Version management tracks all changes
- Performance tested with 1000+ storyboard panels
- Pre-vis video integration working
- User acceptance testing passed with directors
- Cross-platform compatibility verified

## Future Enhancements
- **AI Storyboard Generation**: Automatic panel creation from text
- **3D Pre-vis Integration**: Blender/Unreal Engine connections
- **Collaborative Storyboarding**: Real-time multi-user editing
- **VR Pre-vis**: Virtual reality scene planning
- **Shot List Sync**: Automatic storyboard-to-shot-list conversion
- **Professional Integration**: Storyboard Pro, ShotGrid connections