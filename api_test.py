import requests
import os

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8888"
OUTPUT_IMAGE_PATH = "api_test_output.png"

def get_first_available_model():
    """Fetches the list of available models from the API and returns the first one."""
    try:
        response = requests.get(f"{BASE_URL}/api/models", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        if models:
            print(f"Found models: {models}")
            return models[1]
        else:
            print("Warning: No models found via API. Check if the server is running and models are in the 'models' folder.")
            return "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32" # Fallback
    except requests.exceptions.RequestException as e:
        print(f"Error fetching models: {e}")
        print("Using fallback model name.")
        return "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32" # Fallback

def test_generate_api():
    """
    Uses 'requests' to call the /api/generate endpoint.
    """
    print("--- Starting API Test for Image Generation (using requests) ---")

    # 1. Get a valid model name from the API
    print("\n1. Fetching available model...")
    model_name = get_first_available_model()
    print(f"   Using model: {model_name}")

    # 2. Define the payload for the POST request
    payload = {
        "model_name": model_name,
        "prompt": "a stunningly beautiful ultra-detailed cinematic portrait of a barbarian warrior queen, fantasy, golden hour",
        "negative_prompt": "blurry, low quality, deformed, ugly",
        "steps": 8,
        "width": 1024,
        "height": 1024,
        "seed": -1
    }
    print("\n2. Calling POST /api/generate...")
    print(f"   Payload: {payload}")
    
    try:
        # 3. Send the POST request
        response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=60)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # 4. Save the returned image data
        with open(OUTPUT_IMAGE_PATH, "wb") as f:
            f.write(response.content)
        
        print("\n3. Request successful!")
        print(f"   Image saved successfully at: {os.path.abspath(OUTPUT_IMAGE_PATH)}")

    except requests.exceptions.RequestException as e:
        print(f"   An error occurred during the API call: {e}")
        if e.response:
            print(f"   Response from server: {e.response.text}")

    print("\n--- API Test Finished ---")

if __name__ == "__main__":
    # Before running, make sure the main server is running:
    # python app.py
    test_generate_api()