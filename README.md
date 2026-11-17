# ComfyUI-OllamaPrompt

A custom node which uses Ollama to refine the input prompt.

No Python dependencies; it talks to Ollama's HTTP API directly.

## Install

1. Install [Ollama](https://ollama.com) and pull a model, e.g. `ollama pull llama3.2`.
2. Search for **Ollama Prompt** in ComfyUI-Manager, or:

   ```sh
   cd ComfyUI/custom_nodes
   git clone https://github.com/retrodiffuse/ComfyUI-OllamaPrompt
   ```

3. Restart ComfyUI.

## Nodes

**Ollama Prompt Refiner** sends your prompt and instruction to Ollama and outputs the rewritten prompt along with the CLIP model.

| Input | Does |
| --- | --- |
| `model` | Dropdown of installed models (free text if Ollama isn't reachable when ComfyUI loads) |
| `instruction` | System prompt telling the model how to rewrite |
| `url` | Ollama server, defaults to `OLLAMA_HOST` or `http://localhost:11434` |
| `seed` | Fixed seed gives a repeatable rewrite |
| `unload_after` | Unload the model from VRAM after each run, leaving room for diffusion |
| `max_tokens` | Output cap, `-1` for no limit |

`<think>` blocks from reasoning models are stripped.

**Ollama Prompt Preview** shows the refined text on the node and encodes it to `CONDITIONING` for your sampler.

## License

Apache-2.0.
