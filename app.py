
import base64
import io
import time
import requests
import streamlit as st
from PIL import Image

BASE_URL = "https://api.fashn.ai/v1"

st.set_page_config(
    page_title="Vav n Val | AI Virtual Try-On",
    page_icon="👗",
    layout="wide",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .block-container { max-width: 1200px; padding-top: 2rem; }
    .brand {
        text-align:center;
        font-size: 42px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 0;
    }
    .tagline {
        text-align:center;
        color:#777;
        margin-top: 0.2rem;
        margin-bottom: 2rem;
    }
    .result-box {
        border: 1px solid #e8e8e8;
        border-radius: 18px;
        padding: 18px;
        background: #fff;
    }
    div.stButton > button {
        width:100%;
        border-radius: 12px;
        min-height: 48px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand">Vav n Val</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="tagline">AI Virtual Try-On Studio</div>',
    unsafe_allow_html=True
)

# ---------- API key ----------
api_key = None

try:
    api_key = st.secrets.get("FASHN_API_KEY")
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("FASHN_API_KEY")

if not api_key:
    st.warning(
        "FASHN API key set nahi hai. Streamlit Cloud me App settings → Secrets "
        "me FASHN_API_KEY add karein."
    )
    st.stop()


def image_to_data_uri(uploaded_file):
    raw = uploaded_file.getvalue()
    if not raw:
        raise ValueError("Image empty hai.")

    mime = uploaded_file.type or "image/jpeg"
    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def run_fashn(model_file, garment_file, resolution, generation_mode,
              num_images, prompt, output_format):
    model_data = image_to_data_uri(model_file)
    garment_data = image_to_data_uri(garment_file)

    inputs = {
        "product_image": garment_data,
        "model_image": model_data,
        "resolution": resolution,
        "generation_mode": generation_mode,
        "num_images": num_images,
        "output_format": output_format,
        "return_base64": True,
    }

    if prompt.strip():
        inputs["prompt"] = prompt.strip()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.post(
        f"{BASE_URL}/run",
        json={"model_name": "tryon-max", "inputs": inputs},
        headers=headers,
        timeout=60,
    )

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"FASHN API error ({response.status_code}): {detail}")

    data = response.json()
    prediction_id = data.get("id")

    if not prediction_id:
        raise RuntimeError(f"Prediction ID nahi mila: {data}")

    progress = st.progress(0, text="AI generation start ho rahi hai...")

    for attempt in range(120):
        status_response = requests.get(
            f"{BASE_URL}/status/{prediction_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60,
        )

        if status_response.status_code >= 400:
            try:
                detail = status_response.json()
            except Exception:
                detail = status_response.text
            raise RuntimeError(
                f"FASHN status error ({status_response.status_code}): {detail}"
            )

        status_data = status_response.json()
        status = status_data.get("status")

        progress_value = min(95, 5 + int((attempt / 120) * 90))
        progress.progress(
            progress_value,
            text=f"Status: {status or 'processing'}..."
        )

        if status == "completed":
            progress.progress(100, text="Generation complete.")
            outputs = status_data.get("output") or []
            if not outputs:
                raise RuntimeError("Generation complete hua, lekin output nahi mila.")

            # With return_base64=true the docs say outputs are data URIs.
            return outputs, status_data

        if status == "failed":
            error = status_data.get("error") or "Unknown FASHN runtime error"
            raise RuntimeError(f"Generation failed: {error}")

        time.sleep(3)

    raise TimeoutError("Generation timeout ho gaya. FASHN status dashboard me check karein.")


def data_uri_to_bytes(data_uri):
    if not isinstance(data_uri, str) or "," not in data_uri:
        raise ValueError("Unexpected output format.")
    _, encoded = data_uri.split(",", 1)
    return base64.b64decode(encoded)


# ---------- UI ----------
left, right = st.columns(2, gap="large")

with left:
    st.subheader("👩 Model Photo")
    model_file = st.file_uploader(
        "Model photo upload karein",
        type=["jpg", "jpeg", "png", "webp"],
        key="model",
    )
    if model_file:
        st.image(model_file, use_container_width=True)

with right:
    st.subheader("👗 Garment / Dress")
    garment_file = st.file_uploader(
        "Dress / garment photo upload karein",
        type=["jpg", "jpeg", "png", "webp"],
        key="garment",
    )
    if garment_file:
        st.image(garment_file, use_container_width=True)

st.divider()

c1, c2, c3 = st.columns(3)

with c1:
    resolution = st.selectbox("Resolution", ["1k", "2k", "4k"], index=1)

with c2:
    generation_mode = st.selectbox(
        "Generation Quality",
        ["fast", "balanced", "quality"],
        index=1,
    )

with c3:
    num_images = st.selectbox("Number of Results", [1, 2, 3, 4], index=0)

prompt = st.text_input(
    "Optional styling instruction",
    placeholder="Example: remove scarf, tuck in shirt, open jacket",
)

output_format = st.selectbox(
    "Output Format",
    ["png", "jpeg"],
    index=0,
)

generate = st.button("✨ Generate AI Try-On", type="primary")

if generate:
    if not model_file or not garment_file:
        st.error("Model photo aur garment photo dono upload karein.")
    else:
        try:
            with st.spinner("FASHN AI result generate kar raha hai..."):
                outputs, metadata = run_fashn(
                    model_file,
                    garment_file,
                    resolution,
                    generation_mode,
                    num_images,
                    prompt,
                    output_format,
                )

            st.success("✅ Try-On complete!")

            st.subheader("Generated Results")

            cols = st.columns(min(2, len(outputs)))
            for i, output in enumerate(outputs):
                img_bytes = data_uri_to_bytes(output)
                file_ext = "png" if output_format == "png" else "jpg"

                with cols[i % len(cols)]:
                    st.image(img_bytes, caption=f"Result {i+1}", use_container_width=True)
                    st.download_button(
                        label=f"⬇️ Download Result {i+1}",
                        data=img_bytes,
                        file_name=f"vav_n_val_tryon_{i+1}.{file_ext}",
                        mime=f"image/{output_format}",
                        key=f"download_{i}",
                    )

            st.caption("Generated with FASHN Try-On Max.")

        except Exception as exc:
            st.error(str(exc))

st.divider()
st.caption("Vav n Val • AI Virtual Try-On Studio")
