# Paper micro-benchmark

Measured from `scripts/paper_microbench.py` on the public development set.
Repository snapshots were not checked out, so this file does not report a pytest resolve rate.

## Embeddings

Snapshots: 127. Random-pair cosine mean 0.829 (p10 0.532, p90 0.989). Same-parent mean 0.885. Cross-parent mean 0.829.

## Ontology localization

Tasks: 129. Gold files: 278.
Lexical seed + 1-hop file recall: 53/278 (19.1%).
Size-matched random neighborhood file recall: 0.126.
Task-level lexical coverage (at least one gold file): 47/129 (36.4%).
Random task-level coverage, mean over trials: 0.164.
Hunk-symbol recall: 70/364 (19.2%) versus random 0.032.
Tasks with no lexical seed, and therefore an empty neighborhood: 32/129.
Neighborhood size: median 9995 chars, p90 409956. Tasks over the 5000-char prompt cap: 74.

## Gates

Axiology approved 129/129 gold solution diffs.
Rejected test-file tamper 129/129, protected shim 129/129, empty diff 129/129.
Metrology on a repeated diagnostic: stagnating=[False, True, True, True], hop radius=[1, 1, 2, 3, 3], budget exhausted=True. Varied diagnostics did not stagnate ([False, False, False]) and left hop radius at 1.

## Gemma 4 12B file localization

Model `gemma4:12b` on `127.0.0.1:11434`, think disabled, context 4096, 12 public tasks.
A prediction hits when it names the same file as the gold diff, ignoring a leading `src/` or `./`. A parent directory does not count.
Issue text only: file hit 3/12 (25.0%), abstain 0, parse failures 0, mean 1.7s.
Issue plus capped neighborhood: file hit 4/12 (33.3%), abstain 0, parse failures 0, mean 3.3s.

| Task | Repo | Gold file | Issue only | With neighborhood |
|---|---|---|---|---|
| `httpx_3672` | httpx | `src/ahttpx/_parsers.py, src/ahttpx/_pool.py, src/ahttpx/_server.py, src/httpx/_network.py, src/httpx/_parsers.py, src/httpx/_pool.py, src/httpx/_server.py` | http/parser.py, server.py | httpx/_parsers.py |
| `requests_6589` | requests | `src/requests/utils.py` | requests/utils.py | requests/utils.py |
| `requests_6592` | requests | `src/requests/status_codes.py` | src/models/status_codes.py | src/models/status_codes.py |
| `requests_6629` | requests | `src/requests/exceptions.py` | requests/exceptions.py | requests/exceptions.py |
| `rich_2725` | rich | `rich/table.py` | table.py | rich/box.py |
| `rich_2943` | rich | `rich/style.py` | src/meta/cache.py | rich/style.py |
| `rich_3006` | rich | `rich/repr.py` | src/pytorch/utils._serialization.py | rich/progress.py |
| `rich_3043` | rich | `rich/_export_format.py` | textual/app/export.py, .pre-commit-config.yaml | rich/console.py |
| `fastapi_11194` | fastapi | `fastapi/dependencies/utils.py` | fastapi/dependencies.py, fastapi/params.py | fastapi/params.py |
| `fastapi_11355` | fastapi | `fastapi/dependencies/utils.py` | typer/utils/types.py | typer/utils/types.py |
| `fastapi_12942` | fastapi | `fastapi/_compat.py` | fastapi/dependencies.py | fastapi/dependencies.py |
| `fastapi_13207` | fastapi | `fastapi/_compat/v2.py` | fastapi/openapi.py | fastapi/openapi.py |
