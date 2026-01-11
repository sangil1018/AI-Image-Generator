import gradio as gr
from model_handler import ModelHandler
import os

# Initialize the model handler
handler = ModelHandler()

# --- Custom CSS for Premium Glassmorphism & Animations ---
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');

body, .gradio-container {
    font_family: 'Outfit', sans-serif;
    background: #0f0c29;  /* fallback for old browsers */
    background: -webkit-linear-gradient(to right, #24243e, #302b63, #0f0c29);  /* Chrome 10-25, Safari 5.1-6 */
    background: linear-gradient(to right, #24243e, #302b63, #0f0c29); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
    color: #e0e0e0;
}

/* Glassmorphism Containers */
.glass-panel {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
}

/* Section Headers */
h1, h2, h3 {
    color: #ffffff;
    font-weight: 600;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

/* Inputs & Dropdowns */
.gradio-container input, .gradio-container textarea, .gradio-container select {
    background: rgba(0, 0, 0, 0.3) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
}

/* Buttons */
#generate-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    color: white;
    font-weight: 600;
    font-size: 1.1rem;
    padding: 12px 24px;
    border-radius: 12px;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
}

#generate-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(118, 75, 162, 0.6);
}

#generate-btn:active {
    transform: translateY(0);
}

/* Sliders */
input[type=range] {
    accent-color: #764ba2;
}
"""

# --- Custom Theme Definition (for base colors) ---
theme = gr.themes.Soft(
    primary_hue="violet",
    secondary_hue="slate",
    neutral_hue="slate",
).set(
    body_background_fill="#0f0c29",
    block_background_fill="rgba(255,255,255,0.03)",
    block_border_width="0px",
    input_background_fill="rgba(0,0,0,0.3)",
    button_primary_background_fill="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    button_primary_text_color="white",
)

def generate_image(model_name, prompt, negative_prompt, steps, guidance_scale, width, height, seed):
    try:
        # Load the model if it's not the current one
        # Use a status message return if possible, or just generate
        handler.load_model(model_name)
        
        # Generate image
        image = handler.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            steps=steps,
            guidance_scale=guidance_scale,
            width=width,
            height=height,
            seed=seed
        )
        return image
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- UI Layout ---
with gr.Blocks(theme=theme, css=custom_css, title="Z-Image-Turbo Premium") as demo:
    
    with gr.Row(elem_classes="glass-panel"):
        gr.Markdown(
            """
            # ⚡ Z-Image-Turbo
            ### Ultra-Fast AI Image Generation
            """,
            elem_id="header-title"
        )
    
    with gr.Row():
        # --- Left Sidebar (Controls) ---
        with gr.Column(scale=1, elem_classes="glass-panel"):
            gr.Markdown("### ⚙️ Settings")
            
            model_dropdown = gr.Dropdown(
                label="Select Model",
                choices=[
                    "Disty0/Z-Image-Turbo-SDNQ-int8",
                    "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32"
                ],
                value="Disty0/Z-Image-Turbo-SDNQ-int8",
                interactive=True
            )
            
            prompt_input = gr.Textbox(
                label="Prompt", 
                placeholder="Describe your imagination... (e.g. A futuristic city with neon lights)", 
                lines=3
            )
            
            negative_prompt_input = gr.Textbox(
                label="Negative Prompt", 
                placeholder="Elements to avoid (e.g. blurred, low quality)", 
                lines=2
            )
            
            with gr.Accordion("🎨 Advanced Controls", open=False):
                steps_slider = gr.Slider(label="Steps", minimum=1, maximum=50, value=4, step=1)
                guidance_scale_slider = gr.Slider(label="Guidance Scale", minimum=0.0, maximum=20.0, value=0.0, step=0.1)
                with gr.Row():
                    width_slider = gr.Slider(label="Width", minimum=256, maximum=2048, value=1024, step=64)
                    height_slider = gr.Slider(label="Height", minimum=256, maximum=2048, value=1024, step=64)
                seed_number = gr.Number(label="Seed (-1 for Random)", value=42, precision=0)

            generate_btn = gr.Button("✨ Generate Image", elem_id="generate-btn")

        # --- Right Area (Preview) ---
        with gr.Column(scale=2, elem_classes="glass-panel"):
            gr.Markdown("### 🖼️ Preview")
            output_image = gr.Image(
                label="Generated Result", 
                type="pil", 
                interactive=False, 
                elem_id="output-image",
                height=600
            )

    # --- Event Binding ---
    generate_btn.click(
        fn=generate_image,
        inputs=[
            model_dropdown,
            prompt_input,
            negative_prompt_input,
            steps_slider,
            guidance_scale_slider,
            width_slider,
            height_slider,
            seed_number
        ],
        outputs=output_image
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)
