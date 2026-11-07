# Paper micro-benchmark

Measured from `scripts/paper_microbench.py` on the public development set.
Fail-to-pass pytest resolve rate is not reported here (needs competition wheels/sandbox).
Snapshot gold-apply / syntax / Axiology numbers live in `outputs/snapshot_probe.json`
(from `scripts/snapshot_probe.py`).

## Embeddings

Snapshots: 127. Random-pair cosine mean 0.829 (p10 0.532, p90 0.989). Same-parent mean 0.885. Cross-parent mean 0.829.

## Ontology localization

Tasks: 129. Gold files: 278.
Lexical seed + 1-hop file recall: 53/278 (19.1%).
Size-matched random neighborhood file recall: 0.126.
Task-level lexical coverage (at least one gold file): 47/129 (36.4%).
Random task-level coverage, mean over trials: 0.164.
Hunk-symbol recall: 70/364 (19.2%) versus random 0.032.
Neighborhood size: median 9995 chars, p90 409956. Tasks over the 5000-char prompt cap: 74.

## Gates

Axiology approved 129/129 gold solution diffs.
Rejected test-file tamper 129/129, protected shim 129/129, empty diff 129/129.
Metrology on a repeated diagnostic: stagnating=[False, True, True, True], hop radius=[1, 1, 2, 3, 3], budget exhausted=True. Varied diagnostics did not stagnate ([False, False, False]) and left hop radius at 1.

## Gemma 4 12B file localization

Model `gemma4:12b` on `127.0.0.1:11434`, think disabled, context 4096, 30 public tasks.
Issue text only: file hit 10/30 (33.3%), abstain 1, parse failures 0, mean 11.0s.
Issue plus capped neighborhood: file hit 14/30 (46.7%), abstain 0, parse failures 0, mean 10.7s.

| Task | Repo | Gold file | Issue only | With neighborhood |
|---|---|---|---|---|
| `httpx_3672` | httpx | `src/ahttpx/_parsers.py, src/ahttpx/_pool.py, src/ahttpx/_server.py, src/httpx/_network.py, src/httpx/_parsers.py, src/httpx/_pool.py, src/httpx/_server.py` | http/parser.py, server.py | httpx/_parsers.py |
| `requests_6589` | requests | `src/requests/utils.py` | requests/utils.py | requests/utils.py |
| `requests_6592` | requests | `src/requests/status_codes.py` | src/models/status_codes.py | src/models/status_codes.py |
| `requests_6629` | requests | `src/requests/exceptions.py` | requests/exceptions.py | requests/exceptions.py |
| `requests_6644` | requests | `src/requests/adapters.py` | urllib3/connection_pool.py | requests/api.py |
| `requests_7205` | requests | `src/requests/utils.py` | requests/auth.py | requests/sessions.py |
| `requests_7309` | requests | `src/requests/utils.py` | utils.py | requests/utils.py |
| `rich_2725` | rich | `rich/table.py` | table.py | rich/table.py |
| `rich_2943` | rich | `rich/style.py` | meta/cache.py | rich/style.py |
| `rich_3006` | rich | `rich/repr.py` | sqlalchemy/models.py | rich/scope.py |
| `rich_3043` | rich | `rich/_export_format.py` | textual/app/export.py, .pre-commit-config.yaml | rich/console.py |
| `rich_3052` | rich | `rich/prompt.py` | rich/prompt.py | rich/prompt.py |
| `rich_3061` | rich | `rich/text.py` | rich/text.py | rich/text.py |
| `rich_3063` | rich | `rich/markup.py` | rich/console.py | rich/console.py |
| `rich_3064` | rich | `rich/markdown.py` | rich/markdown.py | rich/markdown.py |
| `rich_3067` | rich | `rich/highlighter.py` | fastapi/routing.py | rich/text.py |
| `rich_3105` | rich | `rich/_export_format.py` | . | rich/syntax.py |
| `fastapi_11194` | fastapi | `fastapi/dependencies/utils.py` | fastapi/dependencies.py, fastapi/params.py | fastapi/params.py |
| `fastapi_11355` | fastapi | `fastapi/dependencies/utils.py` | typer/utils/types.py | typer/utils/types.py |
| `fastapi_12942` | fastapi | `fastapi/_compat.py` | fastapi/dependencies.py | fastapi/params.py |
| `fastapi_13207` | fastapi | `fastapi/_compat/v2.py` | fastapi/openapi.py | fastapi.openapi.utils.generate_schema |
| `fastapi_13537` | fastapi | `fastapi/dependencies/utils.py` | fastapi/params.py | fastapi/dependencies/utils.py |
| `fastapi_13920` | fastapi | `fastapi/dependencies/utils.py` | src/pydantic/_internal/typing_utils.py | src/pydantic/_internal/typing_utils.py |
| `fastapi_14246` | fastapi | `fastapi/_compat/v2.py` | fastapi/models.py, fastapi/openapi.py | fastapi/models.py |
| `fastapi_14258` | fastapi | `fastapi/routing.py` | fastapi/routing.py | fastapi/routing.py |
| `fastapi_14266` | fastapi | `fastapi/dependencies/utils.py` | fastapi/openapi.py | fastapi/openapi/utils.py |
| `fastapi_14297` | fastapi | `fastapi/_compat/v2.py` | fastapi/_compat/v2.py | fastapi/_compat/v2.py |
| `fastapi_14301` | fastapi | `fastapi/dependencies/utils.py` | fastapi/dependencies.py | fastapi/dependencies/utils.py |
| `fastapi_14303` | fastapi | `fastapi/dependencies/utils.py` | fastapi/dependencies/utils.py | fastapi/dependencies/utils.py |
| `fastapi_14349` | fastapi | `fastapi/_compat/v2.py` | fastapi/schema.py | fastapi/openapi/models.py |
