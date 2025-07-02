# Generative Media Studio - Frontend

SvelteKit frontend application for the Generative Media Studio platform.

## Setup

```bash
# Install dependencies
npm install
```

## Development

```bash
# Run development server
npm run dev

# Or use npm from root directory
npm run dev:frontend
```

## Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with UI
npm run test:ui
```

## Project Structure

```
src/
├── routes/          # SvelteKit pages
├── lib/
│   ├── components/  # Reusable components
│   ├── stores/      # Svelte stores
│   └── utils/       # Utility functions
└── app.html         # App template
```