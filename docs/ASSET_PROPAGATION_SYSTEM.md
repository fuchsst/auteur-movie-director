# Asset Propagation System - STORY-089 Implementation

## Overview

The Asset Propagation System is a comprehensive solution for managing assets across the story hierarchy in Auteur Movie Director. It provides inheritance, overrides, usage tracking, and resolution for generative processes.

## System Architecture

### Hierarchy Levels
The system supports a 6-level hierarchy:
- **PROJECT**: Global project assets
- **ACT**: Act-specific assets
- **CHAPTER**: Chapter-level assets
- **SCENE**: Scene-specific assets
- **SHOT**: Shot-level assets
- **TAKE**: Individual take assets

### Asset Types
- **character**: Character definitions and models
- **style**: Visual style guides and preferences
- **location**: Location assets and environments
- **prop**: Props and objects used in scenes
- **wardrobe**: Clothing and costume assets
- **vehicle**: Vehicle assets
- **set_dressing**: Environmental decoration
- **sfx**: Special effects
- **sound**: Sound effects
- **music**: Musical assets and scores

### Propagation Modes
- **INHERIT**: Assets flow down from parent levels
- **OVERRIDE**: Specific level can override inherited assets
- **MERGE**: Combine assets from multiple levels
- **BLOCK**: Prevent inheritance of specific assets

## API Endpoints

### Asset Management
- `POST /api/v1/asset-propagation/assets` - Add asset to hierarchy level
- `GET /api/v1/asset-propagation/resolve/{project}/{level}/{level_id}` - Resolve assets for a level
- `GET /api/v1/asset-propagation/resolve/generation/{project}/{level}/{level_id}` - Get assets formatted for generation

### Rules Management
- `POST /api/v1/asset-propagation/rules` - Add custom propagation rules
- `GET /api/v1/asset-propagation/hierarchy/levels` - Get available hierarchy levels

### Usage Tracking
- `GET /api/v1/asset-propagation/usage/{project}/{asset_id}` - Get asset usage information
- `GET /api/v1/asset-propagation/validate/{project}` - Validate asset consistency

### State Management
- `POST /api/v1/asset-propagation/save/{project}` - Save propagation state
- `POST /api/v1/asset-propagation/load/{project}` - Load propagation state
- `GET /api/v1/asset-propagation/export/{project}` - Export complete state

## Frontend Components

### AssetPropagationPanel.svelte
Main UI component for displaying and managing asset propagation:
- Shows resolved assets for any hierarchy level
- Displays inheritance and override information
- Real-time updates via WebSocket
- Refresh functionality

### Store Integration
- `asset-propagation.ts` - Main store for state management
- `asset-propagation.ts` - API service layer
- Reactive updates across all components

## Usage Examples

### Adding an Asset
```typescript
await assetPropagationService.addAssetToContext({
  projectId: 'my_project',
  level: HierarchyLevel.SCENE,
  levelId: 'scene_1',
  assetId: 'hero_prop',
  assetType: 'prop',
  overrideData: { description: 'Hero\'s signature weapon' }
});
```

### Resolving Assets
```typescript
const resolved = await assetPropagationService.resolveAssets(
  'my_project',
  HierarchyLevel.SHOT,
  'shot_1'
);
```

### Getting Generation Context
```typescript
const context = await assetPropagationService.resolveForGeneration(
  'my_project',
  HierarchyLevel.TAKE,
  'take_1'
);
// Returns formatted data for AI generation
```

## Configuration

### Default Propagation Rules
The system includes sensible defaults:
- Characters inherit from project to take
- Styles inherit from project to take
- Locations inherit from scene to take
- Props can override at scene level
- Wardrobe can override at shot level

### Custom Rules
Custom rules can be added for specific project needs:
```typescript
await assetPropagationService.addPropagationRule({
  assetType: 'prop',
  sourceLevel: HierarchyLevel.SCENE,
  targetLevel: HierarchyLevel.SHOT,
  propagationMode: PropagationMode.OVERRIDE,
  priority: 10
});
```

## Testing

### Backend Tests
- Unit tests for all service methods
- API endpoint integration tests
- State persistence tests
- Error handling validation

### Frontend Tests
- Component rendering tests
- Store state management tests
- API integration tests
- UI interaction tests

### Integration Tests
- Full end-to-end workflow testing
- Cross-level asset propagation validation
- Generation context accuracy
- State export/import roundtrip

## File Structure

### Backend
- `app/services/asset_propagation.py` - Core service implementation
- `app/api/v1/asset_propagation.py` - REST API endpoints
- `app/models/asset_types.py` - Asset type definitions
- `tests/test_asset_propagation.py` - Comprehensive test suite

### Frontend
- `src/lib/types/asset-propagation.ts` - TypeScript type definitions
- `src/lib/services/asset-propagation.ts` - API service layer
- `src/lib/stores/asset-propagation.ts` - Svelte store
- `src/lib/components/asset-propagation/AssetPropagationPanel.svelte` - Main UI component

## Performance Considerations

- **Caching**: Asset resolution results are cached per level
- **Batch Operations**: Support for bulk asset operations
- **Lazy Loading**: Assets loaded on-demand
- **State Persistence**: Efficient JSON-based state storage

## Security

- Input validation on all endpoints
- Type-safe API contracts
- Error handling with proper HTTP status codes
- Sanitization of asset metadata

## Future Enhancements

- **WebSocket Real-time Updates**: Live asset changes across clients
- **Asset Versioning**: Track changes to assets over time
- **Collaborative Editing**: Multi-user asset management
- **Asset Templates**: Predefined asset collections
- **AI-Driven Suggestions**: Intelligent asset recommendations based on context

## Migration Guide

For existing projects, the system can:
1. Import existing assets from project structure
2. Apply default propagation rules
3. Validate consistency across hierarchy
4. Export state for backup/transfer

## Support

For issues or questions:
- Check the test suite for usage examples
- Review API documentation at `/api/docs`
- Consult the development guide in `CLAUDE.md`