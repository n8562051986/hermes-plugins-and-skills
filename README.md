# Hermes Plugins & Skills

Custom plugins, tools, and patches for [Hermes Agent](https://hermes-agent.nousresearch.com), created by [@n8562051986](https://github.com/n8562051986).

## Contents

### Slash command plugins

| Plugin | Command | Description | Backend |
|--------|---------|-------------|---------|
| [`cc-chat`](./cc-chat/) | `/cc <question>` | AI chat via Command Code CLI (`cmd -p`) | Langsung `cmd -p` |
| [`cai-chat`](./cai-chat/) | `/cai <question>` | AI chat via Command Code Web UI (HTTP wrapper) | HTTP ke `:5000` |
| [`g4f-chat`](./g4f-chat/) | `/g4f <question>` | AI chat via g4f (PollinationsAI), gratis no login | `ai` CLI |
| [`run-command`](./run-command/) | `/run <command>` | Execute shell commands, zero AI tokens | Langsung shell |

### Standalone tools

| Tool | Description |
|------|-------------|
| [`commandcode-webui`](./commandcode-webui/) | Flask web UI wrapper untuk `cmd -p` — chat via browser di `http://127.0.0.1:5000` |
| [`quran-progress`](./quran-progress/) | Quran reading progress tracker — add, list, report, history |
| [`wsl-ssh-forward`](./wsl-ssh-forward/) | Auto-detect WSL IP, forward SSH port via Windows |

### Patches

| Patch | Description |
|-------|-------------|
| [`patches/cpr-bare-form-fix.patch`](./patches/cpr-bare-form-fix.patch) | Strip bare `[[row;colR` CPR leak from WSL ConPTY (di-revert, archived) |

## Installing

### Slash command plugins

```bash
# Copy to Hermes plugins directory
cp -r cc-chat ~/.hermes/plugins/
cp -r cai-chat ~/.hermes/plugins/
cp -r g4f-chat ~/.hermes/plugins/
cp -r run-command ~/.hermes/plugins/

# Enable via Hermes CLI
hermes plugins enable cc-chat
hermes plugins enable cai-chat
hermes plugins enable g4f-chat
hermes plugins enable run-command

# Restart Hermes session
```

### Prerequisites

- **`/cc`** — `npm i -g command-code@latest` then `cmd login`
- **`/cai`** — Sama kayak `/cc` plus web UI jalan: `python ~/clawd/commandcode-webui/app.py`
- **`/g4f`** — `pip install g4f` and the `ai` CLI script

### commandcode-webui (Flask web UI)

```bash
cd commandcode-webui
pip install flask
python app.py
# → http://127.0.0.1:5000
```

### quran-progress CLI

```bash
chmod +x quran-progress/quran-progress
cp quran-progress/quran-progress ~/.local/bin/
echo "🌼D : H204 J27" | quran-progress add
quran-progress report
```

## GitHub Workflow

Setelah commit, update README ini biar dokumentasi selalu sinkron dengan isi repo.
