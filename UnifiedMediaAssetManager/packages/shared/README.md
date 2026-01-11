# @unified/shared

Shared types and utilities for the Unified Media Ecosystem monorepo.

## Purpose

This package provides common TypeScript interfaces, types, and constants used across both Media Manager and StoryForge applications. By centralizing shared types, we ensure consistency and reduce duplication.

## Installation

This package is part of the monorepo and automatically available to other workspaces.

```bash
# Install dependencies
npm install --workspace=packages/shared

# Build the package
npm run build --workspace=packages/shared
```

## Usage

### In Media Manager (Next.js Frontend)

```typescript
import { Universe, Element, MediaAsset, ElementType } from '@unified/shared';

interface Props {
  universe: Universe;
  elements: Element[];
}

function UniverseView({ universe, elements }: Props) {
  // Type-safe usage of shared interfaces
  return (
    <div>
      <h1>{universe.name}</h1>
      {elements.map(el => (
        <div key={el.id}>{el.name} - {el.type}</div>
      ))}
    </div>
  );
}
```

### In Media Manager (FastAPI Backend)

```python
# Python equivalent types are defined in backend/app/models/
# This package is for TypeScript/JavaScript only
```

### In StoryForge

```typescript
import { 
  Universe, 
  TimelineEvent, 
  Element,
  ELEMENT_TYPES 
} from '@unified/shared';

const event: TimelineEvent = {
  id: '1',
  universeId: 'universe-1',
  title: 'Battle of Winterfell',
  linkedElements: ['character-1', 'location-1']
};
```

## Available Types

### Core Entities
- `User` - User account information
- `Universe` - Story universe/project
- `Element` - Characters, locations, props, etc.
- `MediaAsset` - Images, videos, audio, 3D models
- `TimelineEvent` - Story timeline events

### API Types
- `APIResponse<T>` - Standard API response wrapper
- `PaginatedResponse<T>` - Paginated data response
- `MediaGenerationRequest` - AI generation request

### HITL Types
- `HITLRequest` - Human-in-the-loop review requests

### Utility Types
- `Nullable<T>` - T or null
- `Optional<T>` - T or undefined
- `ID` - string or number

### Enums/Constants
- `MEDIA_TYPES` - All supported media types
- `ELEMENT_TYPES` - All supported element types

## Development

```bash
# Watch mode for development
npm run dev --workspace=packages/shared

# Build
npm run build --workspace=packages/shared

# Clean dist folder
npm run clean --workspace=packages/shared
```

## TypeScript Configuration

This package is configured with strict TypeScript settings:
- Strict type checking enabled
- ES2020 target
- CommonJS modules for maximum compatibility
- Declaration files generated for IntelliSense

## Adding New Types

1. Edit `src/index.ts`
2. Add your interface/type with JSDoc comments
3. Group related types under section comments
4. Export from the main file
5. Rebuild the package: `npm run build --workspace=packages/shared`

## Version History

- **1.0.0** - Initial shared types package
  - User, Universe, Element, MediaAsset
  - Timeline, HITL types
  - API response wrappers
