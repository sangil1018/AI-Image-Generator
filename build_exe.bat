@echo off
chcp 65001 > nul
echo [INFO] PyInstaller 설치 확인 중...
call venv\Scripts\activate.bat
pip install pyinstaller

echo [INFO] 빌드 시작... (시간이 오래 걸릴 수 있습니다)
pyinstaller build.spec --clean --noconfirm

echo [SUCCESS] 빌드 완료! dist\Z-Image-Turbo\Z-Image-Turbo.exe 를 실행하세요.
echo.
pause
