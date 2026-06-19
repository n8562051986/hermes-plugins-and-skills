# Command Code Web UI

Web interface untuk `cmd -p` — chat dengan AI lewat browser.

## Cara Pakai

```bash
# 1. Masuk folder & setup virtual env (sekali aja)
cd ~/clawd/commandcode-webui
python3 -m venv venv
source venv/bin/activate
pip install flask

# 2. Jalankan (pakai source venv dulu tiap kali)
source venv/bin/activate
python app.py

# 3. Buka http://127.0.0.1:5000
```

## Fitur

- Streaming response real-time (SSE) — output muncul token by token
- Pilih model dari dropdown / ketik manual
- Markdown rendering
- Dark theme
- Shortcut: `Ctrl+L` clear chat, `Enter` send, `Shift+Enter` newline

## Catatan

- Hanya bind ke `127.0.0.1` — aman dari akses luar
- Butuh `cmd` CLI yang sudah login (`cmd login`)
