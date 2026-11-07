# Local competition data (gitignored)

Downloaded from [gemma-4-developer-agent](https://www.kaggle.com/competitions/gemma-4-developer-agent/data) after accepting that competition’s rules.

| Path | Contents |
|------|----------|
| `tasks.jsonl` | 129 public development tasks |
| `graphs/` | AST multigraph JSON (commit-named + task hardlinks as shipped) |
| `embeddings/` | 256-d node vectors in `.npz` archives |
| `docker/`, `sandbox/` | Sandbox build shims / setup |
| `HARNESS_README.md` | Official harness documentation |

**Not downloaded here:** `snapshots/` (~20 GB repo archives) and `wheels/`. Add those when you need full offline apply/`pytest` loops.

Do not commit or redistribute these files; use the Kaggle Data tab.
