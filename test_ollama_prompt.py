import io
import json
import urllib.error
import urllib.request

import ollama_prompt as op


def run():
    calls = {}

    def fake_urlopen(req, timeout=None):
        calls["url"] = req.full_url
        calls["body"] = json.loads(req.data)
        return io.BytesIO(json.dumps({"response": "<think>hmm</think>\n a vivid cat \n"}).encode())

    urllib.request.urlopen = fake_urlopen
    (pipe,) = op.OllamaPromptRefiner().refine(
        "CLIP", "cat", "instr", "llama3.2", "http://localhost:11434/", 7, True, 300
    )
    assert calls["url"] == "http://localhost:11434/api/generate", calls["url"]
    assert calls["body"]["system"] == "instr" and calls["body"]["options"]["seed"] == 7
    assert calls["body"]["keep_alive"] == 0, calls["body"]
    assert calls["body"]["options"]["num_predict"] == 300, calls["body"]
    assert pipe == ("CLIP", "a vivid cat"), pipe

    def boom(req, timeout=None):
        raise urllib.error.URLError("refused")

    urllib.request.urlopen = boom
    assert op._models("http://x") == []
    assert op.OllamaPromptRefiner.INPUT_TYPES()["required"]["model"][0] == "STRING"
    try:
        op.OllamaPromptRefiner().refine("CLIP", "cat", "i", "m", "http://x", 0, False, 300)
    except RuntimeError as e:
        assert "failed" in str(e)
    else:
        raise AssertionError("expected RuntimeError")
    print("ok")


if __name__ == "__main__":
    run()
