@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" "analyze_songs.py"
if errorlevel 1 (echo Analysis failed. Please read the error above.) else (echo Finished. Plots are in the outputs folder.)
pause

