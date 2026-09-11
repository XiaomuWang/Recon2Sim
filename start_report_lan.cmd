@echo off
cd /d "%~dp0"
echo Local: http://127.0.0.1:8765/
echo LAN:   http://10.192.41.46:8765/ (use your current LAN IP if changed)
echo Keep this window open while sharing. Press Ctrl+C to stop.
python -m a2s.report_server --port 8765 --bind 0.0.0.0
if errorlevel 1 pause
