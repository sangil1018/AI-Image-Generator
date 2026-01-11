import torch
import diffusers
from diffusers import DiffusionPipeline
from sdnq import SDNQConfig
from sdnq.common import use_torch_compile as triton_is_available
from sdnq.loader import apply_sdnq_options_to_model
import gc
import json
import os

class ModelHandler:
    def __init__(self):
        self.pipeline = None
        self.current_model_name = None
        self.cache_dir = self._load_config()

    def _load_config(self):
        """Load configuration from config.json if available."""
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    path = data.get("model_storage_path", None)
                    if path:
                        print(f"Using custom model storage path: {path}")
                        return path
            except Exception as e:
                print(f"Error reading config.json: {e}")
        return None  # Use default huggingface location

    def load_model(self, model_name):
        if self.current_model_name == model_name:
            return self.pipeline

        # Unload previous model to free memory
        if self.pipeline:
            del self.pipeline
            gc.collect()
            torch.cuda.empty_cache()
            self.pipeline = None

        print(f"Loading model: {model_name}")
        
        try:
            # Use trust_remote_code=True for custom pipelines
            # Using bfloat16 as per user snippet
            dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
            
            # Use cache_dir if configured
            self.pipeline = DiffusionPipeline.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=dtype,
                cache_dir=self.cache_dir
            )

            # Enable INT8 MatMul for AMD, Intel ARC and Nvidia GPUs
            if triton_is_available and (torch.cuda.is_available() or hasattr(torch, 'xpu') and torch.xpu.is_available()):
                try:
                    self.pipeline.transformer = apply_sdnq_options_to_model(self.pipeline.transformer, use_quantized_matmul=False)
                    self.pipeline.text_encoder = apply_sdnq_options_to_model(self.pipeline.text_encoder, use_quantized_matmul=False)
                    self.pipeline.transformer = torch.compile(self.pipeline.transformer) # optional for faster speeds
                    print("SDNQ Optimization applied: INT8 MatMul & torch.compile")
                except Exception as e:
                    print(f"Warning: Failed to apply SDNQ optimizations: {e}")

            # CPU Offload - User requested to disable due to accelerator error
            # self.pipeline.enable_model_cpu_offload()
            self.pipeline.to("cuda")
            
            self.current_model_name = model_name
            print("Model loaded successfully.")
            return self.pipeline
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            self.current_model_name = None # Reset if failed
            raise e

    def generate(self, prompt, negative_prompt="", steps=4, guidance_scale=0.0, width=1024, height=1024, seed=42):
        if not self.pipeline:
            raise ValueError("No model loaded. Please select a model first.")

        if seed is not None and seed != -1:
            generator = torch.Generator("cuda").manual_seed(int(seed))
        else:
            generator = None

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
