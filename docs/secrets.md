# Secrets management

This project supports multiple secret resolution methods for runtime and tests:

1. Environment variables (`NEO4J_PASSWORD`, etc.).
2. File-based secrets mounted by Kubernetes at `/var/run/secrets/<KEY>` or via `<KEY>_FILE` env var.
3. Optional HashiCorp Vault integration when `VAULT_ADDR`, `VAULT_TOKEN`, and `VAULT_SECRET_PATH` are set.

Usage:

- Local (env):

```bash
export NEO4J_PASSWORD=supersecret
PYTHONPATH=.. python -m pytest tests/test_secrets.py
```

- Local (file):

```bash
echo "fileval" > /tmp/neo4j_password
export NEO4J_PASSWORD_FILE=/tmp/neo4j_password
PYTHONPATH=.. python -m pytest tests/test_secrets.py
```

- Vault (example variables):

```bash
export VAULT_ADDR=https://vault.example.local
export VAULT_TOKEN=sometoken
export VAULT_SECRET_PATH=secret/data/graph
# The secrets module will attempt to read key names from the secret's data
PYTHONPATH=.. python -m pytest tests/test_secrets.py
```

CI notes:

- The GitHub Actions workflow `.github/workflows/ci.yml` runs tests with `ENABLE_OTEL=false` and `RUN_STRESS=0` to avoid external dependencies and background tracing threads.
- The `tests/test_secrets.py` uses a fake `hvac` module in tests so CI does not require a real Vault.

GitHub Actions example (inject repo secrets into the job):

```yaml
jobs:
	secrets-tests:
		runs-on: ubuntu-latest
		steps:
			- uses: actions/checkout@v4
			- name: Run secrets unit tests
				env:
					NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
					VAULT_ADDR: ${{ secrets.VAULT_ADDR }}
					VAULT_TOKEN: ${{ secrets.VAULT_TOKEN }}
					VAULT_SECRET_PATH: ${{ secrets.VAULT_SECRET_PATH }}
				run: |
					PYTHONPATH=.. RUN_STRESS=0 ENABLE_OTEL=false python -m pytest tests/test_secrets_vault.py -q
```

This workflow demonstrates safely injecting repository secrets into a CI job without committing credentials to the repo. Tests should avoid depending on real external services; use mocks or the provided fake `hvac` test helper.
