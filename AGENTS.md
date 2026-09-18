# Development workflow

- `main` is the stable/release branch.
- `dev` is the integration branch for ongoing development.
- Create feature/fix branches from `dev` and merge them back into `dev`.
- Promote tested release candidates from `dev` to `main`.
- Update `CHANGELOG.md` for every user-visible or architecturally relevant change.
- Keep `VERSION`, `pyproject.toml`, release tags, and changelog releases synchronized.
- Run the version check and unit tests before pushing release-related changes.
- Never commit proprietary VRC, Telemetrick, CSP, or Assetto Corsa code/assets/data.
- Keep setup and telemetry processing local and read-only unless the user explicitly
  approves a generated copy or another write operation.
