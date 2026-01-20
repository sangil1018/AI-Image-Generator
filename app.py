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

# --- Path setup for portable executable ---
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # Running as a normal script
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

LORA_DIR = os.path.join(BASE_PATH, "lora")
MODELS_DIR = os.path.join(BASE_PATH, "models")

# Initialize the model handler
try:
    handler = ModelHandler()
except Exception as e:
    print(f"Failed to initialize ModelHandler: {e}")
    # Exit if the handler is critical and cannot be initialized
    sys.exit(1)

# --- Dynamic Scanners for Models and LoRAs ---
def get_lora_files():
    """Scans the LORA_DIR for .safetensors files."""
    if not os.path.exists(LORA_DIR):
        os.makedirs(LORA_DIR)
        return ["None"]
    
    files = [f for f in os.listdir(LORA_DIR) if f.endswith(".safetensors")]
    return ["None"] + files

def get_model_names():
    """
    Scans the MODELS_DIR for model directories and converts them back to
    Hugging Face repository IDs.
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

# --- Pydantic Models for API validation ---
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

# --- FastAPI App ---
app = FastAPI(
    title="Z-Image-Turbo API",
    description="An API for ultra-fast AI image generation.",
    version="1.0.0"
)

@app.get("/api/models", tags=["Info"])
async def get_models_api():
    """Returns a list of available models."""
    return {"models": get_model_names()}

@app.get("/api/loras", tags=["Info"])
async def get_loras_api():
    """Returns a list of available LoRA files."""
    return {"loras": get_lora_files()}

@app.post("/api/generate", tags=["Image Generation"])
async def generate_image_api(request: GenerationRequest):
    """Generates an image based on the provided prompt and settings."""
    try:
        # Load the base model if it's not the current one
        handler.load_model(request.model_name)
        
        # Load LoRA if selected
        lora_path = os.path.join(LORA_DIR, request.lora_name) if request.lora_name != "None" else None
        handler.load_lora(lora_path)

        # Generate image
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
            raise HTTPException(status_code=500, detail="Model failed to generate an image.")
        
        # Convert PIL image to a byte stream
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        
        return StreamingResponse(buffer, media_type="image/png")

    except Exception as e:
        print(f"Error in /api/generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Server Lifecycle Management ---
server_instance = None

def kill_process_on_port(port):
    """Find and kill the process running on the given port (Windows only)."""
    if os.name != 'nt':
        print(f"Port clearing feature is only supported on Windows.")
        return
    
    print(f"Checking for any process on port {port}...")
    try:
        command = f"netstat -aon | findstr ':{port}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        output = result.stdout.strip()

        if not output:
            print(f"Port {port} is free.")
            return

        pids_found = set(re.findall(r'\s(\d+)\s*$', output, re.MULTILINE))
        if not pids_found: return

        for pid in pids_found:
            print(f"Found process {pid} on port {port}. Terminating...")
            try:
                kill_command = f"taskkill /F /PID {pid}"
                subprocess.run(kill_command, shell=True, check=True, capture_output=True, text=True)
                print(f"Successfully terminated process {pid}.")
            except subprocess.CalledProcessError as e:
                if "not found" not in e.stderr.strip():
                     print(f"Failed to terminate process {pid}: {e.stderr.strip()}")
        
        time.sleep(2)
    except Exception as e:
        print(f"An error occurred while trying to free up port {port}: {e}")

@app.post("/shutdown", tags=["Admin"])
async def shutdown():
    """Triggers a graceful server shutdown."""
    global server_instance
    if server_instance:
        threading.Thread(target=server_instance.shutdown).start()
        return {"message": "Server is shutting down"}
    return {"message": "Server instance not found."}

if __name__ == "__main__":
    PORT = 8888
    
    # Check and kill any process using the server port before starting
    kill_process_on_port(PORT)
    
    class Server(uvicorn.Server):
        def install_signal_handlers(self):
            pass

    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = Server(config=config)
    server_instance = server
    
    print(f"Starting API server at http://0.0.0.0:{PORT}")
    print(f"View API docs at http://0.0.0.0:{PORT}/docs")
    server.run()