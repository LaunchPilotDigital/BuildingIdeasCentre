@echo off
echo Building Ideas Centre preview: http://localhost:8000
echo Close this window to stop it.
start "" http://localhost:8000
python -m http.server 8000 --directory "%~dp0site"
