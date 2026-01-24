#!/bin/bash
# 이 스크립트는 WSL2 또는 Linux 환경에서 프로젝트의 Python 환경 설정을 자동화합니다.
# 사용법: ./setup.sh

# 에러 발생 시 즉시 스크립트를 중지합니다.
set -e

# --- 출력 색상 정의 ---
C_GREEN='\033[0;32m'
C_YELLOW='\033[1;33m'
C_NC='\033[0m' # 색상 없음

echo -e "${C_YELLOW}프로젝트 환경 설정을 시작합니다...${C_NC}"

# --- 1. Python 가상 환경 생성 ---
if [ ! -d "venv" ]; then
    echo "Python 가상 환경을 './venv'에 생성합니다..."
    python3 -m venv venv
else
    echo "가상 환경 './venv'가 이미 존재합니다."
fi

# 가상 환경의 Python 실행 파일 경로 정의
VENV_PYTHON="venv/bin/python"

# --- 2. 필수 라이브러리 설치 ---
echo "pip를 업그레이드하고 requirements.txt의 라이브러리를 설치합니다..."
$VENV_PYTHON -m pip install --upgrade pip wheel
$VENV_PYTHON -m pip install -r requirements.txt

# --- 3. GPU 확인 및 CUDA 지원 PyTorch 설치 ---
# 'nvidia-smi' 명령어가 사용 가능한지 확인하여 GPU 존재 여부를 판단합니다.
if command -v nvidia-smi &> /dev/null; then
    echo -e "${C_GREEN}NVIDIA GPU가 감지되었습니다. CUDA를 지원하는 PyTorch를 설치합니다...${C_NC}"
    # CUDA 12.4와 호환되는 PyTorch를 명시적으로 설치합니다.
    # 이 버전은 CUDA 12.6 환경과 호환됩니다.
    $VENV_PYTHON -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
else
    echo -e "${C_YELLOW}NVIDIA GPU가 감지되지 않았습니다. CUDA 지원 PyTorch 설치를 건너뜁니다.${C_NC}"
    echo "만약 GPU가 있다면, 드라이버가 올바르게 설치되었는지 확인하세요."
fi

# --- 4. 완료 및 다음 단계 안내 ---
echo ""
echo -e "${C_GREEN}=========================================${C_NC}"
echo -e "${C_GREEN}  환경 설정이 성공적으로 완료되었습니다!  ${C_NC}"
echo -e "${C_GREEN}=========================================${C_NC}"
echo ""
echo "서버를 실행하려면 아래 단계를 따르세요:"
echo "1. 다음 명령어로 가상 환경을 활성화합니다:"
echo -e "   ${C_YELLOW}source venv/bin/activate${C_NC}"
echo "2. 다음 명령어로 애플리케이션을 실행합니다:"
echo -e "   ${C_YELLOW}python app.py${C_NC}"
echo ""
