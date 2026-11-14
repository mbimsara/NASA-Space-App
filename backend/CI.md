# Automated backend tests

[Backend tests](../.github/workflows/backend-tests.yml) runs on pushes to any
branch and pull requests that change `backend/`, `data/`, the shared validation
script, this workflow, `.env.example`, or root pytest configuration. It also
supports manual runs from GitHub Actions. Pull requests run when opened,
reopened, or updated with new commits.

The Ubuntu job uses Python 3.12, caches pip downloads, installs
`requirements-ci.txt` (which includes `requirements.txt`), validates shared data
with `python scripts/validate_data.py`, and runs every test in `backend/tests`.
Either command failing fails the job. New runs cancel older runs for the same
Git ref. The existing `data-checks.yml` workflow remains unchanged.

Tests use temporary SQLite databases. Pytest runs from a temporary directory so
the application's legacy relative startup database also stays outside the
checkout. `DATABASE_URL` points to runner temporary storage for versions of the
backend that support environment configuration. No `.env`, secrets, production
credentials, frontend, or external database service is needed.

`pytest-socket` blocks network sockets during tests; Unix sockets remain enabled
for FastAPI's in-process TestClient. Provider calls must be mocked. Dependency
installation and GitHub Actions themselves still need internet access. This is
a pytest guard, not an operating-system network sandbox for subprocesses.

The Actions log shows pytest results. A JUnit XML report is uploaded as
`backend-test-results` even when tests fail, if pytest produced it. No deployment
is performed. Branch protection must be configured separately if passing tests
should be required before merging; path-filtered checks should not be made
unconditionally required for unrelated frontend-only pull requests.

To reproduce on Linux/macOS with Python 3.12, start at the repository root:

```bash
python3.12 -m venv .venv-ci
source .venv-ci/bin/activate
python -m pip install -r backend/requirements-ci.txt
python scripts/validate_data.py
repo_root="$PWD"
test_dir="$(mktemp -d)"
(
  cd "$test_dir"
  PYTHONPATH="$repo_root/backend" DATABASE_URL="sqlite:///$test_dir/startup.db" \
    python -m pytest "$repo_root/backend/tests" -ra \
      --disable-socket --allow-unix-socket
)
test_status=$?
rm -rf "$test_dir"
exit "$test_status"
```
