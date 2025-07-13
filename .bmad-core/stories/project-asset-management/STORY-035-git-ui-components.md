# User Story: Git UI Components

**Story ID**: STORY-035  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 8  
**Priority**: Medium  
**Sprint**: Git Sprint (Week 7-8)  

## Story Description

**As a** creative professional  
**I want** to visualize and interact with my project's version history  
**So that** I can understand changes and restore previous versions  

## Acceptance Criteria

### Functional Requirements
- [ ] Visual timeline showing commit history
- [ ] Commit details panel with file changes
- [ ] Diff viewer for text files
- [ ] Media preview for binary changes
- [ ] One-click rollback with confirmation
- [ ] Search commits by message/author/date
- [ ] Filter by file types changed
- [ ] Tag creation and management UI
- [ ] Branch visualization (future)

### Technical Requirements
- [ ] Components in `frontend/src/lib/components/git/`:
  - `GitTimeline.svelte`
  - `CommitDetails.svelte`
  - `DiffViewer.svelte`
  - `RollbackDialog.svelte`
- [ ] Interactive timeline visualization
- [ ] Lazy loading for long histories
- [ ] Real-time updates for new commits
- [ ] Keyboard shortcuts:
  - Up/Down: Navigate commits
  - Enter: Show details
  - R: Rollback to selected
- [ ] Responsive design
- [ ] Performance with 1000+ commits

### Quality Requirements
- [ ] Timeline renders smoothly
- [ ] Diff viewer syntax highlighting
- [ ] Clear visual hierarchy
- [ ] Accessibility compliant
- [ ] Touch-friendly on mobile
- [ ] Graceful error handling

## Implementation Notes

### Technical Approach
1. **Timeline Component**:
   ```svelte
   <script lang="ts">
     import { gitStore } from '$lib/stores/git';
     import CommitNode from './CommitNode.svelte';
     
     export let projectId: string;
     
     let selectedCommit: string | null = null;
     let timelineScale = 'days';  // days, weeks, months
     
     $: commits = $gitStore.getHistory(projectId);
     $: groupedCommits = groupByTime(commits, timelineScale);
   </script>
   
   <div class="git-timeline">
     <div class="timeline-controls">
       <ScaleSelector bind:scale={timelineScale} />
       <SearchBar on:search={filterCommits} />
     </div>
     
     <div class="timeline-track">
       {#each groupedCommits as group}
         <div class="time-group">
           <h3>{group.label}</h3>
           {#each group.commits as commit}
             <CommitNode 
               {commit} 
               selected={commit.hash === selectedCommit}
               on:select={() => selectedCommit = commit.hash}
             />
           {/each}
         </div>
       {/each}
     </div>
     
     {#if selectedCommit}
       <CommitDetails commitHash={selectedCommit} />
     {/if}
   </div>
   ```

2. **Commit Node Design**:
   ```svelte
   <div class="commit-node" class:selected>
     <div class="node-marker" />
     <div class="node-content">
       <p class="message">{commit.message}</p>
       <div class="metadata">
         <span class="author">{commit.author}</span>
         <time>{formatTime(commit.timestamp)}</time>
         <span class="stats">+{commit.additions} -{commit.deletions}</span>
       </div>
     </div>
   </div>
   ```

3. **Rollback Safety**:
   ```svelte
   <ConfirmDialog
     title="Rollback Project?"
     message="This will restore your project to {commit.message}. 
              Current changes will be saved as a new commit."
     dangerous={true}
     on:confirm={performRollback}
   />
   ```

### Dependencies
- STORY-034 (Git service extensions)
- Git history API endpoints
- Diff library for file comparison
- No agent dependencies

### Integration Points
- Consumes Git history API
- Triggers rollback operations
- Updates on auto-commits
- Links to file browser

## Testing Strategy

### Unit Tests
```javascript
test('groups commits by time scale', () => {
  // Test timeline grouping logic
});

test('filters commits by search', () => {
  // Test search functionality
});

test('rollback shows confirmation', () => {
  // Test safety dialog
});
```

### Integration Tests
- Load real project history
- Test rollback operation
- Verify timeline updates
- Test diff viewer accuracy

### Visual Tests
- Timeline layouts
- Commit node states
- Diff viewer themes
- Mobile responsiveness

## Definition of Done
- [ ] Timeline visualization complete
- [ ] Commit details functional
- [ ] Diff viewer implemented
- [ ] Rollback with confirmation
- [ ] Search and filter working
- [ ] Keyboard navigation done
- [ ] Performance optimized
- [ ] All tests passing
- [ ] Code reviewed and approved