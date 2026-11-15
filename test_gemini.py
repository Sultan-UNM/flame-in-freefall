from pathlib import Path
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
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )

    print(f"Streaming request to {MODEL_NAME}...", flush=True)
    try:
        for chunk in client.models.generate_content_stream(
            model=MODEL_NAME,
            contents="Reply in one short sentence: confirm Gemini API is working.",
        ):
            print(chunk.text, end="", flush=True)
        print()
    except errors.ClientError as e:
        if e.code == 429:
            print(f"Rate limit exceeded (HTTP 429): {e.message}")
        else:
            print(f"Client error (HTTP {e.code}): {e.message}")
    except errors.APIError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Network/Timeout error ({type(e).__name__}): {e}")


if __name__ == "__main__":
    main()