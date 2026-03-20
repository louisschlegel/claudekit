# Go Microservice — Claude Code Instructions

## Stack
- Go 1.23+, standard library + minimal dependencies
- gRPC + protobuf for inter-service communication
- PostgreSQL (pgx driver), Redis
- Docker, Kubernetes, Helm charts

## Conventions
- Project layout: `cmd/`, `internal/`, `pkg/`, `api/`, `deploy/`
- Interfaces in consumer packages, not provider
- Error wrapping: `fmt.Errorf("operation: %w", err)`
- Context propagation: always pass `ctx context.Context` as first parameter
- No globals except logger and config (initialized in main)

## Database
- Migrations in `internal/db/migrations/` (golang-migrate format)
- Repository pattern: interfaces in `internal/domain/`, implementations in `internal/db/`
- Use `pgxpool` for connection pooling
- Always use prepared statements or `pgx.NamedArgs`

## Testing
- Table-driven tests with `t.Run()` subtests
- Mocks with `go.uber.org/mock` (mockgen)
- Integration tests with testcontainers-go
- `go test ./... -race -cover` in CI

## gRPC
- Proto files in `api/proto/`
- Generate with `buf generate`
- Interceptors for auth, logging, metrics
- Health check service on every service
