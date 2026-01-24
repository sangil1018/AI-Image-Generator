using UnityEngine;
using UnityEditor;
using UnityEngine.UI;
using TMPro;

public class UIGenerator
{
    private static Color panelBackgroundColor = new Color(0.95f, 0.95f, 0.98f, 1f);
    private static Color elementBackgroundColor = new Color(0.88f, 0.9f, 0.98f, 1f);
    private static Color primaryColor = new Color(0.3f, 0.3f, 0.8f, 1f);
    private static Color textColor = new Color(0.1f, 0.1f, 0.1f, 1f);
    private static int mainSpacing = 20;
    private static int elementSpacing = 15;
    private static int panelPadding = 25;
    private static int fontSize = 16;
    private static int titleFontSize = 24;

    [MenuItem("GameObject/AI Image UI/Generate UI")]
    public static void GenerateUI()
    {
        Canvas canvas = Object.FindObjectOfType<Canvas>();
        if (canvas == null)
        {
            GameObject canvasGO = new GameObject("UICanvas");
            canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvasGO.AddComponent<CanvasScaler>();
            canvasGO.AddComponent<GraphicRaycaster>();
        }

        GameObject mainContainer = CreateUIObject("MainContainer", canvas.transform);
        HorizontalLayoutGroup mainLayout = mainContainer.AddComponent<HorizontalLayoutGroup>();
        mainLayout.spacing = mainSpacing;
        mainLayout.padding = new RectOffset(mainSpacing, mainSpacing, mainSpacing, mainSpacing);
        mainLayout.childControlWidth = true;
        mainLayout.childControlHeight = true;
        mainLayout.childForceExpandWidth = true;
        mainLayout.childForceExpandHeight = true;
        SetAnchorsAndPivots(mainContainer.GetComponent<RectTransform>(), AnchorPresets.StretchAll);

        GameObject controlPanel = CreatePanel("Control Panel", mainContainer.transform);
        VerticalLayoutGroup controlPanelLayout = controlPanel.AddComponent<VerticalLayoutGroup>();
        controlPanelLayout.spacing = elementSpacing;
        controlPanelLayout.padding = new RectOffset(panelPadding, panelPadding, panelPadding, panelPadding);
        controlPanelLayout.childControlWidth = true;
        controlPanelLayout.childControlHeight = false;
        controlPanelLayout.childForceExpandWidth = true;
        controlPanelLayout.childForceExpandHeight = false;

        GameObject outputPanel = CreatePanel("Output", mainContainer.transform);
        VerticalLayoutGroup outputPanelLayout = outputPanel.AddComponent<VerticalLayoutGroup>();
        outputPanelLayout.spacing = elementSpacing;
        outputPanelLayout.padding = new RectOffset(panelPadding, panelPadding, panelPadding, panelPadding);
        outputPanelLayout.childControlWidth = true;

        PythonServerManager manager = Object.FindObjectOfType<PythonServerManager>();
        if (manager == null)
        {
            Debug.LogError("장면에 PythonServerManager를 찾을 수 없습니다. 먼저 추가해주세요.");
        }

        CreateTitle(controlPanel.transform, "Control Panel");

        var modelDropdown = CreateDropdown(controlPanel.transform, "Model", "Select Model (e.g., Z-Image-Turbo)");

        // --- LoRA Controls Container ---
        GameObject loraControlsContainer = CreateUIObject("LoraControls", controlPanel.transform);
        loraControlsContainer.AddComponent<VerticalLayoutGroup>().spacing = elementSpacing;
        
        var loraDropdown = CreateDropdown(loraControlsContainer.transform, "LoRA", "Select LoRA (e.g., None)");
        var (loraSlider, loraValueText) = CreateSlider(loraControlsContainer.transform, "LoRA Scale", 0.5f, 0.8f, 0.7f);
        
        var promptInput = CreateInputField(controlPanel.transform, "Prompt", "Enter prompt here...");

        GameObject buttonContainer = CreateUIObject("ButtonContainer", controlPanel.transform);
        HorizontalLayoutGroup buttonLayout = buttonContainer.AddComponent<HorizontalLayoutGroup>();
        buttonLayout.spacing = elementSpacing;
        var generateButton = CreateButton(buttonContainer.transform, "Generate Image");
        var downloadButton = CreateButton(buttonContainer.transform, "Download LoRAs");

        LayoutElement promptLayout = promptInput.gameObject.AddComponent<LayoutElement>();
        promptLayout.minHeight = 100;

        CreateTitle(outputPanel.transform, "Output");

        var (rawImage, rawImageContainer) = CreateRawImage(outputPanel.transform);
        var (statusText, statusIcon, statusContainer) = CreateStatus(outputPanel.transform, "Status: Ready to generate. (Server connected)");

        LayoutElement imageLayoutElement = rawImageContainer.AddComponent<LayoutElement>();
        imageLayoutElement.flexibleHeight = 1;
        imageLayoutElement.minHeight = 100;

        if (manager != null)
        {
            manager.modelDropdown = modelDropdown;
            manager.loraControlsContainer = loraControlsContainer; // Assign the new container
            manager.loraDropdown = loraDropdown;
            manager.loraScaleSlider = loraSlider;
            manager.loraScaleValueText = loraValueText;
            manager.promptInputField = promptInput;
            manager.targetImageDisplay = rawImage;
            manager.statusText = statusText;
            manager.statusIcon = statusIcon;

            var genButton = generateButton.GetComponent<Button>();
            genButton.onClick.RemoveAllListeners();
            genButton.onClick.AddListener(manager.RequestImageGeneration);

            var dlButton = downloadButton.GetComponent<Button>();
            dlButton.onClick.RemoveAllListeners();
            dlButton.onClick.AddListener(manager.OpenLoraDownloadPage);

            Debug.Log("UI가 성공적으로 생성되고 PythonServerManager에 연결되었습니다.");
        }

        Selection.activeGameObject = canvas.gameObject;
    }

