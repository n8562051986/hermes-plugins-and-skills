# Hermes Plugins & Skills

Custom plugins and skills for [Hermes Agent](https://hermes-agent.nousresearch.com), created by [@n8562051986](https://github.com/n8562051986).

## Contents

| Item | Type | Description |
|------|------|-------------|
| [`run-command`](./run-command/) | Plugin | `/run <command>` — execute shell commands directly, zero AI tokens |
| [`quran-progress`](./quran-progress/) | Standalone CLI | Quran reading progress tracker — add, list, report, history |

## Installing

### run-command plugin

```bash
# Copy to Hermes plugins directory
cp -r run-command ~/.hermes/plugins/

# Enable in Hermes config
hermes config set plugins.enabled '["run-command", ...]'
```

### quran-progress CLI

```bash
# Single script, zero dependencies
chmod +x quran-progress/quran-progress
cp quran-progress/quran-progress ~/.local/bin/
echo "🌼D : H204 J27" | quran-progress add
quran-progress report
```
