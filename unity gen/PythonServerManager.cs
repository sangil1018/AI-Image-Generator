using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using Newtonsoft.Json;

public class PythonServerManager : MonoBehaviour
{
    [Header("Server Configuration")]
    [Tooltip("The absolute path to the Python project's root folder. E.g., C:\\AI\\Z-Image-Turbo")]
    public string executionDirectory = @"C:\AI\Z-Image-Turbo";
    [Tooltip("The base URL of the Python server. Default: http://127.0.0.1:8888")]
    public string serverBaseUrl = "http://127.0.0.1:8888";
    [Tooltip("URL to open for downloading LoRAs. Default: https://huggingface.co/models?other=base_model:adapter:Tongyi-MAI/Z-Image-Turbo")]
    public string loraDownloadUrl = "https://huggingface.co/models?other=base_model:adapter:Tongyi-MAI/Z-Image-Turbo";

    [Header("UI References")]
    [Tooltip("The Dropdown for model selection")]
    public TMP_Dropdown modelDropdown;
    [Tooltip("The Dropdown for LoRA selection")]
    public TMP_Dropdown loraDropdown;
    [Tooltip("The Slider for controlling LoRA weight")]
    public Slider loraScaleSlider;
    [Tooltip("A TextMeshProUGUI element to display the current LoRA Scale value.")]
    public TextMeshProUGUI loraScaleValueText;
    [Tooltip("The InputField where the user types the prompt")]
    public TMP_InputField promptInputField;
    [Tooltip("The RawImage used to display the generated image")]
    public RawImage targetImageDisplay;
    [Tooltip("A Text element to show status messages")]
    public TextMeshProUGUI statusText;
    [Tooltip("An Image element to show a status icon (e.g., checkmark, loading spinner)")]
    public Image statusIcon;

    [Header("Generation Settings")]
    [Tooltip("The negative prompt to guide the image generation.")]
    public string negativePrompt = "blurry, low quality, deformed, ugly";
    [Tooltip("The number of inference steps.")]
    [Range(1, 50)]
    public int steps = 8;
    [Tooltip("The guidance scale, typically 0.0 for Turbo models.")]
    [Range(0f, 10f)]
    public float guidanceScale = 0.0f;
    [Tooltip("The width of the generated image.")]
    public int width = 1024;
    [Tooltip("The height of the generated image.")]
    public int height = 1024;
    [Tooltip("The seed for randomization. Use -1 for a random seed.")]
    public int seed = -1;


    private Process pythonServerProcess;
    private static readonly HttpClient client = new();
    private bool serverIsReady = false;

    private void Start()
    {
        // Set a longer timeout for the static HttpClient to prevent TaskCanceledException
        client.Timeout = TimeSpan.FromSeconds(120);
        StartCoroutine(StartServerAndFetchData());
    }

    void OnApplicationQuit()
    {
        StopPythonServer();
    }

    private IEnumerator StartServerAndFetchData()
    {
        // 먼저 서버가 이미 실행 중인지 확인합니다.
        var checkTask = CheckServerStatus();
        yield return new WaitUntil(() => checkTask.IsCompleted);

        if (checkTask.Result)
        {
            UnityEngine.Debug.Log("기존 Python 서버가 감지되었습니다. 연결을 시도합니다.");
            serverIsReady = true;
        }
        else
        {
            UnityEngine.Debug.Log("실행 중인 Python 서버가 없습니다. 새로 시작합니다.");
            StartPythonServer();

            if (pythonServerProcess == null)
            {
                yield break;
            }

            if (statusText) statusText.text = "서버 초기화를 기다리는 중...";
            yield return new WaitForSeconds(15);
            serverIsReady = true;
        }

        if (statusText) statusText.text = "서버 준비 완료. 데이터 가져오는 중...";
        yield return StartCoroutine(UpdateDropdownsCoroutine());
    }

    private async Task<bool> CheckServerStatus()
    {
        try
        {
            // 간단한 GET 요청으로 서버 상태 확인 (타임아웃 짧게 설정)
            using (var cts = new System.Threading.CancellationTokenSource(TimeSpan.FromSeconds(2)))
            {
                var response = await client.GetAsync(serverBaseUrl, cts.Token);
                return response.IsSuccessStatusCode;
            }
        }
        catch
        {
            return false;
        }
    }