    private static GameObject CreateUIObject(string name, Transform parent)
    {
        GameObject go = new GameObject(name);
        go.AddComponent<RectTransform>();
        go.transform.SetParent(parent, false);
        return go;
    }

    private static void SetAnchorsAndPivots(RectTransform rect, AnchorPresets preset)
    {
        switch (preset)
        {
            case AnchorPresets.TopLeft:
                rect.anchorMin = new Vector2(0, 1); rect.anchorMax = new Vector2(0, 1); rect.pivot = new Vector2(0, 1);
                break;
            case AnchorPresets.TopCenter:
                rect.anchorMin = new Vector2(0.5f, 1); rect.anchorMax = new Vector2(0.5f, 1); rect.pivot = new Vector2(0.5f, 1);
                break;
            case AnchorPresets.StretchAll:
                rect.anchorMin = Vector2.zero; rect.anchorMax = Vector2.one; rect.pivot = new Vector2(0.5f, 0.5f);
                rect.offsetMin = Vector2.zero; rect.offsetMax = Vector2.zero;
                break;
        }
    }
    public enum AnchorPresets { TopLeft, TopCenter, StretchAll }

    private static GameObject CreatePanel(string name, Transform parent)
    {
        GameObject panel = CreateUIObject(name, parent);
        Image img = panel.AddComponent<Image>();
        img.color = panelBackgroundColor;
        return panel;
    }

    private static TextMeshProUGUI CreateTitle(Transform parent, string text)
    {
        TextMeshProUGUI title = CreateText(parent, text, titleFontSize, FontStyles.Bold);
        LayoutElement layout = title.gameObject.AddComponent<LayoutElement>();
        layout.minHeight = 40;
        return title;
    }

    private static TextMeshProUGUI CreateText(Transform parent, string text, int size, FontStyles style = FontStyles.Normal)
    {
        GameObject textGO = CreateUIObject("Text", parent);
        TextMeshProUGUI tmp = textGO.AddComponent<TextMeshProUGUI>();
        tmp.text = text;
        tmp.fontSize = size;
        tmp.fontStyle = style;
        tmp.color = textColor;
        tmp.alignment = TextAlignmentOptions.Left;
        return tmp;
    }

