# Expense Policy Agent - React Frontend

React + TypeScript + Vite frontend for the Expense Policy Agent web application.

**Phase 1 Status**: Foundation and routing setup complete. Placeholder pages only.

## Development

### Prerequisites

- Node.js 16+ with npm or yarn
- Django backend running on `http://localhost:8000`

### Setup

```bash
npm install
```

### Start Development Server

```bash
npm run dev
```

The React app will be available at `http://localhost:5173`

Routes:
- `/upload` - Receipt upload page
- `/finance` - Finance dashboard

### Build for Production

```bash
npm run build
```

Output: `dist/`

### Type Check

```bash
npm run type-check
```

## Architecture

- **pages/**: Top-level route components
- **components/**: Reusable UI components
- **api/**: HTTP client and API wrappers
- **hooks/**: Custom React hooks
- **types/**: TypeScript interfaces
- **utils/**: Utility functions
- **styles/**: Global and component styles

## API Communication

During development, Vite proxies API requests to Django:
- `/api/*` → `http://localhost:8000/api/*`
- `/finance/*` → `http://localhost:8000/finance/*`

See `vite.config.ts` for proxy configuration.

## Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Variables:
- `VITE_API_BASE_URL`: Django backend URL (default: `http://localhost:8000`)
- `VITE_DEBUG`: Enable debug logging (default: `false`)

## Next Steps (Phase 2+)

- Phase 2: Implement receipt upload page with file validation
- Phase 3: Implement finance dashboard with filters and approval workflow
- Phase 4: Migrate Teams workflow to React (if applicable)

## Testing

Frontend tests will be added in Phase 2:
- Component unit tests (Vitest + React Testing Library)
- Integration tests (API calls)
- E2E tests (Playwright)

## Troubleshooting

### CORS Issues During Development

If you see CORS errors in the browser console when calling Django APIs:
1. Ensure Django is running on `http://localhost:8000`
2. Check that Vite proxy is configured correctly in `vite.config.ts`
3. The proxy should forward requests without requiring CORS headers

### Build Errors

```bash
npm run type-check
```

Check for TypeScript compilation errors before building.

### Dependencies

Minimal dependencies in Phase 1:
- `react` + `react-dom`: UI framework
- `react-router-dom`: Client-side routing
- Vite: Build tool

Additional packages will be added in Phase 2+ (e.g., HTTP client, state management).
