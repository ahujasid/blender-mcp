import requests


def send_to_ollama(metadata):
    prompt = f"Analyze this Blender scene:\n\n{metadata}"

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "gemma3:4b", "prompt": prompt},  # or any model you have loaded
    )

    return response.json()["response"]
