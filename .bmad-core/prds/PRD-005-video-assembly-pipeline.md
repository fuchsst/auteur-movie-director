# Product Requirements Document: Video Assembly Pipeline

## Executive Summary

### Business Justification
The Video Assembly Pipeline transforms the Generative Media Studio from a shot creation tool into a complete film production platform. By implementing the VSEAssemblerNode as the terminal node in visual workflows, this system enables seamless progression from individual shots to finished films:
- **Complete Creative Journey**: From first shot to final export in one platform
- **Professional Standards**: Industry-standard EDL format for compatibility
- **Zero Technical Barriers**: Visual assembly replaces complex editing software
- **Instant Gratification**: See assembled sequences in real-time
- **Future-Proof Workflow**: Export to any professional NLE when needed

### Target User Personas
- **Independent Filmmakers**: Complete films without expensive software
- **Content Creators**: Rapid assembly for social media content
- **Creative Agencies**: Batch processing for multiple versions
- **Film Students**: Learn complete production pipeline
- **Professional Editors**: Quick rough cuts before refinement

### Expected Impact
- Enable complete film production within the platform
- Reduce assembly time from hours to minutes
- Eliminate software switching for basic edits
- Establish EDL as bridge to professional tools
- Democratize film finishing for all creators

## Problem Statement

### Current Limitations
1. **Broken Workflow**: Generated shots trapped without assembly
2. **Software Dependency**: Requires expensive NLE software
3. **Context Loss**: Metadata and parameters lost in export
4. **Manual Process**: Each shot must be individually placed
5. **Version Chaos**: Multiple exports for small changes

### Pain Points
- "I have 50 great shots but no way to combine them"
- "Exporting to Premiere breaks my creative flow"
- "I lost track of which take I used in the edit"
- "Changing one shot means re-exporting everything"
- "My client wants three versions with different music"

### Workflow Gaps
- No visual connection between generation and assembly
- Missing bridge from AI creation to traditional editing
- No automated assembly based on creative intent
- Lack of non-destructive editing within platform
- No batch export for multiple formats

## Solution Overview

### VSEAssemblerNode: The Terminal Node
Implement a visual assembly system where shots connect directly to a final render node:

**Visual Workflow**
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Shot 1  │────▶│ Shot 2  │────▶│ Shot 3  │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
   Take 3          Take 1          Take 2
     └───────────────┴───────────────┘
                     │
                     ▼
              ┌─────────────┐
              │VSEAssembler │──▶ Final Video
              └─────────────┘
