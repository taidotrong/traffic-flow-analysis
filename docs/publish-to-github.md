# Repository validation and publishing

The project repository is [taidotrong/traffic-flow-analysis](https://github.com/taidotrong/traffic-flow-analysis). The latest source import and validation details are recorded in [validation.md](validation.md).

From a clean clone:

```bash
git clone https://github.com/taidotrong/traffic-flow-analysis.git
cd traffic-flow-analysis
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/validate_notebooks.py
node --check dashboard/static/js/app.js
docker compose -f dashboard/docker-compose.yml config --quiet
git diff --check
```

For real-model validation, obtain the weights and short video from the links in [dashboard/README.md](../dashboard/README.md), then run `scripts/smoke_dashboard.py` with those paths. Notebook validation does not execute training.

Review and stage intended source changes, then commit and push to the existing remote using your configured GitHub identity. Do not force-push or replace the baseline history. The GitHub Actions workflow repeats the regression, notebook, syntax and Compose checks.

Generated databases, cookies, videos, datasets, checkpoint binaries and validation outputs are ignored. The small original sample database is intentionally tracked as a migration fixture. Keep model download locations and hashes in [models/README.md](../models/README.md); do not force-add ignored binary artifacts.
