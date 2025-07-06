# Frontend Library Directory

This directory contains the core library code for the Auteur Movie Director frontend application built with SvelteKit.

## Directory Structure

### `/api`

API client and communication layer.

- `client.ts` - Main API client for backend communication

### `/components`

Reusable Svelte components organized by feature.

- See `/components/CLAUDE.md` for detailed component documentation

### `/services`

Service layer for complex business logic.

- `websocket.ts` - WebSocket client service with auto-reconnection

### `/stores`

Svelte stores for global state management.

- See `/stores/CLAUDE.md` for detailed store documentation

### `/types`

TypeScript type definitions and interfaces.

- See `/types/CLAUDE.md` for detailed type documentation

### `/utils`

Utility functions and helpers (to be created as needed).

## Architecture Principles

### Component Hierarchy

```
App
├── ThreePanelLayout
│   ├── Left Panel
│   │   ├── ProjectBrowser
│   │   └── AssetBrowser
│   ├── Center Panel
│   │   └── MainViewContainer
│   │       └── View Components (Canvas, Scene, Assets, Settings)
│   └── Right Panel
│       ├── PropertiesInspector
│       └── ProgressArea
```

### Data Flow

1. **Stores** manage global application state
2. **Components** subscribe to stores and dispatch events
3. **Services** handle complex operations (WebSocket, API calls)
4. **Types** ensure type safety across the application

### State Management

- **Global State**: Svelte stores in `/stores`
- **Component State**: Local component variables
- **Derived State**: Computed from stores using `derived`
- **Persistent State**: LocalStorage for session continuity

### API Communication

- **REST API**: Via `api/client.ts` for CRUD operations
- **WebSocket**: Real-time updates via `services/websocket.ts`
- **File Uploads**: Multipart form data with progress tracking

## Development Guidelines

### Component Creation

1. Create component in appropriate feature directory
2. Define typed props and events
3. Implement responsive design
4. Add accessibility attributes
5. Document with comments

### Store Usage

1. Import stores using `$` prefix for auto-subscription
2. Update stores through exposed methods
3. Avoid direct store manipulation
4. Clean up subscriptions in `onDestroy`

### Type Safety

1. Define interfaces for all data structures
2. Use TypeScript strict mode
3. Avoid `any` types
4. Document complex types

### Testing

1. Unit test stores and utilities
2. Component testing with Svelte Testing Library
3. Integration tests for critical flows
4. E2E tests for user journeys
