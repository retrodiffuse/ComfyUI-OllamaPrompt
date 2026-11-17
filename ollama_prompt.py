import json
import os
import re
import urllib.error
import urllib.request

_env = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = _env if _env.startswith("http") else "http://" + _env

DEFAULT_INSTRUCTION = (
    "You are a prompt engineer for image diffusion models. Rewrite the user's prompt "
    "with richer visual detail: subject, composition, lighting, materials, mood, style. "
    "Keep the original intent. Reply with the prompt only, no preamble, no quotes."
)


def _models(url):
    """Installed models, refreshed whenever ComfyUI asks for node definitions."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=2) as r:
            return [m["name"] for m in json.load(r)["models"]]
    except Exception:
        return []  # ponytail: server down -> fall back to a free-text field


def _ollama(url, model, system, prompt, seed, unload, num_predict):
    body = json.dumps({
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "keep_alive": 0 if unload else "5m",
        "options": {"seed": seed, "num_predict": num_predict},
    }).encode()
    req = urllib.request.Request(
        url.rstrip("/") + "/api/generate", body, {"Content-Type": "application/json"}
    )
    try:
        # ponytail: 10 min covers a slow CPU model; make it a widget if that ever bites
        with urllib.request.urlopen(req, timeout=600) as r:
            text = json.load(r)["response"]
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(f"Ollama request to {url} failed: {e}") from e
    # ponytail: reasoning models emit <think>...</think>; drop it, keep the prompt
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


class OllamaPromptRefiner:
    @classmethod
    def INPUT_TYPES(cls):
        models = _models(OLLAMA_URL)
        return {
            "required": {
                "clip": ("CLIP",),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "instruction": ("STRING", {"multiline": True, "default": DEFAULT_INSTRUCTION}),
                "model": (models,) if models else ("STRING", {"default": "llama3.2"}),
                "url": ("STRING", {"default": OLLAMA_URL}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0x7FFFFFFFFFFFFFFF,  # Ollama reads seed as int64
                                 "control_after_generate": True}),
                "unload_after": ("BOOLEAN", {"default": True}),
                "max_tokens": ("INT", {"default": 300, "min": -1, "max": 8192,
                                       "tooltip": "Output token cap (-1 = no limit)"}),
            }
        }

    RETURN_TYPES = ("PROMPT_PREV",)
    RETURN_NAMES = ("prompt_prev",)
    FUNCTION = "refine"
    CATEGORY = "OllamaPrompt"

    def refine(self, clip, prompt, instruction, model, url, seed, unload_after, max_tokens):
        return ((clip, _ollama(url, model, instruction, prompt, seed, unload_after, max_tokens)),)


class OllamaPromptPreview:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"prompt_prev": ("PROMPT_PREV",)}}

    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"
    OUTPUT_NODE = True
    CATEGORY = "OllamaPrompt"

    def encode(self, prompt_prev):
        clip, text = prompt_prev
        tokens = clip.tokenize(text)
        if hasattr(clip, "encode_from_tokens_scheduled"):
            cond = clip.encode_from_tokens_scheduled(tokens)
        else:
            out, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            cond = [[out, {"pooled_output": pooled}]]
        return {"ui": {"text": [text]}, "result": (cond,)}


NODE_CLASS_MAPPINGS = {
    "OllamaPromptRefiner": OllamaPromptRefiner,
    "OllamaPromptPreview": OllamaPromptPreview,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaPromptRefiner": "Ollama Prompt Refiner",
    "OllamaPromptPreview": "Ollama Prompt Preview",
}
