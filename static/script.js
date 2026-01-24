document.addEventListener('DOMContentLoaded', () => {
    // UI 요소 가져오기
    const modelSelect = document.getElementById('model-select');
    const loraSelect = document.getElementById('lora-select');
    const loraScaleSlider = document.getElementById('lora-scale');
    const loraScaleValue = document.getElementById('lora-scale-value');
    const promptInput = document.getElementById('prompt');
    const generateBtn = document.getElementById('generate-btn');
    const resultImage = document.getElementById('result-image');
    const imageContainer = document.getElementById('image-container');
    const status = document.getElementById('status');
    const loadingOverlay = document.getElementById('loading-overlay');
    const errorMessage = document.getElementById('error-message');
    const galleryGrid = document.getElementById('gallery-grid');
    const resolutionSelect = document.getElementById('resolution-select');
    const imageInfoContainer = document.getElementById('image-info-container');
    const imageInfoPrompt = document.getElementById('image-info-prompt');
    const imageInfoSeed = document.getElementById('image-info-seed');
    const imageInfoSteps = document.getElementById('image-info-steps');
    const imageInfoGuidance = document.getElementById('image-info-guidance');
    const stepsSlider = document.getElementById('steps');
    const stepsValue = document.getElementById('steps-value');
    const guidanceScaleSlider = document.getElementById('guidance-scale');
    const guidanceScaleValue = document.getElementById('guidance-scale-value');
    const seedInput = document.getElementById('seed');
    const randomizeSeedBtn = document.getElementById('randomize-seed');
    const downloadBtn = document.getElementById('download-btn');
    const toggleBtn = document.querySelector('.toggle-btn');
    const controlPanel = document.querySelector('.control-panel');

    // 모델 및 LoRA 목록 로드 함수
    async function initialize() {
        generateBtn.disabled = true;
        try {
            // 모델 목록 가져오기
            const modelsRes = await fetch('/api/models');
            if (!modelsRes.ok) throw new Error('Failed to load models');
            const modelsData = await modelsRes.json();
            modelSelect.innerHTML = modelsData.models.map(m => `<option value="${m}">${m}</option>`).join('');

            // LoRA 목록 가져오기
            const lorasRes = await fetch('/api/loras');
            if (!lorasRes.ok) throw new Error('Failed to load LoRAs');
            const lorasData = await lorasRes.json();
            loraSelect.innerHTML = lorasData.loras.map(l => `<option value="${l}">${l}</option>`).join('');

        } catch (error) {
            errorMessage.textContent = `Error: ${error.message}`;
            console.error(error);
        } finally {
            generateBtn.disabled = false;
        }
    }

    // 이미지 생성 함수
    async function generateImage() {
        if (!promptInput.value.trim()) {
            alert('Please enter a prompt.');
            return;
        }

        errorMessage.textContent = ''; // 이전 오류 메시지 초기화
        errorMessage.style.display = 'none'; // 이전 오류 메시지 숨기기
        generateBtn.disabled = true;
        status.textContent = 'Generating... this may take a moment.';
        resultImage.style.display = 'none';
        downloadBtn.style.display = 'none';
        imageInfoContainer.style.display = 'none';
        loadingOverlay.style.display = 'flex'; // 로딩 오버레이 표시

        const [width, height] = resolutionSelect.value.split('x').map(Number);
        
        const payload = {
            model_name: modelSelect.value,
            lora_name: loraSelect.value,
            lora_scale: parseFloat(loraScaleSlider.value),
            prompt: promptInput.value,
            width: width,
            height: height,
            seed: parseInt(seedInput.value, 10),
            steps: parseInt(stepsSlider.value, 10),
            guidance_scale: parseFloat(guidanceScaleSlider.value),
        };

        console.log('Sending payload:', payload);

        try {
            let progress = 0;
            const progressBar = document.getElementById('progress-bar');
            progressBar.style.width = '0%';
            const interval = setInterval(() => {
                progress += 1;
                progressBar.style.width = `${progress}%`;
                if (progress >= 100) {
                    clearInterval(interval);
                }
            }, 100); // 10 seconds simulation

            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'image/png'
                },
                body: JSON.stringify(payload)
            });

            clearInterval(interval);
            progressBar.style.width = '100%';

            if (!response.ok) {
                let errorMessageText = `HTTP Error: ${response.status} ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMessageText += `\n\nDetails: ${errorData.detail}`;
                    }
                } catch (jsonError) {
                    try {
                        const rawText = await response.text();
                        if (rawText) {
                            errorMessageText += `\n\nServer response: ${rawText}`;
                        }
                    } catch (textError) {
                        // Ignore if we can't even get text
                    }
                }
                throw new Error(errorMessageText);
            }

            const imageBlob = await response.blob();
            const imageUrl = URL.createObjectURL(imageBlob);
            
            resultImage.src = imageUrl;
            resultImage.style.display = 'block';
            downloadBtn.style.display = 'block';
            status.textContent = 'Generation complete.';
            
            addOrUpdateGalleryItem(imageUrl, payload);

        } catch (error) {
            status.textContent = `Error: Please check below for details.`;
            errorMessage.textContent = `Error: ${error.message}`;
            errorMessage.style.display = 'block';
            console.error(error);
        } finally {
            generateBtn.disabled = false;
            loadingOverlay.style.display = 'none'; // 로딩 오버레이 숨기기
        }
    }
    
    function addOrUpdateGalleryItem(imageUrl, params) {
        const galleryItem = document.createElement('div');
        galleryItem.className = 'gallery-item';
        const img = document.createElement('img');
        img.src = imageUrl;
        galleryItem.appendChild(img);

        const downloadIcon = document.createElement('a');
        downloadIcon.href = imageUrl;
        downloadIcon.download = `generated_image_${Date.now()}.png`;
        downloadIcon.className = 'download-btn';
        downloadIcon.innerHTML = '<i class="fas fa-download"></i>';
        galleryItem.appendChild(downloadIcon);

        galleryItem.addEventListener('click', (e) => {
            if (e.target.tagName !== 'I' && e.target.tagName !== 'A') {
                resultImage.src = imageUrl;
                resultImage.style.display = 'block';
                downloadBtn.style.display = 'block';
                imageInfoPrompt.textContent = `Prompt: ${params.prompt}`;
                imageInfoSeed.textContent = `Seed: ${params.seed}`;
                imageInfoSteps.textContent = `Steps: ${params.steps}`;
                imageInfoGuidance.textContent = `Guidance Scale: ${params.guidance_scale}`;
                imageInfoContainer.style.display = 'block';
            }
        });

        // Add to the beginning of the grid
        galleryGrid.insertBefore(galleryItem, galleryGrid.firstChild);
    }

    // Event Listeners
    loraScaleSlider.addEventListener('input', () => {
        loraScaleValue.textContent = loraScaleSlider.value;
    });

    stepsSlider.addEventListener('input', () => {
        stepsValue.textContent = stepsSlider.value;
    });

    guidanceScaleSlider.addEventListener('input', () => {
        guidanceScaleValue.textContent = guidanceScaleSlider.value;
    });

    randomizeSeedBtn.addEventListener('click', () => {
        seedInput.value = Math.floor(Math.random() * 1000000);
    });

    downloadBtn.addEventListener('click', () => {
        const link = document.createElement('a');
        link.href = resultImage.src;
        link.download = `generated_image_${Date.now()}.png`;
        link.click();
    });

    toggleBtn.addEventListener('click', () => {
        controlPanel.classList.toggle('collapsed');
        toggleBtn.querySelector('i').classList.toggle('fa-chevron-left');
        toggleBtn.querySelector('i').classList.toggle('fa-chevron-right');
    });

    generateBtn.addEventListener('click', generateImage);

    // 초기화 함수 실행
    initialize();
});
