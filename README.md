# Z-Image-Turbo API 서버

`Z-Image-Turbo` (SDNQ 양자화 기술)를 활용한 초고속 AI 이미지 생성 API 서버입니다.

## 주요 기능
- **초고속 생성**: SDNQ int8 양자화 및 `torch.compile` 최적화를 통해 빠른 속도로 이미지를 생성합니다.
- **FastAPI 백엔드**: 웹 UI 대신 안정적이고 빠른 FastAPI를 기반으로 하는 API 서버를 제공합니다.
- **Unity 연동 예제**: Unity에서 API 서버와 통신하여 이미지를 생성하고 UI에 표시하는 C# 클라이언트 예제를 포함합니다. (`unity gen` 폴더 참고)
- **포터블 빌드**: API 서버를 독립 실행 가능한 `.exe` 파일로 빌드할 수 있습니다.

## 설치 방법 (Installation)

1. **다운로드**: 이 저장소를 클론(Clone)하거나 다운로드합니다.
2. **설정 실행**:
   `setup_env.bat` 파일을 더블 클릭하여 실행하세요.
   - 자동으로 Python 가상 환경(venv)을 생성하고 필요한 라이브러리를 설치합니다.

## 사용 방법 (Usage)

`run.bat` 파일을 더블 클릭하면 API 서버가 시작됩니다. 서버가 실행되면 `http://127.0.0.1:8888/docs`에서 사용 가능한 API 목록과 테스트 도구를 확인할 수 있습니다.

**빌드된 EXE 파일로 실행 시:**
`dist` 폴더 내의 `Z-Image-Turbo.exe` (빌드 후 생성됨)를 실행하면 동일하게 API 서버가 시작됩니다.

## EXE 빌드 방법

소스 코드를 단일 실행 파일로 만들려면:
1. `setup_env.bat`이 성공적으로 완료되었는지 확인하세요.
2. `build_exe.bat` 파일을 더블 클릭하여 실행하세요.
3. 빌드가 완료되면 `dist` 폴더에 실행 파일이 생성됩니다. (시간이 5~10분 소요될 수 있습니다)

## 문제 해결 (Troubleshooting)

- **"Torch not compiled with CUDA enabled" 오류**:
  현재 설치된 PyTorch가 GPU를 지원하지 않을 때 발생합니다. 수동으로 다시 설치해야 합니다:
  ```cmd
  venv\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
  ```

- **"Triton is not available" 경고**:
  Windows 환경에서는 Triton이 기본적으로 지원되지 않아 발생하는 경고입니다. 무시하셔도 되며, 프로그램은 PyTorch 기본 모드(Eager mode)로 정상 작동합니다.