```

### Core Components

1. **VSEAssemblerNode**: Terminal node that accepts shot sequence
2. **Take Resolver**: Automatically selects active takes
3. **EDL Compiler**: Generates industry-standard CMX3600 format
4. **MoviePy Engine**: Programmatic video assembly
5. **Export Manager**: Multi-format output system

## User Stories & Acceptance Criteria

### Epic 1: Visual Sequence Assembly
**As a** filmmaker  
**I want to** connect shots visually to create sequences  
**So that** I see my film structure before rendering

**Acceptance Criteria:**
- [ ] Drag connection from shot outputs to VSEAssembler
- [ ] Visual preview of connected sequence
- [ ] Reorder by reconnecting nodes
- [ ] See total runtime dynamically
- [ ] Validate sequence before render

### Epic 2: Intelligent Take Selection
**As a** creator with multiple takes  
**I want to** easily choose the best version  
**So that** I get optimal results

**Acceptance Criteria:**
- [ ] Active take highlighted in node
- [ ] Quick take switching in sequence
- [ ] Take metadata preserved in EDL
- [ ] Visual comparison mode
- [ ] Bulk take operations

### Epic 3: One-Click Final Render
**As a** user ready to export  
**I want to** create my final video instantly  
**So that** I can share my work

**Acceptance Criteria:**
- [ ] Single "Render Final Video" button
- [ ] Real-time progress indication
- [ ] Automatic output to 06_Exports/
- [ ] Success notification with preview
- [ ] Open in system player option

### Epic 4: Professional EDL Export
**As a** professional editor  
**I want to** continue editing in my NLE  
**So that** I can add advanced effects

**Acceptance Criteria:**
- [ ] Export CMX3600 compliant EDL
- [ ] Preserve all timing information
- [ ] Include source file paths
- [ ] Support reel names
- [ ] Import verified in major NLEs

### Epic 5: Multi-Version Export
**As an** agency creating variants  
**I want to** export multiple versions efficiently  
**So that** I meet different requirements

**Acceptance Criteria:**
- [ ] Save assembly as template
- [ ] Batch export different formats
- [ ] Swap audio tracks easily
- [ ] Export settings presets
- [ ] Queue multiple renders

## Technical Requirements

### VSEAssemblerNode Specification

#### Node Interface Details
- **Description**: Terminal node for sequence compilation and final video rendering
- **Input Ports**: 
  - Sequence In (EDL) - Receives Edit Decision List data from connected sequence
- **On-Node Parameters**: 
  - "Render Final Video" button - Primary action trigger
  - Status display - Shows current rendering state
- **Output Ports**: 
  - Final Video (Video) - Path to rendered video file
- **Properties Panel (Right Side)**:
  - Output Format dropdown (MP4, MOV, ProRes, WebM)
  - Resolution selector (720p, 1080p, 4K, Original)
  - Bitrate control (Auto, Custom with slider)
  - Frame rate options (24fps, 30fps, 60fps, Match Source)
  - Audio settings (codec, bitrate, channels)
  - Color space handling (sRGB, Rec.709, P3)
  - Render progress bar with time estimate
  - Preview link when complete

#### Visual Placement
The VSEAssemblerNode serves as the visual endpoint of any sequence:
- Positioned at the far right of the canvas
- Larger size than standard nodes to indicate importance
- Distinctive icon/color to mark as terminal node
- Cannot have outgoing connections (terminal only)

### VSEAssemblerNode Implementation
```javascript
class VSEAssemblerNode extends BaseNode {
    constructor() {
        super();
        this.type = 'VSEAssembler';
        this.inputs = {
            sequence: { 
                type: 'EDL',
                required: true,
                description: 'Edit Decision List from sequence'
            }
        };
        this.outputs = {
            video: { type: 'Video', description: 'Final rendered video' }
        };
        this.parameters = {
            format: {
                type: 'select',
                options: ['MP4', 'MOV', 'ProRes', 'WebM'],
                default: 'MP4',
                inPropertiesPanel: true
            },
            resolution: {
                type: 'select',
                options: ['Original', '720p', '1080p', '4K'],
                default: '1080p',
                inPropertiesPanel: true
            },
            bitrate: {
                type: 'slider',
                min: 1, max: 50, default: 10,
                unit: 'Mbps',
                inPropertiesPanel: true
            }
        };
        this.ui = {
            onNodeDisplay: {
                button: {
                    label: 'Render Final Video',
                    icon: 'film',
                    size: 'large',
                    primary: true
                },
                status: {
                    type: 'text',
                    position: 'below-button'
                }
            }
        };
    }
    
    async compile() {
        const shots = this.gatherConnectedShots();
        const edl = await this.generateEDL(shots);
        return edl;
    }
}
```

### EDL Generation Engine
```python
class EDLCompiler:
    def compile_from_sequence(self, shot_sequence, project_settings):
        """Generate CMX3600 EDL from shot sequence"""
        edl = CMX3600()
        edl.title = project_settings['name']
        edl.fcm = 'NON-DROP FRAME'
        
        record_tc = Timecode('01:00:00:00', project_settings['frameRate'])
        
        for idx, shot in enumerate(shot_sequence):
            # Resolve active take
            source_path = shot.get_active_take_path()
            
            # Create EDL event
            event = EDLEvent(
                num=idx + 1,
                reel=f"SHOT{shot.id:03d}",
                track='V',
                edit_type='C',  # Cut
                source_in=Timecode('00:00:00:00'),
                source_out=shot.duration,
                record_in=record_tc,
                record_out=record_tc + shot.duration
            )
            
            # Add source file comment
            event.comments.append(f"* FROM CLIP NAME: {source_path}")
            event.comments.append(f"* GENERATOR: Generative Media Studio")
            event.comments.append(f"* TAKE: {shot.active_take_id}")
            
            edl.add_event(event)
            record_tc = event.record_out
            
        return edl.to_string()
```

### Assembly Pipeline
```python
class VideoAssembler:
    def assemble_from_edl(self, edl_path, output_settings):
        """Assemble final video from EDL using MoviePy"""
        
        # Parse EDL
        edl = EDLParser(edl_path)
        clips = []
        
        # Load and trim clips
        for event in edl.events:
            source_path = self.resolve_source_path(event)
            clip = VideoFileClip(source_path)
            
            # Apply in/out points
            trimmed = clip.subclip(
                event.source_in.to_seconds(),
                event.source_out.to_seconds()
            )
            
            clips.append(trimmed)
        
        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Apply output settings
        output_params = self.get_codec_params(output_settings)
        
        # Export with progress callback
        final_video.write_videofile(
            output_settings['path'],
            fps=output_settings['fps'],
            codec=output_params['codec'],
            audio_codec=output_params['audio_codec'],
            preset=output_params['preset'],
            logger=ProgressLogger(self.websocket)
        )
        
        return output_settings['path']
