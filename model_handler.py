import torch
import diffusers
from diffusers import DiffusionPipeline
from sdnq import SDNQConfig
from sdnq.common import use_torch_compile as triton_is_available
from sdnq.loader import apply_sdnq_options_to_model
import gc
import json
import os

import torch
import diffusers
from diffusers import DiffusionPipeline
from sdnq import SDNQConfig
from sdnq.common import use_torch_compile as triton_is_available
from sdnq.loader import apply_sdnq_options_to_model
import gc
import json
import os
import sys

# Determine the base path for the application, works for both script and PyInstaller .exe
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # Running as a normal script
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))


class ModelHandler:
    def __init__(self):
        self.pipeline = None
        self.current_model_name = None
        self.current_lora = None # Track current LoRA
        # The cache_dir is now programmatically set to be the 'models' folder next to the executable/script
        self.cache_dir = os.path.join(BASE_PATH, "models")
        print(f"Models directory set to: {self.cache_dir}")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # config.json is no longer used for model path.


    def load_lora(self, lora_path):
        """Loads a LoRA file using a named adapter."""
        if self.current_lora == lora_path:
            return

        if not self.pipeline:
            raise ValueError("Base model must be loaded before loading a LoRA.")

        # If a LoRA was previously loaded, delete that specific adapter
        if self.current_lora is not None:
            try:
                self.pipeline.delete_adapter(["default_lora"])
                print("Previous LoRA adapter 'default_lora' deleted.")
            except Exception as e:
                print(f"Warning: Could not delete adapter 'default_lora': {e}")

        self.current_lora = None

        if lora_path is None:
            return

        print(f"Loading LoRA: {lora_path}")
        try:
            # Using a consistent adapter name
            self.pipeline.load_lora_weights(lora_path, adapter_name="default_lora")
            self.current_lora = lora_path
            print("LoRA loaded successfully.")
        except Exception as e:
            print(f"Error loading LoRA {lora_path}: {e}")
            self.current_lora = None
            raise e

    def load_model(self, model_name):
        if self.current_model_name == model_name:
            return self.pipeline

        # Unload previous model to free memory
        if self.pipeline:
            del self.pipeline
            gc.collect()
            torch.cuda.empty_cache()
            self.pipeline = None
            self.current_lora = None

        print(f"Loading model: {model_name}")
        
        try:
            dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
            
            self.pipeline = DiffusionPipeline.from_pretrained(
                model_name,
                torch_dtype=dtype,
                use_safetensors=True, # Recommended for safety and speed
                cache_dir=self.cache_dir
            )

            # Enable INT8 MatMul for AMD, Intel ARC and Nvidia GPUs
            if triton_is_available and (torch.cuda.is_available() or hasattr(torch, 'xpu') and torch.xpu.is_available()):
                try:
                    self.pipeline.transformer = apply_sdnq_options_to_model(self.pipeline.transformer, use_quantized_matmul=True)
                    self.pipeline.text_encoder = apply_sdnq_options_to_model(self.pipeline.text_encoder, use_quantized_matmul=True)
                    # self.pipeline.transformer = torch.compile(self.pipeline.transformer) # optional for faster speeds
                    print("SDNQ Optimization applied: INT8 MatMul & torch.compile")
                except Exception as e:
                    print(f"Warning: Failed to apply SDNQ optimizations: {e}")

            self.pipeline.to("cuda")
            
            self.current_model_name = model_name
            print("Model loaded successfully.")
            return self.pipeline
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            self.current_model_name = None
            raise e

    def generate(self, prompt, negative_prompt="", steps=4, guidance_scale=0.0, width=1024, height=1024, seed=42, lora_scale=0.8):
        if not self.pipeline:
            raise ValueError("No model loaded. Please select a model first.")

        if seed is not None and seed != -1:
            generator = torch.Generator("cuda").manual_seed(int(seed))
        else:
            generator = None

        # New: Set adapter based on LoRA selection
        if self.current_lora:
            self.pipeline.set_adapters(["default_lora"], adapter_weights=[lora_scale])
        else:
            self.pipeline.disable_lora()

        image = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale, # This should be 0.0 for Turbo models
            width=width,
            height=height,
            generator=generator
        ).images[0]
        
        return image
