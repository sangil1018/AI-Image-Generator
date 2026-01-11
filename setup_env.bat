@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

echo [Z-Image-Turbo] Python 가상 환경 설정 스크립트입니다.
echo.

REM Check for Python
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python을 찾을 수 없습니다.
    pause
    exit /b 1
)

REM Create venv if not exists
if not exist "venv" (
    echo [INFO] 가상 환경(venv)을 생성합니다...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if torch is already installed
pip show torch >nul 2>&1
if %errorlevel% equ 0 goto :TORCH_INSTALLED

REM Torch NOT installed, try installing
echo [INFO] PyTorch가 감지되지 않았습니다. 기본 CUDA 버전(12.8)을 설치합니다...
echo [WARNING] RTX 5090 사용자는 설치 실패 시 Readme를 참조하여 Nightly 버전을 수동 설치하세요.

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
if %errorlevel% neq 0 goto :TORCH_INSTALL_FAILED

pip install accelerate
goto :INSTALL_DEPS

:TORCH_INSTALL_FAILED
echo [ERROR] PyTorch (Stable/cu128) 설치 실패.
echo [INFO] RTX 50 시리즈라면 아래 명령어를 복사해 수동으로 설치하세요:
echo venv\Scripts\pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
echo.
echo 당황하지 마시고, 일단 나머지 패키지 설치를 계속 진행합니다...
goto :INSTALL_DEPS

:TORCH_INSTALLED
echo [INFO] PyTorch가 이미 설치되어 있습니다. (건너뜀)

:INSTALL_DEPS
REM Install dependencies
echo [INFO] 나머지 패키지 설치 시작...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [SUCCESS] 환경 설정이 완료되었습니다!
echo [INFO] 'run.bat'을 실행하여 프로그램을 시작할 수 있습니다.
echo.
pause
