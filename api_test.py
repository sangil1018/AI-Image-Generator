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

def get_model_type(model_name):
    """모델 이름에서 아키텍처 타입을 식별합니다."""
    model_name_lower = model_name.lower()
    if 'flux' in model_name_lower:
        return 'flux'
    elif 'qwen' in model_name_lower:
        return 'qwen'
    return 'sd' # 기본값

def get_prompt_and_guidance(model_type):
    """모델 타입에 맞는 기본 프롬프트와 작성 가이드를 반환합니다."""
    if model_type == 'flux':
        print("\n--- FLUX 모델 프롬프트 가이드 ---")
        print("FLUX 모델은 일반적인 SD 모델과 달리, 복잡하고 서술적인 문장을 잘 이해합니다.")
        print("단순한 키워드 나열보다 완전한 문장으로 묘사하는 것이 좋습니다.")
        print("Negative Prompt와 LoRA는 사용되지 않습니다.")
        return "A cinematic shot of a an old man sitting on a mountainside, daytime, breathtaking, 8k"
    elif model_type == 'qwen':
        print("\n--- Qwen-Image 모델 프롬프트 가이드 ---")
        print("Qwen 모델은 지시사항(Instruction) 형식의 프롬프트를 사용합니다.")
        print("만들고 싶은 이미지를 명확하고 구체적으로 서술하세요. 중국어/영어를 잘 이해합니다.")
        print("Negative Prompt와 LoRA는 사용되지 않습니다.")
        return "A wolf howling at the moon in a dark forest, highly detailed, photorealistic."
    else: # sd
        print("\n--- Stable Diffusion 모델 프롬프트 가이드 ---")
        print("키워드 기반 프롬프트에 가장 잘 반응합니다. 쉼표(,)로 키워드를 구분하여 퀄리티, 스타일, 피사체, 배경 등을 묘사하세요.")
        print("Negative Prompt와 LoRA 사용이 가능합니다.")
        return "a korean girl, solo, whole body with long boots, dynamic pose, beautiful detailed eyes, cinematic lighting, masterpiece, ultra-detailed, 8k"

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
    model_type = get_model_type(selected_model)
    print(f"   > 선택된 모델: {selected_model} (타입: {model_type.upper()})")

    # 2. 프롬프트 및 파라미터 입력
    base_prompt = get_prompt_and_guidance(model_type)
    prompt_input = input(f"   > 프롬프트를 입력하세요 (기본값: '{base_prompt}'): ").strip()
    final_prompt = prompt_input if prompt_input else base_prompt

    payload = {
        "model_name": selected_model,
        "prompt": final_prompt,
        "width": 1024,
        "height": 1024,
        "steps": 8,
        "seed": -1
    }

    # 3. 모델 타입별 파라미터 추가
    if model_type == 'sd':
        neg_prompt = input("   > Negative 프롬프트를 입력하세요 (기본값: 'blurry, low quality, deformed, ugly'): ").strip()
        payload['negative_prompt'] = neg_prompt if neg_prompt else "blurry, low quality, deformed, ugly"
        payload['guidance_scale'] = 0.0 # Turbo 모델 기본값
        
        # LoRA 선택
        loras = get_all_loras()
        if loras:
            lora_options = ["사용 안함"] + loras
            selected_lora = prompt_for_selection(lora_options, "LoRA 선택 (SD 모델 전용)")
            if selected_lora != "사용 안함":
                payload['lora_name'] = selected_lora
                
                lora_scale = 0.8
                scale_input = input(f"   > LoRA 스케일 값을 입력하세요 (기본값: {lora_scale}): ").strip()
                try:
                    payload['lora_scale'] = float(scale_input) if scale_input else lora_scale
                except ValueError:
                    payload['lora_scale'] = lora_scale

                trigger_input = input(f"   > '{selected_lora.replace('.safetensors', '')}' LoRA의 트리거 워드를 입력하세요 (선택 사항): ").strip()
                if trigger_input:
                    payload['prompt'] += f", {trigger_input}"
        else:
            print("\n사용 가능한 LoRA가 없습니다.")
    
    print("\n--- 이미지 생성 요청 ---")
    print("Payload:", json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        # 4. POST 요청 보내기
        response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=300) # 타임아웃 증가
        response.raise_for_status()

        # 5. 반환된 이미지 데이터 저장
        model_name_safe = selected_model.replace('/', '_').replace('\\', '_')
        lora_name_safe = payload.get('lora_name', 'None').replace('.safetensors', '')
        output_filename = f"output_{model_name_safe}_{lora_name_safe}.png"

        with open(output_filename, "wb") as f:
            f.write(response.content)
        
        print("\n--- 요청 성공! ---")
        print(f"이미지가 다음 경로에 성공적으로 저장되었습니다: {os.path.abspath(output_filename)}")

    except requests.exceptions.RequestException as e:
        print(f"\n--- API 호출 중 오류가 발생했습니다 ---")
        print(e)
        if hasattr(e, 'response') and e.response:
            print(f"서버 응답: {e.response.text}")

    print("\n--- 테스트 종료 ---")

if __name__ == "__main__":
    import json
    # 이 스크립트를 실행하기 전에 메인 서버가 실행 중인지 확인하세요:
    # python app.py
    run_generation_test()