# Z-Image-Turbo 이미지 생성기

`Z-Image-Turbo` (SDNQ 양자화 기술)를 활용한 초고속 AI 이미지 생성기입니다. 최신 트렌드의 프리미엄 다크/글래스모피즘 UI가 적용되었습니다.

## 주요 기능
- **초고속 생성**: SDNQ int8 양자화 및 `torch.compile` 최적화를 통해 빠른 속도로 이미지를 생성합니다.
- **프리미엄 UI**: Gradio 기반의 세련된 다크 모드 및 글래스모피즘 디자인.
- **사용자 설정**: 모델 저장 경로를 `config.json`을 통해 자유롭게 변경 가능.
- **포터블 빌드**: 독립 실행 가능한 `.exe` 파일로 빌드 지원.

## 설치 방법 (Installation)

1. **다운로드**: 이 저장소를 클론(Clone)하거나 다운로드합니다.
2. **설정 실행**:
   `setup_env.bat` 파일을 더블 클릭하여 실행하세요.
   - 자동으로 Python 가상 환경(venv)을 생성하고 필요한 라이브러리를 설치합니다.
   - RTX 5090 등 최신 GPU 사용자는 설치 중 안내되는 메시지를 참고하세요.

## 사용 방법 (Usage)

**소스 코드로 실행 시:**
`run.bat` 파일을 더블 클릭하면 프로그램이 시작됩니다.

**EXE 파일로 실행 시 (빌드 후):**
`dist/Z-Image-Turbo` 폴더 내의 `Z-Image-Turbo.exe`를 실행하세요.

## 환경 설정 (`config.json`)
대용량 모델 파일이 저장될 위치를 변경할 수 있습니다.
프로젝트 최상위 폴더에 `config.json` 파일이 없다면 생성하고, 아래와 같이 작성하세요:
```json
{
    "model_storage_path": "D:/MyCustomModelPath"
}
```
설정하지 않을 경우 기본적으로 `./models` 폴더(또는 Hugging Face 기본 캐시)에 저장됩니다.

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
  *(RTX 5090 사용자는 `cu124` 대신 `cu128`이나 Nightly 버전을 사용해야 할 수 있습니다.)*

- **"Triton is not available" 경고**:
  Windows 환경에서는 Triton이 기본적으로 지원되지 않아 발생하는 경고입니다. 무시하셔도 되며, 프로그램은 PyTorch 기본 모드(Eager mode)로 정상 작동합니다.
