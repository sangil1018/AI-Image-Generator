# -*- coding: utf-8 -*-
import gc
import json
import os
import sys

# --- 지연 로딩될 라이브러리 (Lazy-loaded library placeholders) ---
torch = None
diffusers = None
DiffusionPipeline = None
SDNQConfig = None
triton_is_available = None
apply_sdnq_options_to_model = None

def _lazy_import():
    """
    무거운 AI 라이브러리를 처음 필요할 때만 가져옵니다.
    이로 인해 애플리케이션 시작 속도가 매우 빨라집니다.
    """
    global torch, diffusers, DiffusionPipeline, SDNQConfig, triton_is_available, apply_sdnq_options_to_model
    
    # 이미 임포트되었는지 확인
    if torch is not None:
        return

    print("AI 라이브러리를 처음으로 불러오는 중입니다. 잠시만 기다려 주세요...")
    try:
        import torch as torch_lib
        import diffusers as diffusers_lib
        from diffusers import DiffusionPipeline as DP_lib
        from sdnq import SDNQConfig as SDNQ_lib
        from sdnq.common import use_torch_compile as triton_lib
        from sdnq.loader import apply_sdnq_options_to_model as apply_sdnq_lib

        # 전역 변수에 할당
        torch = torch_lib
        diffusers = diffusers_lib
        DiffusionPipeline = DP_lib
        SDNQConfig = SDNQ_lib
        triton_is_available = triton_lib
        apply_sdnq_options_to_model = apply_sdnq_lib
        
        print("라이브러리 로딩 완료.")
    except ImportError as e:
        print(f"치명적 오류: 필수 라이브러리를 불러올 수 없습니다. ({e})")
        print("venv 환경이 올바르게 설정되었는지, requirements.txt의 모든 패키지가 설치되었는지 확인해 주세요.")
        sys.exit(1)


# 애플리케이션의 기본 경로 결정 (스크립트 및 PyInstaller .exe 모두에서 작동)
if getattr(sys, 'frozen', False):
    # PyInstaller 번들로 실행 중
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # 일반 스크립트로 실행 중
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))


class ModelHandler:
    def __init__(self):
        """
        ModelHandler를 초기화합니다.
        실제 모델과 무거운 라이브러리는 필요할 때까지 로드되지 않습니다.
        """
        self.pipeline = None
        self.current_model_name = None
        self.current_lora = None # 현재 로드된 LoRA 추적
        # cache_dir는 실행 파일/스크립트 옆의 'models' 폴더로 설정됩니다.
        self.cache_dir = os.path.join(BASE_PATH, "models")
        print(f"모델 디렉토리: {self.cache_dir}")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
    def load_lora(self, lora_path):
        """이름이 지정된 어댑터를 사용하여 LoRA 파일을 로드합니다."""
        _lazy_import() # 라이브러리가 로드되었는지 확인

        if self.current_lora == lora_path:
            return

        if not self.pipeline:
            raise ValueError("LoRA를 로드하기 전에 기본 모델을 먼저 로드해야 합니다.")

        # 이전에 로드된 LoRA가 있으면 해당 어댑터를 삭제합니다.
        if self.current_lora is not None:
            try:
                self.pipeline.delete_adapter(["default_lora"])
                print("이전 LoRA 어댑터 'default_lora'가 삭제되었습니다.")
            except Exception as e:
                print(f"경고: 어댑터 'default_lora'를 삭제할 수 없습니다: {e}")

        self.current_lora = None

        if lora_path is None:
            return

        print(f"LoRA 로딩 중: {lora_path}")
        try:
            # 일관된 어댑터 이름 사용
            self.pipeline.load_lora_weights(lora_path, adapter_name="default_lora")
            self.current_lora = lora_path
            print("LoRA 로딩 성공.")
        except Exception as e:
            print(f"LoRA {lora_path} 로딩 중 오류 발생: {e}")
            self.current_lora = None
            raise e

    def load_model(self, model_name):
        """AI 모델을 메모리로 로드합니다."""
        _lazy_import() # 라이브러리가 로드되었는지 확인
        
        if self.current_model_name == model_name:
            return self.pipeline

        # 메모리 확보를 위해 이전 모델 언로드
        if self.pipeline:
            del self.pipeline
            gc.collect()
            torch.cuda.empty_cache()
            self.pipeline = None
            self.current_lora = None

        print(f"모델 로딩 중: {model_name}")
        
        try:
            dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
            
            self.pipeline = DiffusionPipeline.from_pretrained(
                model_name,
                torch_dtype=dtype,
                use_safetensors=True,
                cache_dir=self.cache_dir
            )

            # AMD, Intel ARC, Nvidia GPU에 대해 INT8 MatMul 활성화
            if triton_is_available and (torch.cuda.is_available() or hasattr(torch, 'xpu') and torch.xpu.is_available()):
                try:
                    self.pipeline.transformer = apply_sdnq_options_to_model(self.pipeline.transformer, use_quantized_matmul=True)
                    self.pipeline.text_encoder = apply_sdnq_options_to_model(self.pipeline.text_encoder, use_quantized_matmul=True)
                    print("SDNQ 최적화 적용됨: INT8 MatMul")
                except Exception as e:
                    print(f"경고: SDNQ 최적화를 적용하지 못했습니다: {e}")

            self.pipeline.to("cuda")
            
            self.current_model_name = model_name
            print("모델 로딩 성공.")
            return self.pipeline
        except Exception as e:
            print(f"모델 {model_name} 로딩 중 오류 발생: {e}")
            self.current_model_name = None
            raise e

    def generate(self, prompt, negative_prompt="", steps=4, guidance_scale=0.0, width=1024, height=1024, seed=42, lora_scale=0.8):
        """이미지를 생성합니다."""
        _lazy_import() # 라이브러리가 로드되었는지 확인

        if not self.pipeline:
            raise ValueError("로드된 모델이 없습니다. 먼저 모델을 선택해 주세요.")

        if seed is not None and seed != -1:
            generator = torch.Generator("cuda").manual_seed(int(seed))
        else:
            generator = None

        # LoRA 선택에 따라 어댑터 설정
        if self.current_lora:
            self.pipeline.set_adapters(["default_lora"], adapter_weights=[lora_scale])
        else:
            self.pipeline.disable_lora()

        image = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            width=width,
            height=height,
            generator=generator
        ).images[0]
        
        return image
