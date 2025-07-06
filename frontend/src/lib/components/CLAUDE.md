# Components Directory

This directory contains all reusable Svelte components for the Auteur Movie Director frontend application.

## Directory Structure

### `/asset`

Asset management components for browsing, filtering, and displaying project assets.

- `AssetBrowser.svelte` - Main asset browser in left panel
- `AssetFilters.svelte` - Category filtering for assets view
- `AssetGrid.svelte` - Grid display of asset cards

### `/common`

Shared utility components used across the application.

- `TaskProgress.svelte` - Progress bar component for async tasks
- `WebSocketStatus.svelte` - WebSocket connection status indicator

### `/layout`

Core layout components that structure the application.

- `ThreePanelLayout.svelte` - Main three-panel layout container
- `MainViewContainer.svelte` - Tab system container for center panel
- `TabBar.svelte` - Reusable tab bar component

### `/progress`

Progress and notification system components.

- `ProgressArea.svelte` - Main progress area in right panel
- `TaskProgress.svelte` - Individual task progress display
- `NotificationItem.svelte` - Notification display component

### `/project`

Project management components.

- `ProjectBrowser.svelte` - Hierarchical project browser
- `ProjectTree.svelte` - Tree structure for project hierarchy
- `NewProjectDialog.svelte` - Dialog for creating new projects

### `/properties`

Properties inspector system for context-sensitive editing.

- `PropertiesInspector.svelte` - Main properties panel
- `PropertyGroup.svelte` - Collapsible property groups
- `PropertyEditor.svelte` - Individual property editing

### `/scene`

Scene management components (placeholder for future implementation).

- `SceneHierarchy.svelte` - Scene structure display
- `ShotList.svelte` - Shot listing component

### `/settings`

Settings management components.

- `SettingsSection.svelte` - Settings section display

### `/upload`

File upload components.

- `FileUpload.svelte` - Drag-and-drop file upload
- `CharacterUploadDialog.svelte` - Character asset upload dialog

### `/views`

Main view components for tab system.

- `CanvasView.svelte` - Production canvas view (placeholder)
- `SceneView.svelte` - Scene management view
- `AssetsView.svelte` - Asset management view
- `SettingsView.svelte` - Settings management view

## Component Guidelines

1. **Props**: All components should have typed props using TypeScript
2. **Events**: Use `createEventDispatcher` for custom events
3. **Stores**: Import stores from `$lib/stores` for state management
4. **Styling**: Use component-scoped styles with CSS variables for theming
5. **Accessibility**: Include proper ARIA attributes and keyboard navigation
