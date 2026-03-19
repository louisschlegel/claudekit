# Rust API — Claude Code Instructions

## Stack
- Rust 1.80+, Axum web framework
- SQLx (async PostgreSQL), Tower middleware
- tokio runtime, tracing for observability
- Docker multi-stage builds

## Conventions
- Modules: `src/routes/`, `src/models/`, `src/services/`, `src/middleware/`
- Use `thiserror` for custom error types, `anyhow` in application code
- Prefer `&str` over `String` in function parameters
- All public functions need doc comments (`///`)
- No `unwrap()` in production code — use `?` operator

## Database
- SQLx compile-time query checking with `sqlx::query!`
- Migrations in `migrations/` directory (sqlx-cli)
- Always use `sqlx::Pool<Postgres>` with connection pooling
- Transactions for multi-step operations: `pool.begin().await?`

## Testing
- Unit tests in same file: `#[cfg(test)] mod tests`
- Integration tests in `tests/` directory
- Use `sqlx::test` for database tests with automatic rollback
- Property-based testing with `proptest` for serialization

## Error Handling
- Custom `AppError` enum implementing `IntoResponse`
- Map all errors to appropriate HTTP status codes
- Never expose internal errors to clients
- Log full error chain with `tracing::error!`
