import requests
from .base import encode_image_base64

# Note for Image Analysis with Ollama:
# The Ollama model used for analysis is configured by the user in Blender's add-on settings.
# For image analysis features to work, this user-specified model *must* be a
# multimodal model capable of processing images (e.g., "llava:latest").
# Ensure the selected model is downloaded and running via Ollama.


def send_to_ollama(metadata, model_name: str, image_path=None):
    if image_path:
        base64_image = encode_image_base64(image_path)
        prompt = f"Analyze this image and its Blender scene metadata:\n\n{metadata}"
        payload = {
            "model": model_name,  # User-configured model
            "prompt": prompt,
            "images": [base64_image],
        }
    else:
        prompt = f"Analyze this Blender scene metadata:\n\n{metadata}"
        payload = {
            "model": model_name,  # User-configured model
            "prompt": prompt,
        }

    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
    )

    return response.json()["response"]
