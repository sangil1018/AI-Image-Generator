# AI Image Generator

FastAPI와 웹 인터페이스를 기반으로 하는 고성능 AI 이미지 생성기입니다. Stable Diffusion Turbo, FLUX, Qwen 등 다양한 최신 모델을 지원하며, 사용하기 쉬운 웹 UI를 통해 손쉽게 이미지를 생성할 수 있습니다.

## 주요 아키텍처

- **백엔드**: WSL2 또는 Linux 환경에서 실행되는 Python FastAPI 서버.
- **프론트엔드**: 모든 최신 웹 브라우저에서 접근 가능한 반응형 웹 UI.
- **Unity 연동 (선택 사항)**: Unity의 WebView 컴포넌트를 사용하여 Unity 에디터 또는 애플리케이션 내에 웹 UI를 통합할 수 있습니다.

---

## 설치 및 실행 방법 (상세)

이 섹션에서는 WSL2(Windows Subsystem for Linux) 환경을 기준으로 처음부터 서버를 실행하기까지의 모든 과정을 상세히 설명합니다.

### 사전 준비 사항

1.  **WSL2 설치**: Windows 사용자라면 반드시 WSL2와 Ubuntu와 같은 Linux 배포판이 설치되어 있어야 합니다.
2.  **Python 3.12 이상**: WSL2 터미널에서 `python3 --version` 명령으로 버전을 확인하세요.
3.  **NVIDIA 드라이버 (GPU 사용자)**: GPU를 사용하려면 Windows에 최신 NVIDIA Game Ready 드라이버(CUDA 12.6 호환)가 설치되어 있어야 하며, WSL2에서 CUDA를 지원해야 합니다.

### 1단계: 프로젝트 다운로드 및 폴더 준비

WSL2 터미널을 열고 다음 명령어를 순서대로 실행하세요.

```bash
# 1. 프로젝트를 홈 디렉토리에 다운로드합니다.
cd ~
git clone https://github.com/YourUsername/YourRepository.git # 이 부분은 실제 프로젝트의 Git 주소로 변경해야 합니다.
# 만약 Git을 사용하지 않는다면, 프로젝트 파일을 이 위치에 복사하세요.

# 2. AI 모델과 LoRA 파일을 저장할 전용 폴더를 홈 디렉토리에 생성합니다.
mkdir ~/AI-models
mkdir ~/AI-loras

# 3. 이 폴더들에 사용하고자 하는 모델과 LoRA 파일(.safetensors)을 미리 넣어두세요.
# 예: Hugging Face 등에서 다운로드한 모델 파일
```

### 2단계: 자동 환경 구성 스크립트 실행

프로젝트에 포함된 `setup.sh` 스크립트가 Python 가상 환경 생성 및 라이브러리 설치를 자동화합니다.

```bash
# 1. 다운로드한 프로젝트 폴더로 이동합니다.
cd YourRepository # 실제 프로젝트 폴더 이름으로 변경

# 2. setup.sh 스크립트에 실행 권한을 부여합니다. (최초 한 번만 필요)
chmod +x setup.sh

# 3. 설치 스크립트를 실행합니다.
./setup.sh
```
스크립트가 성공적으로 완료되면, 화면의 안내에 따라 다음 단계를 진행할 수 있습니다.

### 3단계: 백엔드 서버 실행

모든 설정이 완료되었습니다. 다음 명령어로 서버를 시작하세요.

```bash
# 1. 가상 환경을 활성화합니다. (스크립트 마지막 안내 참고)
source venv/bin/activate

# 2. app.py를 실행하여 서버를 시작합니다.
python app.py
```

서버가 성공적으로 시작되면, 다음과 같은 메시지가 터미널에 나타납니다.

```
INFO:     Uvicorn running on http://0.0.0.0:8888 (Press CTRL+C to quit)
API 서버를 http://0.0.0.0:8888 에서 시작합니다.
API 문서는 http://0.0.0.0:8888/docs 에서 볼 수 있습니다.
```

---

## 사용 방법

1.  웹 브라우저를 열고 주소창에 `http://localhost:8888`을 입력합니다.
2.  화면에 나타난 웹 UI를 통해 모델과 LoRA를 선택하고, 프롬프트를 입력하여 이미지 생성을 시작하세요.
3.  Unity에서 사용하려면, WebView 컴포넌트가 `http://localhost:8888` 주소를 로드하도록 설정합니다.

서버를 중지하려면 터미널에서 `Ctrl + C`를 누르세요.

---

## 도커(Docker)를 이용한 배포 (권장)

도커를 사용하면 복잡한 설치 과정 없이, 어떤 컴퓨터에서든 동일한 환경으로 프로그램을 실행할 수 있습니다. 다른 사람에게 배포하거나 서버 환경에 설치할 때 가장 안정적이고 편리한 방법입니다.

### 사전 준비 사항

1.  **Docker Desktop 설치**: [Docker 공식 홈페이지](https://www.docker.com/products/docker-desktop/)에서 OS에 맞게 설치합니다. (Windows 사용자는 WSL2 백엔드 사용을 권장합니다.)
2.  **NVIDIA Container Toolkit (GPU 사용자)**: 도커 컨테이너 내부에서 NVIDIA GPU를 사용하려면 반드시 필요합니다. [NVIDIA 공식 문서](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)를 참고하여 설치하세요.

### 1단계: 도커 이미지 빌드

프로젝트의 모든 설정과 코드를 담은 '실행 패키지(이미지)'를 만듭니다. 프로젝트의 루트 디렉토리(Dockerfile이 있는 위치)에서 다음 명령어를 실행하세요.

```bash
docker build -t ai-image-generator .
```
- `-t ai-image-generator`: 생성될 도커 이미지에 `ai-image-generator`라는 이름과 태그를 붙입니다.

### 2단계: 도커 컨테이너 실행

빌드된 이미지를 실행하여 서버를 시작합니다.

```bash
docker run --gpus all -p 8888:8888 \
  -v ~/AI-models:/root/AI-models \
  -v ~/AI-loras:/root/AI-loras \
  --name ai-server \
  -d \
  ai-image-generator
```

위 명령어는 복잡해 보이지만 각 옵션은 중요한 역할을 합니다.

- `--gpus all`: 컨테이너가 호스트 컴퓨터의 모든 NVIDIA GPU를 사용할 수 있도록 허용합니다.
- `-p 8888:8888`: 호스트 컴퓨터의 8888번 포트를 컨테이너의 8888번 포트와 연결합니다. 이를 통해 `http://localhost:8888`로 접속할 수 있습니다.
- `-v ~/AI-models:/root/AI-models`: 호스트 컴퓨터의 `~/AI-models` 폴더를 컨테이너 내부의 `/root/AI-models` 폴더에 연결(마운트)합니다. 이렇게 하면 거대한 모델 파일들을 이미지에 포함시키지 않고, 외부에서 관리할 수 있습니다.
- `-v ~/AI-loras:/root/AI-loras`: LoRA 폴더도 동일하게 연결합니다.
- `--name ai-server`: 실행되는 컨테이너에 `ai-server`라는 이름을 부여하여 나중에 관리하기 쉽게 합니다.
- `-d`: 컨테이너를 백그라운드에서 실행합니다. (터미널을 종료해도 서버가 계속 실행됨)

### 도커 컨테이너 관리

- **서버 로그 확인**: `docker logs ai-server`
- **서버 중지**: `docker stop ai-server`
- **서버 재시작**: `docker start ai-server`
- **서버 완전 삭제**: `docker rm ai-server` (중지 후 실행)