    private static TMP_Dropdown CreateDropdown(Transform parent, string label, string placeholder)
    {
        CreateText(parent, label, fontSize, FontStyles.Bold);

        GameObject dropdownGO = CreateUIObject("Dropdown", parent);
        dropdownGO.AddComponent<Image>().color = elementBackgroundColor;
        TMP_Dropdown dropdown = dropdownGO.AddComponent<TMP_Dropdown>();

        var placeholderText = CreateText(dropdownGO.transform, placeholder, fontSize);
        placeholderText.GetComponent<RectTransform>().anchorMin = Vector2.zero;
        placeholderText.GetComponent<RectTransform>().anchorMax = Vector2.one;
        placeholderText.GetComponent<RectTransform>().offsetMin = new Vector2(10, 0);
        placeholderText.GetComponent<RectTransform>().offsetMax = new Vector2(-30, 0);
        dropdown.placeholder = placeholderText;

        var labelText = CreateText(dropdownGO.transform, "", fontSize);
        labelText.GetComponent<RectTransform>().anchorMin = Vector2.zero;
        labelText.GetComponent<RectTransform>().anchorMax = Vector2.one;
        labelText.GetComponent<RectTransform>().offsetMin = new Vector2(10, 0);
        labelText.GetComponent<RectTransform>().offsetMax = new Vector2(-30, 0);
        dropdown.captionText = labelText;

        GameObject arrowGO = CreateUIObject("Arrow", dropdownGO.transform);
        Image arrowImage = arrowGO.AddComponent<Image>();
        arrowImage.color = textColor;
        RectTransform arrowRect = arrowGO.GetComponent<RectTransform>();
        arrowRect.anchorMin = new Vector2(1, 0.5f);
        arrowRect.anchorMax = new Vector2(1, 0.5f);
        arrowRect.pivot = new Vector2(1, 0.5f);
        arrowRect.sizeDelta = new Vector2(20, 20);
        arrowRect.anchoredPosition = new Vector2(-10, 0);

        dropdownGO.AddComponent<LayoutElement>().minHeight = 40;
        return dropdown;
    }

    private static (Slider, TextMeshProUGUI) CreateSlider(Transform parent, string label, float min, float max, float defaultValue)
    {
        CreateText(parent, label, fontSize, FontStyles.Bold);

        GameObject sliderContainer = CreateUIObject("SliderContainer", parent);
        HorizontalLayoutGroup layout = sliderContainer.AddComponent<HorizontalLayoutGroup>();
        layout.spacing = 10;
        layout.childControlWidth = true;
        layout.childControlHeight = true;

        GameObject sliderGO = CreateUIObject("Slider", sliderContainer.transform);
        Slider slider = sliderGO.AddComponent<Slider>();
        slider.minValue = min;
        slider.maxValue = max;
        slider.value = defaultValue;

        GameObject bg = CreateUIObject("Background", sliderGO.transform);
        Image bgImg = bg.AddComponent<Image>();
        bgImg.color = new Color(0.7f, 0.7f, 0.8f);
        RectTransform bgRect = bg.GetComponent<RectTransform>();
        bgRect.anchorMin = new Vector2(0, 0.25f);
        bgRect.anchorMax = new Vector2(1, 0.75f);
        bgRect.pivot = new Vector2(0.5f, 0.5f);
        slider.targetGraphic = bgImg;

        GameObject handleSlideArea = CreateUIObject("HandleSlideArea", sliderGO.transform);
        RectTransform handleAreaRect = handleSlideArea.GetComponent<RectTransform>();
        handleAreaRect.anchorMin = Vector2.zero;
        handleAreaRect.anchorMax = Vector2.one;
        handleAreaRect.offsetMin = new Vector2(10, 0);
        handleAreaRect.offsetMax = new Vector2(-10, 0);

        GameObject handleGO = CreateUIObject("Handle", handleSlideArea.transform);
        Image handleImg = handleGO.AddComponent<Image>();
        handleImg.color = primaryColor;
        RectTransform handleRect = handleGO.GetComponent<RectTransform>();
        handleRect.sizeDelta = new Vector2(20, 20);
        slider.handleRect = handleRect;

        TextMeshProUGUI valueText = CreateText(sliderContainer.transform, defaultValue.ToString("F1"), fontSize);
        valueText.alignment = TextAlignmentOptions.Right;

        LayoutElement sliderLayout = sliderGO.AddComponent<LayoutElement>();
        sliderLayout.flexibleWidth = 1;
        LayoutElement textLayout = valueText.gameObject.AddComponent<LayoutElement>();
        textLayout.minWidth = 50;

        slider.onValueChanged.AddListener((v) => valueText.text = v.ToString("F1"));

        sliderContainer.AddComponent<LayoutElement>().minHeight = 30;

        return (slider, valueText);
    }

