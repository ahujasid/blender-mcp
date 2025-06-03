import requests
from .base import encode_image_base64

CLAUDE_API_KEY = "your-anthropic-api-key"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"


def send_to_claude(image_path, metadata):
    image_b64 = encode_image_base64(image_path)

    payload = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"This is a scene summary:\n{metadata}"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        },
                    },
                ],
            }
        ],
    }

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    response = requests.post(CLAUDE_API_URL, json=payload, headers=headers)
    return response.json()["content"][0]["text"]
