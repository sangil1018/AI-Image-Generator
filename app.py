# -*- coding: utf-8 -*-
import os
import sys
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import threading
import time
import subprocess
import re
import io

from model_handler import ModelHandler

# --- 휴대용 실행 파일을 위한 경로 설정 ---
if getattr(sys, 'frozen', False):
    # PyInstaller 번들로 실행 중
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # 일반 스크립트로 실행 중
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

LORA_DIR = os.path.join(BASE_PATH, "lora")
MODELS_DIR = os.path.join(BASE_PATH, "models")

# 모델 핸들러 초기화
try:
    handler = ModelHandler()
except Exception as e:
    print(f"ModelHandler 초기화 실패: {e}")
    # 핸들러가 중요하고 초기화할 수 없는 경우 종료
    sys.exit(1)

# --- 모델 및 LoRA 동적 스캐너 ---
def get_lora_files():
    """LORA_DIR에서 .safetensors 파일을 스캔합니다."""
    if not os.path.exists(LORA_DIR):
        os.makedirs(LORA_DIR)
        return ["None"]
    
    files = [f for f in os.listdir(LORA_DIR) if f.endswith(".safetensors")]
    return ["None"] + files

def get_model_names():
    """
    MODELS_DIR에서 모델 디렉토리를 스캔하고
    Hugging Face 저장소 ID로 다시 변환합니다.
    """
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        return []
    
    model_names = []
    for d in os.listdir(MODELS_DIR):
        if d.startswith("models--"):
            repo_id = d.replace("models--", "").replace("--", "/")
            model_names.append(repo_id)
    return model_names

# --- API 유효성 검사를 위한 Pydantic 모델 ---
class GenerationRequest(BaseModel):
    model_name: str
    lora_name: Optional[str] = "None"
    lora_scale: Optional[float] = 0.7
    prompt: str
    negative_prompt: Optional[str] = ""
    steps: int = Field(default=8, ge=1, le=50)
    guidance_scale: float = Field(default=0.0)
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    seed: int = Field(default=-1)

# --- FastAPI 앱 ---
app = FastAPI(
    title="Z-Image-Turbo API",
    description="초고속 AI 이미지 생성을 위한 API입니다.",
    version="1.0.0"
)

@app.get("/api/models", tags=["정보"])
async def get_models_api():
    """사용 가능한 모델 목록을 반환합니다."""
    return {"models": get_model_names()}

@app.get("/api/loras", tags=["정보"])
async def get_loras_api():
    """사용 가능한 LoRA 파일 목록을 반환합니다."""
    return {"loras": get_lora_files()}

@app.post("/api/generate", tags=["이미지 생성"])
async def generate_image_api(request: GenerationRequest):
    """제공된 프롬프트와 설정을 기반으로 이미지를 생성합니다."""
    try:
        # 현재 모델이 아닌 경우 기본 모델 로드
        handler.load_model(request.model_name)
        
        # 선택된 경우 LoRA 로드
        lora_path = os.path.join(LORA_DIR, request.lora_name) if request.lora_name != "None" else None
        handler.load_lora(lora_path)

        # 이미지 생성
        image = handler.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            width=request.width,
            height=request.height,
            seed=request.seed,
            lora_scale=request.lora_scale
        )

        if image is None:
            raise HTTPException(status_code=500, detail="모델이 이미지 생성에 실패했습니다.")
        
        # PIL 이미지를 바이트 스트림으로 변환
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        return StreamingResponse(buffer, media_type="image/png")

    except Exception as e:
        print(f"/api/generate 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 서버 생명주기 관리 ---
server_instance = None

def kill_process_on_port(port):
    """주어진 포트에서 실행 중인 프로세스를 찾아 종료합니다 (Windows 전용)."""
    if os.name != 'nt':
        print(f"포트 정리 기능은 Windows에서만 지원됩니다.")
        return
    
    print(f"{port}번 포트에서 실행 중인 프로세스를 확인하는 중...")
    try:
        command = f"netstat -aon | findstr ':{port}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        output = result.stdout.strip()

        if not output:
            print(f"{port}번 포트는 비어있습니다.")
            return

        pids_found = set(re.findall(r'\s(\d+)\s*$', output, re.MULTILINE))
        if not pids_found: return

        for pid in pids_found:
            print(f"{port}번 포트에서 프로세스 {pid}를 찾았습니다. 종료 중...")
            try:
                kill_command = f"taskkill /F /PID {pid}"
                subprocess.run(kill_command, shell=True, check=True, capture_output=True, text=True)
                print(f"프로세스 {pid}를 성공적으로 종료했습니다.")
            except subprocess.CalledProcessError as e:
                if "not found" not in e.stderr.strip():
                     print(f"프로세스 {pid}를 종료하지 못했습니다: {e.stderr.strip()}")
        
        time.sleep(2)
    except Exception as e:
        print(f"포트를 비우는 동안 오류가 발생했습니다: {e}")

@app.post("/shutdown", tags=["관리자"])
async def shutdown():
    """서버를 정상적으로 종료합니다."""
    global server_instance
    if server_instance:
        threading.Thread(target=server_instance.shutdown).start()
        return {"message": "서버를 종료하고 있습니다."}
    return {"message": "서버 인스턴스를 찾을 수 없습니다."}

if __name__ == "__main__":
    PORT = 8888
    
    # 시작하기 전에 서버 포트를 사용하는 모든 프로세스를 확인하고 종료합니다.
    kill_process_on_port(PORT)
    
    class Server(uvicorn.Server):
        def install_signal_handlers(self):
            pass

    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = Server(config=config)
    server_instance = server
    
    print(f"API 서버를 http://0.0.0.0:{PORT} 에서 시작합니다.")
    print(f"API 문서는 http://0.0.0.0:{PORT}/docs 에서 볼 수 있습니다.")
    server.run()