    private static TMP_InputField CreateInputField(Transform parent, string label, string placeholder)
    {
        CreateText(parent, label, fontSize, FontStyles.Bold);

        GameObject inputGO = CreateUIObject("InputField", parent);
        inputGO.AddComponent<Image>().color = elementBackgroundColor;
        TMP_InputField inputField = inputGO.AddComponent<TMP_InputField>();

        var placeholderText = CreateText(inputGO.transform, placeholder, fontSize);
        placeholderText.color = new Color(0.5f, 0.5f, 0.5f);
        inputField.placeholder = placeholderText;

        var mainText = CreateText(inputGO.transform, "", fontSize);
        inputField.textComponent = mainText;

        inputField.lineType = TMP_InputField.LineType.MultiLineNewline;

        var textRect = mainText.GetComponent<RectTransform>();
        textRect.anchorMin = Vector2.zero;
        textRect.anchorMax = Vector2.one;
        textRect.offsetMin = new Vector2(10, 5);
        textRect.offsetMax = new Vector2(-10, -5);

        placeholderText.GetComponent<RectTransform>().anchorMin = Vector2.zero;
        placeholderText.GetComponent<RectTransform>().anchorMax = Vector2.one;
        placeholderText.GetComponent<RectTransform>().offsetMin = new Vector2(10, 5);
        placeholderText.GetComponent<RectTransform>().offsetMax = new Vector2(-10, -5);

        return inputField;
    }

    private static Button CreateButton(Transform parent, string text)
    {
        GameObject buttonGO = CreateUIObject(text.Replace(" ", ""), parent);
        Image buttonImage = buttonGO.AddComponent<Image>();
        buttonImage.color = primaryColor;
        Button button = buttonGO.AddComponent<Button>();

        TextMeshProUGUI buttonText = CreateText(buttonGO.transform, text, fontSize, FontStyles.Bold);
        buttonText.color = Color.white;
        buttonText.alignment = TextAlignmentOptions.Center;

        buttonGO.AddComponent<LayoutElement>().minHeight = 45;
        button.gameObject.AddComponent<LayoutElement>().flexibleWidth = 1;

        return button;
    }

    private static (RawImage, GameObject) CreateRawImage(Transform parent)
    {
        GameObject container = CreateUIObject("ImageContainer", parent);
        Image bg = container.AddComponent<Image>();
        bg.color = elementBackgroundColor;
        VerticalLayoutGroup layout = container.AddComponent<VerticalLayoutGroup>();
        layout.childAlignment = TextAnchor.MiddleCenter;
        layout.spacing = 10;

        GameObject rawImageGO = CreateUIObject("RawImageDisplay", container.transform);
        RawImage rawImage = rawImageGO.AddComponent<RawImage>();
        rawImage.color = new Color(1, 1, 1, 0);

        CreateText(container.transform, "Generated Image (RawImage)", fontSize);
        CreateText(container.transform, "Image will appear here", fontSize - 2);

        return (rawImage, container);
    }

    private static (TextMeshProUGUI, Image, GameObject) CreateStatus(Transform parent, string text)
    {
        GameObject container = CreateUIObject("StatusContainer", parent);
        container.AddComponent<Image>().color = elementBackgroundColor;
        HorizontalLayoutGroup layout = container.AddComponent<HorizontalLayoutGroup>();
        layout.padding = new RectOffset(10, 10, 5, 5);
        layout.spacing = 10;
        layout.childAlignment = TextAnchor.MiddleLeft;

        TextMeshProUGUI statusText = CreateText(container.transform, text, fontSize);
        statusText.gameObject.AddComponent<LayoutElement>().flexibleWidth = 1;

        GameObject iconGO = CreateUIObject("StatusIcon", container.transform);
        Image statusIcon = iconGO.AddComponent<Image>();
        statusIcon.color = Color.green;
        iconGO.AddComponent<LayoutElement>().minWidth = 20;
        iconGO.GetComponent<RectTransform>().sizeDelta = new Vector2(20, 20);

        container.AddComponent<LayoutElement>().minHeight = 40;

        return (statusText, statusIcon, container);
    }
}
