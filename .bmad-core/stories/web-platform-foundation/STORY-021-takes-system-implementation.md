# STORY-021: Takes System Implementation

## Story
As a director, I need a non-destructive versioning system for generated content that allows me to create multiple "takes" of shots without losing previous versions, similar to traditional film production.

## Acceptance Criteria
- [x] Deterministic take naming system (e.g., shot_001_take_001.mp4)
- [x] Takes are stored in dedicated directories within shots
- [x] Non-destructive - new takes don't overwrite existing ones
- [x] Takes gallery shows all versions with thumbnails
- [x] Active take selection mechanism
- [x] Integration with Git LFS for media file storage
- [x] Metadata preserved for each take (generation parameters)

## Technical Details

### Directory Structure

```
03_Chapter_Name/
  01_Scene_Name/
    001_Shot_Description/
      takes/
        take_001/
          shot_001_take_001.mp4
          shot_001_take_001_metadata.json
          shot_001_take_001_thumbnail.png
        take_002/
          shot_001_take_002.mp4
          shot_001_take_002_metadata.json
          shot_001_take_002_thumbnail.png
      active_take -> takes/take_001/  # Symlink to active take
```

### Take Metadata Schema

```typescript
interface TakeMetadata {
  id: string;                    // "take_001"
  shotId: string;                // "001_Shot_Description"
  created: string;               // ISO timestamp
  duration: number;              // Video duration in seconds
  resolution: {
    width: number;
    height: number;
  };
  generationParams: {
    model: string;
    seed: number;
    prompt: string;
    negativePrompt?: string;
    steps: number;
    cfg: number;
    // Model-specific parameters
    [key: string]: any;
  };
  resources: {
    vramUsed: number;           // Peak VRAM in MB
    generationTime: number;     // Time in seconds
    quality: 'draft' | 'standard' | 'high';
  };
  status: 'generating' | 'complete' | 'failed';
  error?: string;
}
```

### API Endpoints

#### Create New Take
```typescript
POST /api/projects/{projectId}/shots/{shotId}/takes
Body: {
  generationParams: GenerationParams;
  quality: QualityLevel;
}
Response: {
  takeId: string;
  status: 'queued';
}
```

#### List Takes
```typescript
GET /api/projects/{projectId}/shots/{shotId}/takes
Response: {
  takes: Take[];
  activeTakeId: string;
}
```

#### Set Active Take
```typescript
PUT /api/projects/{projectId}/shots/{shotId}/active-take
Body: {
  takeId: string;
}
```

#### Delete Take
```typescript
DELETE /api/projects/{projectId}/shots/{shotId}/takes/{takeId}
// Marks as deleted but doesn't remove files immediately
```

### Frontend Components

#### Takes Gallery Component
```svelte
<script lang="ts">
  export let shotId: string;
  export let takes: Take[];
  export let activeTakeId: string;
  
  function selectTake(takeId: string) {
    // Update active take
  }
  
  function generateNewTake() {
    // Open generation dialog
  }
</script>

<div class="takes-gallery">
  <div class="takes-header">
    <h3>Takes ({takes.length})</h3>
    <button on:click={generateNewTake}>New Take</button>
  </div>
  
  <div class="takes-grid">
    {#each takes as take}
      <div 
        class="take-item"
        class:active={take.id === activeTakeId}
        on:click={() => selectTake(take.id)}
      >
        <img src={take.thumbnailUrl} alt={take.id} />
        <div class="take-info">
          <span class="take-id">{take.id}</span>
          <span class="take-date">{formatDate(take.created)}</span>
        </div>
      </div>
    {/each}
  </div>
</div>
```

### Git LFS Integration

#### .gitattributes Template
```
# Video files
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text

# Image sequences
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.exr filter=lfs diff=lfs merge=lfs -text

# Audio files
*.wav filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text

# Exclude thumbnails from LFS
*_thumbnail.png !filter !diff !merge
```

### Take Naming Convention

```typescript
function generateTakeName(shotId: string, takeNumber: number): string {
  const paddedTakeNumber = String(takeNumber).padStart(3, '0');
  return `${shotId}_take_${paddedTakeNumber}`;
}

function getNextTakeNumber(existingTakes: string[]): number {
  const numbers = existingTakes
    .map(t => t.match(/take_(\d+)/)?.[1])
    .filter(Boolean)
    .map(Number);
  return Math.max(0, ...numbers) + 1;
}
```

### Thumbnail Generation

```python
async def generate_thumbnail(video_path: Path, output_path: Path):
    """Extract thumbnail from video at 1 second mark"""
    import ffmpeg
    
    stream = ffmpeg.input(str(video_path), ss=1)
    stream = ffmpeg.output(
        stream, 
        str(output_path),
        vframes=1,
        vf='scale=320:180'
    )
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
```

### Active Take Management

- Use symlinks on Unix systems
- Use junction points on Windows
- Fallback to JSON pointer file if symlinks unavailable
- Update project.json with active take reference

### Storage Optimization

- Implement take cleanup for old/unused takes
- Compress metadata JSON files
- Generate multiple thumbnail sizes
- Use hardlinks for duplicate files

## Dependencies
- Git LFS properly configured (STORY-017)
- File Management API (STORY-004)
- Function Runner for generation (STORY-013)

## Story Points: 3

## Priority: High

## Status: ✅ Completed

## Related Stories
- STORY-004: File Management API
- STORY-013: Function Runner Foundation
- STORY-017: Git LFS Integration