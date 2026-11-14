# Backend — Dulanjaya

Planned FastAPI service; no application or database has been scaffolded yet.

First delivery: typed contracts, farm create/read/update persistence, validation and error format, then adapters for observations, rotations, scenarios, assistant, and saved plans. See [API contracts](../docs/API_CONTRACTS.md).

Suggested separation: API routes, persistence, and domain services for observations, rotation, scenarios, finance, and assistant. Domain functions should accept explicit inputs and return structured results so they can be verified independently of HTTP.

When initializing, document Python version, dependency installation, migrations, environment loading, startup, and check commands here. The root `.env.example` is a proposed configuration contract and is not loaded by any existing application.
