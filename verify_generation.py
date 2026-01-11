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
    
    # Test model 1: int8
    model_name_1 = "Disty0/Z-Image-Turbo-SDNQ-int8"
    print(f"Testing load for {model_name_1}...")
    try:
        handler.load_model(model_name_1)
        print(f"Successfully loaded {model_name_1}")
        
        # Generaton test (low steps for speed)
        print("Testing generation...")
        img = handler.generate("A cat", steps=1, width=256, height=256)
        if img:
            print("Generation successful!")
            img.save("test_output_int8.png")
        else:
            print("Generation returned None")
            
    except Exception as e:
        print(f"Failed verification for {model_name_1}: {e}")
        # Continue to next model even if this fails? better to stop and report
    
    # Test model 2: uint4
    model_name_2 = "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32"
    print(f"Testing load for {model_name_2}...")
    try:
        handler.load_model(model_name_2)
        print(f"Successfully loaded {model_name_2}")
         # Generaton test (low steps for speed)
        print("Testing generation...")
        img = handler.generate("A dog", steps=1, width=256, height=256)
        if img:
            print("Generation successful!")
            img.save("test_output_uint4.png")
        else:
            print("Generation returned None")

    except Exception as e:
        print(f"Failed verification for {model_name_2}: {e}")

if __name__ == "__main__":
    verify()
