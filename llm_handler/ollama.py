import requests
from .base import encode_image_base64

# Note for Image Analysis with Ollama:
# To use image analysis features, ensure you have a multimodal model
# (e.g., "llava:latest") downloaded and running via Ollama.
# If you are using a different multimodal model, you may need to update
# the `model_name` variable within the `send_to_ollama` function below.


def send_to_ollama(metadata, image_path=None):
    model_name = "llava:latest"  # Common multimodal model

    if image_path:
        base64_image = encode_image_base64(image_path)
        prompt = f"Analyze this image and its Blender scene metadata:\n\n{metadata}"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "images": [base64_image],
        }
    else:
        prompt = f"Analyze this Blender scene metadata:\n\n{metadata}"
        payload = {
            "model": model_name,
            "prompt": prompt,
        }

    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
    )

    return response.json()["response"]
