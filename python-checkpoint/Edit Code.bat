@echo off
cd /d "%~dp0"
".venv\Scripts\pythonw.exe" -m idlelib "analyze_songs.py"

