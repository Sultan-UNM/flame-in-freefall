import time, tomllib
from pathlib import Path
from google import genai
from google.genai import types

key = tomllib.loads(Path(".streamlit/secrets.toml").read_text())["GEMINI_API_KEY"]
client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=30_000))

def run(label, model, thinking):
    t = time.perf_counter()
    try:
        cfg = types.GenerateContentConfig(max_output_tokens=800, thinking_config=thinking)
        r = client.models.generate_content(model=model, contents="Say hello in one sentence.", config=cfg)
        print(f"{label}: {time.perf_counter()-t:.1f}s -> {r.text!r}")
    except Exception as e:
        print(f"{label}: FAILED after {time.perf_counter()-t:.1f}s -> {type(e).__name__}: {e}")

run("3.8 no thinking cfg", "gemini-3.8-flash", None)
run("3.8 thinking_level=low", "gemini-3.8-flash", types.ThinkingConfig(thinking_level="low"))
run("3.8 thinking_budget=0", "gemini-3.8-flash", types.ThinkingConfig(thinking_budget=0))
run("3.5-flash no thinking cfg", "gemini-3.5-flash", None)