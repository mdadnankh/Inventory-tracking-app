## AI usage & guidance

This repository was created specifically for an assessment and does not include any proprietary code, data, or prompts.

### How AI was used
- Generate initial scaffolding for Docker Compose + Flask + React.
- Iterate on API shape, validation, and error contract.
- Add a small but meaningful test suite that proves key invariants.

### Guardrails followed
- Keep the system small: minimal endpoints and UI, strong correctness rules.
- Validate all external inputs (request JSON) before applying any business logic.
- Return consistent error shapes to make failures diagnosable.
- Prefer simple, explicit code over clever abstractions.
- Add tests for invariants so changes can be made safely.

### Human review / verification
- All generated code is reviewed and run locally via Docker.
- API behavior is verified with curl and with automated tests:
  - `docker compose run --rm backend pytest -q`

### Known risks / future hardening
- Concurrency: enforcing “no negative stock” purely via aggregate reads can race under high contention.
  - Production approach: maintain `current_stock` with transactional updates and row-level locking.

