from pathlib import Path
import pandas as pd
import streamlit as st
from google import genai
from google.genai import errors, types
from data_loader import load_investigations, load_tests

st.set_page_config(page_title="Assistant | Flame in Freefall", layout="wide")
st.title("4. Assistant")

BASE_DIR = Path(__file__).parent.parent
PROMPT_PATH = BASE_DIR / "assistant_prompt.txt"
MODEL_NAME = "gemini-3.8-flash"


def load_system_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8").strip()
    return (
        "Answer strictly in English using only the provided catalog data. "
        "Always cite the source investigation by both its id and name. "
        'If the answer is not present in the data, reply: "Not in the catalog data."'
    )


def fmt_num(val) -> str:
    if pd.isna(val):
        return "no data"
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return f"{val:g}" if isinstance(val, float) else str(val)


@st.cache_data
def build_catalog_context() -> str:
    inv_df = load_investigations()
    tests_df = load_tests()

    inv_Display = inv_df.fillna("no data")
    inv_csv_text = inv_Display.to_csv(index=False)

    summary_rows = []
    if not tests_df.empty and "investigation_id" in tests_df.columns:
        for inv_id, grp in tests_df.groupby("investigation_id", dropna=False):
            inv_id_str = "no data" if pd.isna(inv_id) else str(inv_id)
            count = len(grp)
            o2_min = fmt_num(grp["o2_pct"].min()) if "o2_pct" in grp else "no data"
            o2_max = fmt_num(grp["o2_pct"].max()) if "o2_pct" in grp else "no data"
            p_min = fmt_num(grp["pressure_kpa"].min()) if "pressure_kpa" in grp else "no data"
            p_max = fmt_num(grp["pressure_kpa"].max()) if "pressure_kpa" in grp else "no data"
            summary_rows.append(
                {
                    "investigation_id": inv_id_str,
                    "test_count": count,
                    "o2_min_pct": o2_min,
                    "o2_max_pct": o2_max,
                    "pressure_min_kpa": p_min,
                    "pressure_max_kpa": p_max,
                }
            )

    summary_df = pd.DataFrame(summary_rows)
    summary_csv_text = (
        summary_df.to_csv(index=False) if not summary_df.empty else "no test conditions data"
    )

    return (
        "=== INVESTIGATIONS CATALOG (investigations.csv) ===\n"
        f"{inv_csv_text}\n"
        "=== TEST CONDITIONS SUMMARY BY INVESTIGATION_ID ===\n"
        f"{summary_csv_text}"
    )


def get_api_key() -> str | None:
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key and str(key).strip():
            return str(key).strip()
    except Exception:
        pass
    return None


api_key = get_api_key()
if not api_key:
    st.error(
        "Gemini API key not found. Please set `GEMINI_API_KEY` in `.streamlit/secrets.toml`."
    )

with st.sidebar:
    if st.button("Clear chat history"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("Ask a question about the NASA microgravity combustion catalog...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        if not api_key:
            err_msg = "Cannot query Gemini: `GEMINI_API_KEY` is missing in `.streamlit/secrets.toml`."
            st.warning(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
        else:
            system_prompt = load_system_prompt()
            catalog_context = build_catalog_context()

            history_lines = []
            for m in st.session_state.messages[:-1][-6:]:
                role_label = "User" if m["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {m['content']}")
            history_block = "\n".join(history_lines)

            full_prompt = (
                f"{catalog_context}\n\n"
                + (f"=== RECENT CONVERSATION ===\n{history_block}\n\n" if history_block else "")
                + f"=== USER QUESTION ===\n{user_query}"
            )

            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            )

            try:
                placeholder = st.empty()
                collected_chunks: list[str] = []
                for chunk in client.models.generate_content_stream(
                    model=MODEL_NAME,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.1,
                    ),
                ):
                    if chunk.text:
                        collected_chunks.append(chunk.text)
                        placeholder.markdown("".join(collected_chunks))

                answer = "".join(collected_chunks).strip() or "Not in the catalog data."
                placeholder.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except errors.ClientError as e:
                if e.code == 429:
                    msg = "Rate limit exceeded (HTTP 429). Please wait a minute and try again."
                else:
                    msg = f"Gemini API client error (HTTP {e.code}): {e.message}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            except errors.APIError as e:
                msg = f"Gemini API server error: {e.message if hasattr(e, 'message') else e}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            except Exception as e:
                msg = f"Unexpected connection error ({type(e).__name__}): {e}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})