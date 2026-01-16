@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

echo DEBUG: Script start

echo [Z-Image-Turbo] Python Virtual Environment Setup Script.
echo.

REM Check for Python
echo DEBUG: Checking Python version
python --version
echo DEBUG: Python version check done. errorlevel is %errorlevel%
if %errorlevel% neq 0 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)
echo DEBUG: Python check passed.

REM Create venv if not exists
echo DEBUG: Checking for venv directory
if not exist "venv" goto CREATE_VENV
goto VENV_EXISTS

:CREATE_VENV
echo [INFO] Creating virtual environment (venv)...
python -m venv venv
:VENV_EXISTS
echo DEBUG: venv check passed.

REM Activate venv
call venv\Scripts\activate.bat

REM Check if torch is already installed
echo DEBUG: Checking for torch
pip show torch >nul 2>&1
echo DEBUG: torch check done. errorlevel is %errorlevel%
if %errorlevel% equ 0 goto :TORCH_INSTALLED
echo DEBUG: torch not found.

REM Torch NOT installed, try installing
echo [INFO] PyTorch not detected. Installing default CUDA version (12.8)...
echo [WARNING] RTX 5090 users, if installation fails, please refer to the Readme and install the Nightly version manually.

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
if %errorlevel% neq 0 goto :TORCH_INSTALL_FAILED

pip install accelerate
goto :INSTALL_DEPS

:TORCH_INSTALL_FAILED
echo [ERROR] PyTorch (Stable/cu128) installation failed.
echo [INFO] For RTX 50 series, please copy and paste the command below to install manually:
echo venv\Scripts\pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
echo.
echo Don't worry, we will continue installing the rest of the packages...
goto :INSTALL_DEPS

:TORCH_INSTALLED
echo [INFO] PyTorch is already installed. (Skipping)

:INSTALL_DEPS
REM Install dependencies
echo [INFO] Starting installation of remaining packages...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [SUCCESS] Environment setup is complete!
echo [INFO] You can start the program by running 'run.bat'.
echo.
pause
