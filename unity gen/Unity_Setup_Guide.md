# Unity 프로젝트 설정 가이드 (v2.1 - 상세 설정 추가)

이 가이드는 유니티에서 파이썬 이미지 생성 서버를 제어하고 연동하는 데 필요한 단계별 설정을 안내합니다. `UIGenerator` 스크립트를 통해 UI 구성이 자동화되었습니다.

## 1단계: 스크립트 복사

아래의 두 .cs 파일을 당신의 Unity 프로젝트 폴더로 복사합니다.

1.  **`PythonServerManager.cs`**: `Assets/Scripts`와 같이 스크립트를 관리하는 폴더에 복사하세요.
2.  **`UIGenerator.cs`**: 반드시 `Assets/Editor` 폴더에 복사해야 합니다. (`Editor` 폴더가 없다면 새로 만드세요.)

## 2단계: `Newtonsoft.Json` 패키지 설치

파이썬 서버와 JSON 통신을 위해 `Newtonsoft.Json` 라이브러리가 필요합니다.

*   Unity 에디터 상단 메뉴에서 `Window` > `Package Manager`를 엽니다.
*   패키지 관리자 창 왼쪽 상단에 있는 `+` 버튼을 클릭한 후, `Add package from git URL...`을 선택합니다.
*   입력 필드에 `com.unity.newtonsoft-json`을 입력하고 `Add` 버튼을 클릭하여 설치합니다.

## 3단계: `PythonManager` 오브젝트 설정

1.  Unity 씬(Scene)에서 비어있는 게임 오브젝트를 생성합니다. (예: 마우스 우클릭 > `Create Empty`, 이름을 "PythonManager"로 지정)
2.  생성한 "PythonManager" 게임 오브젝트를 선택한 후, `Add Component` 버튼을 클릭하여 `PythonServerManager` 스크립트를 연결합니다.
3.  인스펙터(Inspector) 창에서 `Python Server Manager` 컴포넌트의 필드들을 다음과 같이 설정합니다.

    *   **`Execution Directory` (실행 디렉토리):**
        *   파이썬 프로젝트의 **절대 경로**를 입력합니다. (예: `D:\AI\AI-Image-Generator`)
    *   **`Server Base Url` (서버 기본 URL):**
        *   기본값인 `http://127.0.0.1:8888`을 유지합니다.
    *   **`Lora Download Url` (LoRA 다운로드 URL):**
        *   필요에 따라 LoRA 다운로드 주소를 변경할 수 있습니다.

4.  **추가 생성 옵션 설정 (Generation Settings)**
    *   컴포넌트 인스펙터의 **`Generation Settings`** 섹션에서 이미지 생성에 대한 상세 옵션을 조정할 수 있습니다. 이 설정들은 UI에 별도의 컨트롤러가 없으며, 여기서 설정된 값이 생성 시 기본값으로 사용됩니다.
    *   **`Negative Prompt`**: 생성하고 싶지 않은 요소(예: `blurry, low quality`)를 입력합니다.
    *   **`Steps`**: 이미지 생성 단계 수입니다. (기본값: 8)
    *   **`Guidance Scale`**: 프롬프트 충실도입니다. (Turbo 모델의 경우 0.0 권장)
    *   **`Width` / `Height`**: 생성될 이미지의 너비와 높이입니다.
    *   **`Seed`**: 이미지 생성 시드값입니다. `-1`로 설정 시 랜덤 시드가 사용됩니다.

## 4단계: UI 자동 생성

*   Unity 에디터 상단 메뉴에서 `GameObject > AI Image UI > Generate UI`를 클릭합니다.

이 한 번의 클릭으로 씬에 필요한 모든 UI(패널, 드롭다운, 버튼 등)가 자동으로 생성되고, `PythonManager`의 필드에 모두 연결됩니다.

생성된 이미지는 다음과 같이 UI에 표시됩니다.

![Generated AI Image](Gemini_Generated_Image.png)

---

### **사용 방법**

1.  **파이썬 서버 빌드 (필요 시):**
    *   Python 서버 코드에 변경사항이 있다면, `build_exe.bat` 파일을 실행하여 `.exe` 파일을 다시 빌드해야 합니다.
2.  **Unity 실행:**
    *   Unity 에디터에서 'Play' 버튼을 누르면 `PythonServerManager`가 백그라운드에서 Python 서버를 자동으로 시작합니다.
    *   서버가 준비되면 모델과 LoRA 목록이 UI에 자동으로 표시됩니다.
    *   프롬프트를 입력하고 'Generate Image' 버튼을 클릭하면 이미지가 생성됩니다.

### **참고: TextMeshPro**
자동 생성된 UI는 Unity의 표준 텍스트 시스템인 TextMeshPro를 사용합니다. 프로젝트에 TextMeshPro가 처음 추가될 때 나타나는 "TMP Importer" 팝업창에서 **"Import TMP Essentials"** 버튼을 클릭하여 필수 리소스를 임포트해야 합니다.
