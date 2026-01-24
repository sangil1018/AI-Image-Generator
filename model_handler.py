# -*- coding: utf-8 -*-
import gc
import json
import os
import sys

# --- 지연 로딩될 라이브러리 (Lazy-loaded library placeholders) ---
torch = None
diffusers = None
DiffusionPipeline = None
AutoPipelineForText2Image = None
FluxPipeline = None
SDNQConfig = None
_triton_available = False # Triton 설치 여부를 저장할 플래그
apply_sdnq_options_to_model = None

def _lazy_import():
    """
    무거운 AI 라이브러리를 처음 필요할 때만 가져옵니다.
    이로 인해 애플리케이션 시작 속도가 매우 빨라집니다.
    """
    global torch, diffusers, DiffusionPipeline, AutoPipelineForText2Image, FluxPipeline, SDNQConfig, _triton_available, apply_sdnq_options_to_model
    
    if torch is not None:
        return

    print("AI 라이브러리를 처음으로 불러오는 중입니다. 잠시만 기다려 주세요...")
    try:
        # Triton 설치 여부 확인
        try:
            import triton
            _triton_available = True
            print("Triton 이 감지되었습니다. 양자화 최적화가 활성화됩니다.")
        except ImportError:
            _triton_available = False
            print("Triton 이 설치되어 있지 않습니다. 일부 모델의 양자화 최적화가 비활성화됩니다.")

        import torch as torch_lib
        import diffusers as diffusers_lib
        from diffusers import DiffusionPipeline as DP_lib, AutoPipelineForText2Image as AP_lib, FluxPipeline as FP_lib
        from sdnq import SDNQConfig as SDNQ_lib
        from sdnq.loader import apply_sdnq_options_to_model as apply_sdnq_lib

        torch = torch_lib
        diffusers = diffusers_lib
        DiffusionPipeline = DP_lib
        AutoPipelineForText2Image = AP_lib
        FluxPipeline = FP_lib
        SDNQConfig = SDNQ_lib
        apply_sdnq_options_to_model = apply_sdnq_lib
        
        print("라이브러리 로딩 완료.")
    except ImportError as e:
        print(f"치명적 오류: 필수 라이브러리를 불러올 수 없습니다. ({e})")
        print("venv 환경이 올바르게 설정되었는지, requirements.txt의 모든 패키지가 설치되었는지 확인해 주세요.")
        sys.exit(1)

