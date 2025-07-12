# Manual Testing Checklist - End-to-End Project Flow

## Prerequisites
- [ ] Docker and Docker Compose installed
- [ ] Git and Git LFS configured
- [ ] All services running (`make docker-up` or `npm run docker:up`)
- [ ] Test fixtures available in `tests/fixtures/`

## Service Health Checks
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend API docs at http://localhost:8000/docs
- [ ] WebSocket connects successfully
- [ ] Redis running (`docker-compose exec redis redis-cli ping`)
- [ ] Worker logs show ready state

## Project Creation Flow

### Basic Project Creation
- [ ] Click "New Project" button
- [ ] Enter valid project name
- [ ] Select quality tier (Low/Standard/High)
- [ ] Select narrative structure
- [ ] Submit form
- [ ] Verify redirect to project page
- [ ] Verify project appears in sidebar

### Project Structure Verification
- [ ] Expand project tree in left panel
- [ ] Verify 01_Assets directory with subdirectories
- [ ] Verify 02_Source_Creative directory
- [ ] Verify 03_Renders directory
- [ ] Verify 04_Project_Files directory
- [ ] Check project.json exists in workspace

### Invalid Project Names
- [ ] Try empty project name - should show error
- [ ] Try name with slashes - should show error
- [ ] Try Windows reserved name (CON, PRN) - should show error
- [ ] Try name > 255 characters - should show error
- [ ] Try duplicate name - should show error

## File Operations

### Basic File Upload
- [ ] Navigate to Assets view
- [ ] Click Upload Files
- [ ] Select single image file
- [ ] Verify upload progress shown
- [ ] Verify file appears in asset browser
- [ ] Verify file in correct category folder

### Large File Upload (Git LFS)
- [ ] Upload video file > 50MB
- [ ] Verify Git LFS handles file
- [ ] Check file is LFS pointer in Git
- [ ] Verify file playback works

### Multiple File Upload
- [ ] Select 5+ files at once
- [ ] Verify all files upload
- [ ] Check progress for each file
- [ ] Verify no failed uploads

### Category-Specific Uploads
- [ ] Upload to Characters - verify in 01_Assets/Characters
- [ ] Upload to Styles - verify in 01_Assets/Styles
- [ ] Upload to Locations - verify in 01_Assets/Locations
- [ ] Upload to Music - verify in 01_Assets/Music

## Character Asset Management

### Character Creation
- [ ] Navigate to Assets > Characters
- [ ] Click New Character
- [ ] Enter name and description
- [ ] Add trigger word for LoRA
- [ ] Submit form
- [ ] Verify character card appears

### Base Face Upload
- [ ] Click on character card
- [ ] Upload base face image
- [ ] Verify image preview shown
- [ ] Check file in character directory

### Character Sheet Display
- [ ] View full character sheet
- [ ] Verify metadata displayed
- [ ] Check trigger word shown
- [ ] Verify base face image loads

## WebSocket Real-Time Updates

### Cross-Tab Updates
- [ ] Open project in two browser tabs
- [ ] Create asset in tab 1
- [ ] Verify appears in tab 2 immediately
- [ ] Delete asset in tab 2
- [ ] Verify removed from tab 1

### Task Progress Updates
- [ ] Submit generation task
- [ ] Monitor WebSocket messages in console
- [ ] Verify progress updates received
- [ ] Check completion notification

## Git Integration

### Repository Initialization
- [ ] New project has .git directory
- [ ] Check git status is clean
- [ ] Verify .gitignore configured
- [ ] Verify .gitattributes for LFS

### Git LFS Configuration
- [ ] Check LFS tracks media files
- [ ] Upload large file
- [ ] Verify LFS pointer created
- [ ] Check git lfs ls-files

## Quality Tier Testing

### Low Quality (Draft)
- [ ] Create project with Low quality
- [ ] Submit generation task
- [ ] Verify uses 20 steps
- [ ] Check fast execution time

### Standard Quality
- [ ] Create project with Standard quality
- [ ] Submit generation task
- [ ] Verify uses 30 steps
- [ ] Check balanced execution

### High Quality (Cinematic)
- [ ] Create project with High quality
- [ ] Submit generation task
- [ ] Verify uses 50 steps
- [ ] Check high quality output

## Takes System

### Take Creation
- [ ] Navigate to shot in project tree
- [ ] Create first take
- [ ] Verify take_001 directory created
- [ ] Generate content for take

### Multiple Takes
- [ ] Create second take for same shot
- [ ] Verify take_002 directory
- [ ] Switch between takes
- [ ] Verify non-destructive versioning

## Error Handling

### Network Errors
- [ ] Disconnect network briefly
- [ ] Verify WebSocket reconnects
- [ ] Check no data loss
- [ ] Verify error messages shown

### File System Errors
- [ ] Try uploading to read-only directory
- [ ] Verify graceful error handling
- [ ] Check user-friendly error message

### Concurrent Operations
- [ ] Create multiple projects simultaneously
- [ ] Upload files while creating project
- [ ] Verify no conflicts or corruption

## Performance Testing

### Large Project Handling
- [ ] Create project with 100+ assets
- [ ] Verify UI remains responsive
- [ ] Check asset loading performance
- [ ] Test search/filter speed

### Memory Usage
- [ ] Monitor browser memory usage
- [ ] Upload many large files
- [ ] Verify no memory leaks
- [ ] Check cleanup after deletion

## Cleanup and Deletion

### Project Deletion
- [ ] Delete project from UI
- [ ] Verify removed from sidebar
- [ ] Check workspace directory deleted
- [ ] Verify Git repository removed

### Asset Cleanup
- [ ] Delete individual assets
- [ ] Verify files removed from disk
- [ ] Check Git tracks deletion
- [ ] Verify no orphaned files

## Docker Container Testing

### Container Health
- [ ] Run `docker-compose ps`
- [ ] All containers show healthy
- [ ] Check resource usage reasonable
- [ ] Verify volume mounts working

### Container Restart
- [ ] Restart backend container
- [ ] Verify data persists
- [ ] Check reconnection works
- [ ] Test functionality restored

### Volume Persistence
- [ ] Create project and assets
- [ ] Stop all containers
- [ ] Start containers again
- [ ] Verify all data intact

## Integration Points

### Frontend-Backend Communication
- [ ] API calls succeed
- [ ] Proper error handling
- [ ] Request/response logging
- [ ] CORS configured correctly

### Backend-Worker Communication
- [ ] Tasks queued in Redis
- [ ] Worker picks up tasks
- [ ] Progress updates flow
- [ ] Results stored correctly

### Shared Volume Access
- [ ] Backend writes files
- [ ] Worker can read files
- [ ] Frontend serves files
- [ ] No permission issues

## Sign-off

- [ ] All critical paths tested
- [ ] No blocking issues found
- [ ] Performance acceptable
- [ ] Error handling verified
- [ ] Documentation accurate

**Tested by:** ________________________  
**Date:** ________________________  
**Version:** ________________________  

## Notes
_Record any issues, observations, or recommendations below:_

___________________________________________
___________________________________________
___________________________________________