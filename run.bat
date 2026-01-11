@echo off
chcp 65001 > nul
echo Starting Z-Image-Turbo Generator...
call venv\Scripts\activate.bat
python app.py
pause
