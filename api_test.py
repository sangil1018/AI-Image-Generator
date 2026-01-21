# -*- coding: utf-8 -*-
import requests
import os

# --- 설정 ---
BASE_URL = "http://127.0.0.1:8888"
OUTPUT_IMAGE_PATH = "api_test_output.png"

def get_all_models():
    """API에서 사용 가능한 모든 모델 목록을 가져옵니다."""
    try:
        response = requests.get(f"{BASE_URL}/api/models", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        if models:
            return models
        else:
            print("경고: API에서 모델을 찾을 수 없습니다. 서버가 실행 중이고 'models' 폴더에 모델이 있는지 확인하세요.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"모델 목록 가져오기 오류: {e}")
        return []

def get_all_loras():
    """API에서 사용 가능한 모든 LoRA 목록을 가져옵니다."""
    try:
        response = requests.get(f"{BASE_URL}/api/loras", timeout=5)
        response.raise_for_status()
        loras = response.json().get("loras", [])
        # 항상 첫 번째 요소인 "None"을 제외
        return [lora for lora in loras if lora != "None"]
    except requests.exceptions.RequestException as e:
        print(f"LoRA 목록 가져오기 오류: {e}")
        return []

def prompt_for_selection(item_list, title):
    """사용자에게 목록을 보여주고 항목을 선택하도록 요청합니다."""
    print(f"\n--- {title} ---")
    for i, item in enumerate(item_list):
        print(f"{i + 1}. {item}")
    
    while True:
        try:
            choice = int(input(f"_선택 (1-{len(item_list)}): ").strip())
            if 1 <= choice <= len(item_list):
                return item_list[choice - 1]
            else:
                print(f"잘못된 선택입니다. 1에서 {len(item_list)} 사이의 숫자를 입력하세요.")
        except ValueError:
            print("잘못된 입력입니다. 숫자를 입력하세요.")

def run_generation_test():
    """
    사용자 선택에 기반하여 이미지 생성을 테스트하는 전체 프로세스를 실행합니다.
    """
    # 1. 모델 선택
    models = get_all_models()
    if not models:
        print("사용 가능한 모델이 없어 테스트를 진행할 수 없습니다.")
        return
    
    selected_model = prompt_for_selection(models, "모델 선택")
    print(f"   > 선택된 모델: {selected_model}")

    # 2. LoRA 선택
    loras = get_all_loras()
    selected_lora = "사용 안함"
    lora_scale = 0.8 # 기본값

    if loras:
        lora_options = ["사용 안함"] + loras
        selected_lora = prompt_for_selection(lora_options, "LoRA 선택")
    else:
        print("\n사용 가능한 LoRA가 없습니다.")

    if selected_lora == "사용 안함":
        print("   > LoRA를 사용하지 않습니다.")
        lora_name = "None"
    else:
        print(f"   > 선택된 LoRA: {selected_lora}")
        lora_name = selected_lora
        # LoRA 스케일 입력 받기
        while True:
            try:
                scale_input = input(f"   > LoRA 스케일 값을 입력하세요 (0.0 ~ 1.0, 기본값: {lora_scale}): ").strip()
                if not scale_input:
                    break # 기본값 사용
                lora_scale = float(scale_input)
                if 0.0 <= lora_scale <= 2.0: # 스케일 범위는 조금 넉넉하게
                    break
                else:
                    print("   > 잘못된 범위입니다. 0.0에서 2.0 사이의 값을 입력하세요.")
            except ValueError:
                print("   > 잘못된 입력입니다. 숫자를 입력하세요.")
    
    # 3. 페이로드 정의
    base_prompt = "a korean girl, solo, whole body with long boots, dynamic pose, beautiful detailed eyes, cinematic lighting, masterpiece, ultra-detailed, 8k, photorealistic, golden hour lighting"
    lora_trigger_word = ""

    if lora_name != "None":
        trigger_input = input(f"   > '{lora_name.replace('.safetensors', '')}' LoRA의 트리거 워드를 입력하세요 (선택 사항): ").strip()
        if trigger_input:
            lora_trigger_word = trigger_input
            print(f"   > LoRA 트리거 워드: {lora_trigger_word}")
        else:
            print("   > LoRA 트리거 워드를 입력하지 않았습니다.")

    # 최종 프롬프트 구성
    final_prompt = base_prompt
    if lora_trigger_word:
        final_prompt += f", {lora_trigger_word}"

    payload = {
        "model_name": selected_model,
        "lora_name": lora_name,
        "lora_scale": lora_scale,
        "prompt": final_prompt, # 최종 프롬프트를 사용
        "negative_prompt": "blurry, low quality, deformed, ugly, worst quality, low quality, normal quality",
        "steps": 8,
        "width": 1024,
        "height": 1024,
        "seed": -1
    }
    
    print("\n--- 이미지 생성 요청 ---")
    print(f"Payload: {payload}")
    
    try:
        # 4. POST 요청 보내기
        response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=120)
        response.raise_for_status()

        # 5. 반환된 이미지 데이터 저장
        output_filename = f"output_{selected_model.replace('/', '_')}_{lora_name.replace('.safetensors', '')}.png"
        with open(output_filename, "wb") as f:
            f.write(response.content)
        
        print("\n--- 요청 성공! ---")
        print(f"이미지가 다음 경로에 성공적으로 저장되었습니다: {os.path.abspath(output_filename)}")

    except requests.exceptions.RequestException as e:
        print(f"\n--- API 호출 중 오류가 발생했습니다 ---")
        print(e)
        if e.response:
            print(f"서버 응답: {e.response.text}")

    print("\n--- 테스트 종료 ---")

if __name__ == "__main__":
    # 이 스크립트를 실행하기 전에 메인 서버가 실행 중인지 확인하세요:
    # python app.py
    run_generation_test()