if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class ModelHandler:
    def __init__(self):
        """
        ModelHandler를 초기화합니다.
        실제 모델과 무거운 라이브러리는 필요할 때까지 로드되지 않습니다.
        """
        self.pipeline = None
        self.current_model_name = None
        self.current_lora = None
        self.model_type = None # 'sd', 'flux', 'qwen' 등 모델 아키텍처 타입
        self.cache_dir = os.path.join(os.path.expanduser("~"), "AI-models")
        print(f"모델 디렉토리: {self.cache_dir}")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_pipeline_info(self, model_name):
        """모델 이름에 따라 적절한 파이프라인 클래스와 로더 인수를 반환합니다."""
        _lazy_import()
        model_name_lower = model_name.lower()
        dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

        if 'flux' in model_name_lower:
            print("FLUX 모델 타입 감지됨.")
            return AutoPipelineForText2Image, 'flux', {'torch_dtype': dtype}
        elif 'qwen' in model_name_lower:
            print("Qwen 모델 타입 감지됨.")
            return AutoPipelineForText2Image, 'qwen', {'torch_dtype': dtype}
        else: # 기본값: Stable Diffusion
            print("Stable Diffusion 모델 타입 감지됨.")
            return DiffusionPipeline, 'sd', {'torch_dtype': dtype, 'use_safetensors': True}

    def load_model(self, model_name):
        """AI 모델을 아키텍처에 맞게 메모리로 로드합니다."""
        if self.current_model_name == model_name:
            return self.pipeline

        if self.pipeline:
            del self.pipeline
            gc.collect()
            torch.cuda.empty_cache()
            self.pipeline = None
            self.current_lora = None
            self.model_type = None

        print(f"모델 로딩 중: {model_name}")
        
        try:
            pipeline_class, model_type, loader_args = self._get_pipeline_info(model_name)
            
            self.pipeline = pipeline_class.from_pretrained(
                model_name,
                **loader_args,
                cache_dir=self.cache_dir
            )
            self.model_type = model_type

            # SDNQ 최적화 적용: 모델 이름에 'sdnq'가 포함되고 Triton이 사용 가능한 경우에만 양자화 시도
            if _triton_available and 'sdnq' in model_name.lower() and (torch.cuda.is_available() or hasattr(torch, 'xpu') and torch.xpu.is_available()):
                print("SDNQ 모델 감지됨. 양자화 최적화를 시도합니다.")
                # 모델의 각 구성 요소에 양자화 적용 시도
                for attr_name in ['transformer', 'text_encoder', 'text_encoder_2', 'unet']:
                    if hasattr(self.pipeline, attr_name) and getattr(self.pipeline, attr_name) is not None:
                        try:
                            component = getattr(self.pipeline, attr_name)
                            setattr(self.pipeline, attr_name, apply_sdnq_options_to_model(component, use_quantized_matmul=True))
                            print(f"SDNQ 최적화 적용됨: {attr_name} (INT8 MatMul)")
                        except Exception as e:
                            print(f"경고: '{attr_name}'에 SDNQ 최적화를 적용하지 못했습니다: {e}")
            
            self.pipeline.to("cuda")
            self.current_model_name = model_name
            print("모델 로딩 성공.")
            return self.pipeline
        except Exception as e:
            print(f"모델 {model_name} 로딩 중 오류 발생: {e}")
            self.current_model_name = None
            self.model_type = None
            raise e

    def load_lora(self, lora_path):
        """LoRA 파일을 로드합니다. 모델이 지원하는 경우에만 적용됩니다."""
        _lazy_import()
        if self.current_lora == lora_path:
            return

        if not self.pipeline:
            raise ValueError("LoRA를 로드하기 전에 기본 모델을 먼저 로드해야 합니다.")

        # 이전에 로드된 LoRA가 있으면 먼저 제거
        if self.current_lora is not None:
            try:
                self.pipeline.delete_adapter(["default_lora"])
                print(f"기존 LoRA 어댑터 '{self.current_lora}' 제거됨.")
            except Exception: pass
        self.current_lora = None
        
        # LoRA 경로가 없으면 여기서 종료 (LoRA 비활성화)
        if lora_path is None: 
            print("LoRA 비활성화됨.")
            return

        print(f"LoRA 로딩 시도 중: {lora_path}")
        try:
            # 이제 모든 모델에 대해 LoRA 로드를 시도합니다.
            self.pipeline.load_lora_weights(lora_path, adapter_name="default_lora")
            self.current_lora = lora_path
            print("LoRA 로딩 성공.")
        except Exception as e:
            # 실패할 경우, 경고를 출력하고 계속 진행합니다.
            print(f"경고: 현재 모델 '{self.current_model_name}'은(는) LoRA '{lora_path}'를 지원하지 않을 수 있습니다. 오류: {e}")
            self.current_lora = None
            # 에러를 다시 발생시키지 않고, LoRA 없이 계속 진행하도록 합니다.

    def generate(self, **kwargs):
        """로드된 모델 타입에 맞춰 적절한 인수로 이미지를 생성합니다."""
        _lazy_import()
        if not self.pipeline:
            raise ValueError("로드된 모델이 없습니다. 먼저 모델을 선택해 주세요.")

        # 공통 파라미터 추출
        prompt = kwargs.get('prompt', "")
        width = kwargs.get('width', 1024)
        height = kwargs.get('height', 1024)
        seed = kwargs.get('seed', -1)
        steps = kwargs.get('steps', 8)
        
        generator = torch.Generator("cuda").manual_seed(int(seed)) if seed not in [None, -1] else None
        
        gen_args = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_inference_steps": steps,
            "generator": generator
        }
        
        print(f"'{self.model_type}' 타입 모델을 사용하여 이미지 생성 중...")

        # 1. LoRA 어댑터 처리: 모델 타입과 관계없이 로드된 LoRA가 있다면 활성화를 시도
        lora_scale = kwargs.get('lora_scale', 0.8)
        if self.current_lora:
            try:
                self.pipeline.set_adapters(["default_lora"], adapter_weights=[lora_scale])
                print(f"LoRA '{self.current_lora}' 활성화 (강도: {lora_scale}).")
            except Exception as e:
                print(f"경고: LoRA 어댑터 가중치를 설정하지 못했습니다. LoRA가 적용되지 않을 수 있습니다. 오류: {e}")
        elif self.model_type == 'sd':
            # SD 계열 파이프라인은 LoRA가 없을 때 비활성화 호출이 필요할 수 있음
            try:
                self.pipeline.disable_lora()
            except Exception: pass

        # 2. 모델 아키텍처별 인수 처리
        if self.model_type == 'flux':
            # FLUX는 일반적으로 negative_prompt와 guidance_scale을 무시함
            pass 
        else:
            # SD, Qwen 등 다른 모델들은 이 파라미터들을 사용
            gen_args["negative_prompt"] = kwargs.get('negative_prompt', "")
            gen_args["guidance_scale"] = kwargs.get('guidance_scale', 0.0)

        image = self.pipeline(**gen_args).images[0]
        
        return image
