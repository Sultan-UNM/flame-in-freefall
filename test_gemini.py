from pathlib import Path
import time
import tomllib
from google import genai
from google.genai import errors, types

MODEL_NAME = "gemini-3.8-flash"


def main() -> None:
    secrets_path = Path(".streamlit/secrets.toml")
    if not secrets_path.exists():
        raise FileNotFoundError(f"Missing {secrets_path}")

    with secrets_path.open("rb") as f:
        secrets = tomllib.load(f)

        api_key = secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .streamlit/secrets.toml")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=30_000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )

    print(f"Streaming request to {MODEL_NAME} (timeout=30s)...", flush=True)
    t0 = time.perf_counter()
    try:
        for chunk in client.models.generate_content_stream(
            model=MODEL_NAME,
            contents="Reply in one short sentence: confirm Gemini API is working.",
        ):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()
    except errors.APIError as e:
        code = getattr(e, "code", "unknown")
        status = getattr(e, "status", "unknown")
        message = getattr(e, "message", str(e))
        print(f"\nAPIError [HTTP {code} / {status}]: {message}\nFull error: {repr(e)}")
    except Exception as e:
        is_timeout = "timeout" in type(e).__name__.lower() or "timed out" in str(e).lower()
        label = "TIMEOUT (30s)" if is_timeout else type(e).__name__
        print(f"\nError [{label}]: {e}\nFull error: {repr(e)}")
    finally:
        elapsed = time.perf_counter() - t0
        print(f"Elapsed time: {elapsed:.2f} s")


if __name__ == "__main__":
    main()