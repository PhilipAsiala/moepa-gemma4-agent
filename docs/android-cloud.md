# Controlling this agent from Android

Cursor Remote Control is **iOS-only**. On Android, use a **cloud agent** in Chrome.

## Open the agent

1. On your Android phone, open Chrome and go to **https://cursor.com/agents**.
2. Sign in with the same Cursor account that owns this repo.
3. Pick the cloud agent for **moepa-gemma4-agent** (this Paper Track companion).
4. Send follow-ups in the chat thread — commits, docs, word-count trims, notebook polish, PR edits.

Direct pattern (once you have a run id from the agents list or a share link):

```text
https://cursor.com/agents/<bcId>
```

Example for the current Paper Track cloud run:

```text
https://cursor.com/agents/bc-1adb5c70-1760-4dd1-bf83-50996e5c3e9b
```

Bookmark that URL so you can resume the same thread without hunting through the list.

## What cloud can and cannot do

| On the cloud agent (this path) | On the workstation agent only |
| --- | --- |
| Edit `paper/`, `docs/`, `notebooks/`, `src/` | Arc Pro B70 / local GPU |
| Run `scripts/wordcount.py`, lint, small CI-friendly probes | Ollama (`gemma4:12b` / `26b`) |
| Commit + push small PR branches | Full `data/graphs`, `embeddings`, `snapshots` (~20 GB) |
| Scaffold / refine the public notebook Markdown | Local microbench / snapshot / pytest resolve with real assets |

Local GPU experiments, Ollama Praxeology loops, and measured numbers that need the competition archives stay on the **workstation agent**. Ask this cloud agent to update prose, checkboxes, and notebook text from results you already measured locally — do not expect it to claim access to your B70 or `data/` tree.

## Small commits

Prefer short, pushable commits from phone follow-ups (docs, word budget, notebook cells). Leave heavy experimental runs for the workstation session.
