# Hermes Plugins & Skills

Custom plugins and skills for [Hermes Agent](https://hermes-agent.nousresearch.com), created by [@n8562051986](https://github.com/n8562051986).

## Contents

| Item | Type | Description |
|------|------|-------------|
| [`run-command`](./run-command/) | Plugin | `/run <command>` — execute shell commands directly, zero AI tokens |
| [`g4f-chat`](./g4f-chat/) | Plugin | `/g4f <question>` — AI chat via g4f (PollinationsAI), gratis no login |
| [`cc-chat`](./cc-chat/) | Plugin | `/cc <question>` — AI chat via Command Code CLI (`cmd -p`), pakai subscription |
| [`quran-progress`](./quran-progress/) | Standalone CLI | Quran reading progress tracker — add, list, report, history |

## Installing

### Slash command plugins

```bash
# Copy to Hermes plugins directory
cp -r run-command ~/.hermes/plugins/
cp -r g4f-chat ~/.hermes/plugins/
cp -r cc-chat ~/.hermes/plugins/

# Enable in Hermes config
hermes config set plugins.enabled '["run-command", "g4f-chat", "cc-chat", ...]'

# Restart Hermes session (/reset or restart TUI)
```

### Prerequisites

- **`/g4f`** — needs `pip install g4f` and the `ai` CLI script
- **`/cc`** — needs `npm i -g command-code@latest` and `cmd login`

### quran-progress CLI

```bash
# Single script, zero dependencies
chmod +x quran-progress/quran-progress
cp quran-progress/quran-progress ~/.local/bin/
echo "🌼D : H204 J27" | quran-progress add
quran-progress report
```