```

### Real-Time Progress Updates
```javascript
// WebSocket progress relay
class AssemblyProgress {
    constructor(websocket) {
        this.ws = websocket;
        this.startTime = Date.now();
    }
    
    updateProgress(percent, stage) {
        this.ws.send(JSON.stringify({
            type: 'assembly_progress',
            data: {
                percent: percent,
                stage: stage,  // 'analyzing', 'rendering', 'encoding'
                elapsed: Date.now() - this.startTime,
                estimated: this.estimateRemaining(percent)
            }
        }));
    }
}
```

### Progress Area Integration
The VSEAssemblerNode provides detailed feedback in the right panel's Progress Area:

#### During Rendering
- **Stage Indicators**: "Analyzing shots", "Building timeline", "Encoding video"
- **Progress Bar**: Real-time percentage with smooth animations
- **Time Display**: "2:45 elapsed, ~1:30 remaining"
- **Throughput Metrics**: "Processing 24 fps, 15 Mbps"
- **Cancel Option**: Stop rendering with cleanup

#### Post-Rendering
- **Completion Notification**: "Video rendered successfully!"
- **Preview Thumbnail**: First frame of final video
- **Quick Actions**: 
  - "Open in Player" - Launch system video player
  - "Show in Folder" - Navigate to export location
  - "Copy Path" - For external use
- **File Details**: Size, duration, format, location

## File Structure Integration

### Project Directory Usage
```
/Projects/MyFilm/
├── 03_Renders/                    # Source shots
│   ├── shots/
│   │   ├── SHOT-001_v01_take01.mp4
│   │   ├── SHOT-001_v01_take02.mp4
│   │   └── SHOT-002_v01_take01.mp4
├── 04_Project_Files/              # Assembly data
│   ├── assemblies/
│   │   ├── main_sequence.edl
│   │   ├── main_sequence.json
│   │   └── alt_ending.edl
└── 06_Exports/                    # Final outputs
    ├── MyFilm_Final_2024-01-02_1080p.mp4
    ├── MyFilm_Final_2024-01-02_4K.mov
    └── MyFilm_Final_2024-01-02_ProRes.mov
```

## Success Metrics

### Performance Metrics
- **Assembly Speed**: Real-time or faster
- **EDL Generation**: < 100ms for 100 shots
- **Preview Generation**: < 2 seconds
- **Export Time**: 1:1 with playback (1x speed)
- **Memory Usage**: < 2GB for hour-long project

### Quality Metrics
- **Frame Accuracy**: 100% precision
- **Audio Sync**: Zero drift
- **Color Fidelity**: Bit-perfect transfer
- **Metadata Preservation**: All parameters retained
- **Format Compliance**: Professional standards met

### Usability Metrics
- **Time to First Export**: < 2 minutes
- **Success Rate**: 99%+ completion
- **User Satisfaction**: 4.7+ stars
- **Support Requests**: < 1% of users
- **Feature Discovery**: 90% use EDL export

## Risk Assessment

### Technical Risks
1. **Memory Management**: Long films exhaust RAM
   - *Mitigation*: Streaming architecture, chunk processing
2. **Codec Complexity**: Format incompatibilities
   - *Mitigation*: FFmpeg backend, extensive testing
3. **Render Failures**: Crashes lose progress
   - *Mitigation*: Checkpoint system, resume capability

### Workflow Risks
1. **Quality Expectations**: Users expect NLE features
   - *Mitigation*: Clear positioning as assembly tool
2. **Performance Anxiety**: Slow renders frustrate
   - *Mitigation*: Progress indication, time estimates
3. **Format Confusion**: Too many options overwhelm
   - *Mitigation*: Smart defaults, presets

## Development Roadmap

### Phase 1: Core Assembly (Week 1-2)
- VSEAssemblerNode implementation
- Basic shot concatenation
- MP4 export only
- Progress tracking

### Phase 2: EDL System (Week 3-4)
- CMX3600 generation
- Professional metadata
- Multi-format support
- NLE compatibility testing

### Phase 3: Advanced Features (Week 5-6)
- Audio track management
- Transition effects
- Color space handling
- Batch processing

### Phase 4: Optimization (Week 7-8)
- Streaming pipeline
- GPU acceleration
- Caching system
- Error recovery

## Future Vision

### Intelligent Assembly
- AI-powered rough cuts based on content
- Automatic pacing based on music
- Smart transitions between shots
- Emotion-based sequencing

### Advanced Integration
- Direct upload to platforms
- Cloud rendering options
- Collaborative review tools
- Version control for edits

---

**Document Version**: 2.0  
**Created**: 2025-01-02  
**Last Updated**: 2025-01-02  
**Status**: Final Draft  
**Owner**: Generative Media Studio Product Team