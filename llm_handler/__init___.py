from .claude import send_to_claude
from .ollama import send_to_ollama


def query_llm(backend="claude", image_path=None, metadata="", ollama_model_name: str = None):
    if backend == "claude":
        return send_to_claude(image_path, metadata)
    elif backend == "ollama":
        return send_to_ollama(metadata=metadata, image_path=image_path, model_name=ollama_model_name)
    else:
        return "Invalid backend selected."
