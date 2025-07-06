# Stores Directory

This directory contains Svelte stores for global state management in the Auteur Movie Director frontend.

## Store Files

### `app.ts`

Application-wide state including current project, workspace configuration, and initialization logic.

- `currentProject` - Currently selected project
- `workspaceConfig` - Workspace settings
- `initializeApp()` - App initialization function

### `assets.ts`

Asset management store for tracking project assets.

- `addAsset()` - Add new asset to project
- `removeAsset()` - Remove asset
- `getProjectAssets()` - Get assets for specific project

### `index.ts`

Main export file that re-exports all stores for convenient importing.

### `notifications.ts`

Notification system store for managing user notifications.

- `add()` - Add new notification
- `dismiss()` - Remove notification
- `markRead()` - Mark as read
- `markAllRead()` - Mark all as read
- `clearRead()` - Clear read notifications

### `selection.ts`

Selection context store for properties inspector.

- `selectProject()` - Select project context
- `selectAsset()` - Select asset context
- `selectNode()` - Select node context (future)
- `clearSelection()` - Clear current selection

### `tasks.ts`

Task management store for tracking async operations.

- `add()` - Add new task
- `updateProgress()` - Update task progress
- `cancel()` - Cancel running task
- `clearCompleted()` - Clear completed tasks

### `views.ts`

View state management for tab system.

- `setActiveTab()` - Set active tab
- `saveViewState()` - Save tab-specific state
- `getViewState()` - Retrieve tab state

### `websocket.ts`

WebSocket connection state management.

- `connected` - Connection status
- `connecting` - Connection in progress
- `error` - Error state
- `reconnectAttempts` - Reconnection counter

## Store Patterns

### Writable Stores

Most stores use Svelte's `writable` for simple state management:

```typescript
const { subscribe, update } = writable<StoreType>(initialValue);
```

### Custom Store Methods

Stores expose custom methods for state manipulation:

```typescript
return {
  subscribe,
  customMethod() {
    update((state) => ({ ...state, modified: true }));
  }
};
```

### LocalStorage Persistence

Some stores persist to localStorage for session continuity:

```typescript
if (browser) {
  localStorage.setItem('storeKey', JSON.stringify(state));
}
```

### Store Composition

Stores can be composed and derived from other stores:

```typescript
export const derivedStore = derived([storeA, storeB], ([$a, $b]) => computeValue($a, $b));
```
