# Workflow: Review and Optimize React Frontend Components

Use this workflow to review, polish, and optimize frontend components and pages.

## Step 1: Type Safety & Schema Parity
1. Inspect component props and state types in `frontend/src/`.
2. Confirm interfaces in `frontend/src/types/` match backend Pydantic schemas.
3. Ensure zero `any` types and strict null-safety checks (`product?.variants?.length`).

## Step 2: User Experience & State Handling
1. **Loading State:** Skeleton loaders or subtle spinners during async data fetching.
2. **Empty State:** Helpful empty state screens with direct call-to-action buttons (e.g. "Add your first product").
3. **Error State:** Human-readable error alerts with retry triggers; no raw JSON crashes.
4. **Demo Data Indication:** Visual badge `[Preview Mode]` or banner whenever demo data is active.

## Step 3: Accessibility & Design Standards
1. Semantic HTML (`<main>`, `<nav>`, `<header>`, `<button>`, `<section>`).
2. Keyboard navigation (`Tab`, `Enter`, `Escape` for modals and dropdowns).
3. High contrast text colors adhering to WCAG 2.1 AA standards.
4. Fluid responsive design using Tailwind CSS across mobile (`<640px`), tablet (`768px`), and desktop (`1024px+`).

## Step 4: Build & Bundle Verification
1. Run TypeScript check and production bundle compilation:
   ```bash
   npm --prefix frontend run build
   ```
2. Confirm 0 type errors and inspect chunk sizes.

