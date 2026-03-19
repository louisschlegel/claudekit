# Next.js SaaS — Claude Code Instructions

## Stack
- Next.js 15 (App Router), TypeScript, Tailwind CSS
- Supabase (PostgreSQL + Auth + Storage)
- Stripe (Payments), Resend (Email)
- Vercel (Deploy), GitHub Actions (CI)

## Conventions
- Use server components by default, `"use client"` only when needed (interactivity, hooks)
- API routes in `app/api/` with route handlers, not pages
- Database queries via Supabase client, never raw SQL in components
- All prices in cents (integer), display with `formatCurrency()`
- Environment: `.env.local` (never commit), `.env.example` for documentation

## Testing
- Vitest for unit tests, Playwright for E2E
- Test files: `*.test.ts` next to source files
- E2E tests in `e2e/` directory
- Mock Supabase client in unit tests, use test DB in E2E

## Git
- Feature branches from `main`, squash merge
- Commit format: `type(scope): message` (feat, fix, docs, refactor, test)
- PR required for main, 1 review minimum

## Security
- Never expose `SUPABASE_SERVICE_ROLE_KEY` to client
- Always use Row Level Security (RLS) on Supabase tables
- Validate all user input with Zod schemas
- Stripe webhooks: always verify signature