    public void StartPythonServer()
    {
        if (pythonServerProcess != null && !pythonServerProcess.HasExited)
        {
            UnityEngine.Debug.Log("Python 서버가 이미 실행 중입니다.");
            return;
        }

        if (string.IsNullOrEmpty(executionDirectory) || !Directory.Exists(executionDirectory))
        {
            UnityEngine.Debug.LogError("실행 디렉토리가 설정되지 않았거나 존재하지 않습니다!");
            if (statusText) statusText.text = "오류: 실행 디렉토리가 설정되지 않았습니다.";
            pythonServerProcess = null;
            return;
        }

        var executablePath = Path.Combine(executionDirectory, "Z-Image-Turbo.exe");
        var batchPath = Path.Combine(executionDirectory, "run.bat");

        string fileToRun;
        if (File.Exists(executablePath))
        {
            fileToRun = executablePath;
        }
        else if (File.Exists(batchPath))
        {
            fileToRun = batchPath;
        }
        else
        {
            UnityEngine.Debug.LogError("지정된 디렉토리에서 'Z-Image-Turbo.exe' 또는 'run.bat'을 찾을 수 없습니다.");
            if (statusText) statusText.text = "오류: 실행 파일을 찾을 수 없습니다.";
            pythonServerProcess = null;
            return;
        }

        var startInfo = new ProcessStartInfo
        {
            FileName = fileToRun,
            WorkingDirectory = executionDirectory,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };

        pythonServerProcess = new Process { StartInfo = startInfo };
        pythonServerProcess.OutputDataReceived += (sender, args) => UnityEngine.Debug.Log($"[PyServer]: {args.Data}");
        pythonServerProcess.ErrorDataReceived += (sender, args) => UnityEngine.Debug.LogWarning($"[PyServer ERR]: {args.Data}");

        try
        {
            pythonServerProcess.Start();
            pythonServerProcess.BeginOutputReadLine();
            pythonServerProcess.BeginErrorReadLine();
            UnityEngine.Debug.Log($"Python 서버 프로세스 시작됨, PID: {pythonServerProcess.Id}");
            if (statusText) statusText.text = "서버 시작 중...";
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"Python 서버 시작 실패: {e.Message}");
            if (statusText) statusText.text = "오류: 서버 시작 실패.";
            pythonServerProcess = null;
        }
    }

    private async Task PopulateDropdown(TMP_Dropdown dropdown, string url, string listKey, string errorMsg)
    {
        if (dropdown == null) return;

        try
        {
            var response = await client.GetAsync(url);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();

            if (listKey == "models")
            {
                var list = JsonConvert.DeserializeObject<ModelListResponse>(json).models;
                dropdown.ClearOptions();
                dropdown.AddOptions(list);
            }
            else if (listKey == "loras")
            {
                var list = JsonConvert.DeserializeObject<LoraListResponse>(json).loras;
                dropdown.ClearOptions();
                dropdown.AddOptions(list);
            }
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"{errorMsg}: {e.Message}");
            if (statusText) statusText.text = errorMsg;
        }
    }

    private IEnumerator UpdateDropdownsCoroutine()
    {
        var modelsTask = PopulateDropdown(modelDropdown, $"{serverBaseUrl}/api/models", "models", "오류: 모델을 가져올 수 없습니다.");
        while (!modelsTask.IsCompleted) yield return null;

        var lorasTask = PopulateDropdown(loraDropdown, $"{serverBaseUrl}/api/loras", "loras", "오류: LoRA를 가져올 수 없습니다.");
        while (!lorasTask.IsCompleted) yield return null;

        if (statusText) statusText.text = "생성 준비 완료.";
    }

    public async void StopPythonServer()
    {
        // First, attempt a graceful shutdown via the API.
        // This works for both externally and internally started servers.
        UnityEngine.Debug.Log("Python 서버에 정상 종료를 요청합니다...");
        try
        {
            using (var cts = new System.Threading.CancellationTokenSource(TimeSpan.FromSeconds(3)))
            {
                await client.PostAsync($"{serverBaseUrl}/shutdown", null, cts.Token);
                UnityEngine.Debug.Log("정상 종료 요청 성공. 서버가 종료될 때까지 잠시 기다립니다...");
                await Task.Delay(2000); // Give server time to shut down.
            }
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogWarning($"정상 종료 요청 실패: {e.Message}. 강제 종료를 시도합니다.");
        }

        // As a final measure, if this script started a process, ensure it's terminated.
        if (pythonServerProcess != null && !pythonServerProcess.HasExited)
        {
            UnityEngine.Debug.Log("내부에서 실행된 Python 프로세스를 강제 종료합니다.");
            try
            {
                pythonServerProcess.Kill();
                pythonServerProcess.WaitForExit(2000); // Wait for kill confirmation
            }
            catch (Exception killException)
            {
                UnityEngine.Debug.LogError($"프로세스 강제 종료 중 오류 발생: {killException.Message}");
            }
            finally
            {
                pythonServerProcess.Close();
                pythonServerProcess = null;
            }
        }
        else
        {
            UnityEngine.Debug.Log("내부에서 실행된 프로세스가 없거나 이미 종료되었습니다.");
        }
        serverIsReady = false;
    }

    public void RequestImageGeneration()
    {
        if (!serverIsReady)
        {
            if (statusText) statusText.text = "서버가 아직 준비되지 않았습니다.";
            return;
        }
        if (promptInputField == null || string.IsNullOrEmpty(promptInputField.text))
        {
            if (statusText) statusText.text = "오류: 프롬프트는 비어있을 수 없습니다.";
            return;
        }

        StartCoroutine(GenerateImageCoroutine());
    }

    /// <summary>
    /// Opens the specified LoRA download URL in the default web browser.
    /// </summary>
    public void OpenLoraDownloadPage()
    {
        Application.OpenURL(loraDownloadUrl);
    }

    private IEnumerator GenerateImageCoroutine()
    {
        // 1. UI 업데이트 (메인 스레드)
        if (statusText) statusText.text = "이미지 생성 중...";
        if (statusIcon) statusIcon.color = Color.yellow;

        // 2. 비동기 작업 시작
        var imageTask = GenerateImageTaskAsync();

        // 3. 작업이 완료될 때까지 메인 스레드를 차단하지 않고 기다립니다.
        yield return new WaitUntil(() => imageTask.IsCompleted);

        // 4. 작업 결과 처리 (메인 스레드)
        if (imageTask.IsFaulted)
        {
            UnityEngine.Debug.LogError($"이미지 생성 실패: {imageTask.Exception}");
            if (statusText) statusText.text = "오류: 생성 실패.";
            if (statusIcon) statusIcon.color = Color.red;
        }
        else
        {
            var imageBytes = imageTask.Result;
            if (imageBytes != null && imageBytes.Length > 0)
            {
                // 생성된 이미지를 파일로 저장
                try
                {
                    string directoryPath = Path.Combine(executionDirectory, "output");
                    Directory.CreateDirectory(directoryPath); // 폴더가 없으면 생성
                    string fileName = $"generated_image_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}.png";
                    string filePath = Path.Combine(directoryPath, fileName);
                    File.WriteAllBytes(filePath, imageBytes);
                    UnityEngine.Debug.Log($"이미지가 다음 경로에 저장되었습니다: {filePath}");
                }
                catch (Exception e)
                {
                    UnityEngine.Debug.LogError($"이미지 저장 실패: {e.Message}");
                }

                var tex = new Texture2D(2, 2);
                tex.LoadImage(imageBytes);
                if (targetImageDisplay != null)
                {
                    targetImageDisplay.texture = tex;
                    targetImageDisplay.color = Color.white;
                }

                if (statusText) statusText.text = "이미지 생성 성공!";
                if (statusIcon) statusIcon.color = Color.green;
            }
            else
            {
                if (statusText) statusText.text = "오류: 서버로부터 빈 이미지를 받았습니다.";
                if (statusIcon) statusIcon.color = Color.red;
            }
        }

        // 5. 잠시 후 UI를 다시 '준비' 상태로 리셋
        yield return new WaitForSeconds(5);
        if (statusText) statusText.text = "생성 준비 완료.";
        if (statusIcon) statusIcon.color = new Color(1, 1, 1, 0); // 아이콘 숨기기
    }

    private async Task<byte[]> GenerateImageTaskAsync()
    {
        var modelName = modelDropdown.options[modelDropdown.value].text;
        var loraName = loraDropdown.options[loraDropdown.value].text;
        var loraScale = loraScaleSlider.value;
        var prompt = promptInputField.text;

        var payload = new
        {
            model_name = modelName,
            lora_name = loraName,
            lora_scale = loraScale,
            prompt = prompt,
            negative_prompt = negativePrompt,
            steps = this.steps,
            guidance_scale = guidanceScale,
            width = this.width,
            height = this.height,
            seed = this.seed
        };

        var jsonPayload = JsonConvert.SerializeObject(payload);

        using (var requestMessage = new HttpRequestMessage(HttpMethod.Post, $"{serverBaseUrl}/api/generate"))
        {
            requestMessage.Content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");
            // Force the connection to close after this request. This mimics the behavior of python's requests library
            // and can solve issues where the server (uvicorn) has problems with keep-alive connections.
            requestMessage.Headers.ConnectionClose = true;

            try
            {
                var response = await client.SendAsync(requestMessage);
                response.EnsureSuccessStatusCode();

                var imageBytes = await response.Content.ReadAsByteArrayAsync();
                return imageBytes;
            }
            catch (Exception)
            {
                throw;
            }
        }
    }

    [Serializable] private class ModelListResponse { public List<string> models; }
    [Serializable] private class LoraListResponse { public List<string> loras; }
}