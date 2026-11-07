# Local competition data (gitignored)

Downloaded from [gemma-4-developer-agent](https://www.kaggle.com/competitions/gemma-4-developer-agent/data) after accepting that competition’s rules.

| Path | Contents |
|------|----------|
| `tasks.jsonl` | 129 public development tasks |
| `graphs/` | AST multigraph JSON |
| `embeddings/` | 256-d node vectors in `.npz` archives |
| `snapshots/` | Per-task `.tgz` git trees at `base_commit` (~20 GB) |
| `docker/`, `sandbox/`, `HARNESS_README.md` | Harness extras |

**Optional:** `wheels/` for offline dependency installs inside the official sandbox image. Gold-patch apply / syntax / Axiology probes use `scripts/snapshot_probe.py` and do not require wheels.

Do not commit or redistribute these files; use the Kaggle Data tab.
