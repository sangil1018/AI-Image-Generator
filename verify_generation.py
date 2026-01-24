import os
import sys

# Ensure we can import model_handler
sys.path.append(os.getcwd())

try:
    from model_handler import ModelHandler
    print("Successfully imported ModelHandler")
except ImportError as e:
    print(f"Failed to import ModelHandler: {e}")
    sys.exit(1)

def verify():
    handler = ModelHandler()
    
    # Test model 1: z-image-turbo
    model_name_1 = "Disty0/Z-Image-Turbo-SDNQ-int8"
    print(f"Testing load for {model_name_1}...")
    try:
        handler.load_model(model_name_1)
        print(f"Successfully loaded {model_name_1}")
        
        # Generaton test (low steps for speed)
        print("Testing generation...")
        img = handler.generate(prompt="A cat", steps=1, width=256, height=256)
        if img:
            print("Generation successful!")
            img.save("test_output_zit.png")
        else:
            print("Generation returned None")
            
    except Exception as e:
        print(f"Failed verification for {model_name_1}: {e}")
        # Continue to next model even if this fails? better to stop and report
    
    # Test model 2: flux.2-klein
    model_name_2 = "Disty0/FLUX.2-klein-9B-SDNQ-4bit-dynamic-svd-r32"
    print(f"Testing load for {model_name_2}...")
    try:
        handler.load_model(model_name_2)
        print(f"Successfully loaded {model_name_2}")
         # Generaton test (low steps for speed)
        print("Testing generation...")
        img = handler.generate(prompt="A dog", steps=1, width=256, height=256)
        if img:
            print("Generation successful!")
            img.save("test_output_flux2-klein.png")
        else:
            print("Generation returned None")

    except Exception as e:
        print(f"Failed verification for {model_name_2}: {e}")

    # Test model 3: flux.1-krea
    model_name_3 = "Disty0/FLUX.1-Krea-dev-SDNQ-uint4-svd-r32"
    print(f"Testing load for {model_name_3}...")
    try:
        handler.load_model(model_name_3)
        print(f"Successfully loaded {model_name_3}")
         # Generaton test (low steps for speed)
        print("Testing generation...")
        img = handler.generate(prompt="A dog", steps=1, width=256, height=256)
        if img:
            print("Generation successful!")
            img.save("test_output_flux1-krea.png")
        else:
            print("Generation returned None")

    except Exception as e:
        print(f"Failed verification for {model_name_3}: {e}")
        
    # Test model 3: qwen-image
    model_name_4 = "Disty0/Qwen-Image-2512-SDNQ-4bit-dynamic"
    print(f"Testing load for {model_name_4}...")
    try:
        handler.load_model(model_name_4)
        print(f"Successfully loaded {model_name_4}")
         # Generaton test (low steps for speed)
        print("Testing generation...")
        img = handler.generate(prompt="A dog", steps=4, width=256, height=256) # Increased steps to 4 for Qwen
        if img:
            print("Generation successful!")
            img.save("test_output_qwen-image.png")
        else:
            print("Generation returned None")

    except Exception as e:
        print(f"Failed verification for {model_name_4}: {e}")

if __name__ == "__main__":
    verify()
