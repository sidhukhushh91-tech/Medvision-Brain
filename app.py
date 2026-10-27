import time
from io import BytesIO

import streamlit as st
import torch
from PIL import Image, UnidentifiedImageError
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL_ID = "Devarshi/Brain_Tumor_Classification"
MAX_FILE_SIZE_MB = 10

st.set_page_config(
    page_title="MedVision AI | Brain MRI Analysis",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
    .main { background: #f7f9fc; }
    .hero {
        padding: 1.5rem 1.8rem;
        border-radius: 18px;
        background: linear-gradient(120deg, #e8f2ff, #f2edff);
        border: 1px solid #dbe6f7;
        margin-bottom: 1.2rem;
    }
    .hero h1 { margin-bottom: .35rem; color: #172554; }
    .small-note { color: #64748b; font-size: .92rem; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e2e8f0;
        padding: 1rem; border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def load_model():
    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
    model.eval()
    return processor, model

def readable_label(label):
    label = str(label).strip().replace("_", " ").replace("-", " ")
    if label.lower() in {"notumor", "no tumor", "no_tumor"}:
        return "No-tumor class"
    return label.title()

st.markdown("""
<div class="hero">
  <h1>🧠 MedVision AI</h1>
  <p><b>Brain MRI Image Classification</b></p>
  <p class="small-note">An educational demonstration using a publicly available, pretrained image-classification model.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("About this project")
    st.write("Upload a brain MRI image to see the model's predicted class and class probabilities.")
    st.divider()
    st.subheader("Supported input")
    st.write("JPG, JPEG, or PNG")
    st.write(f"Maximum file size: {MAX_FILE_SIZE_MB} MB")
    st.divider()
    st.caption("The model downloads from Hugging Face the first time you run the app. An internet connection is required.")

st.warning(
    "Educational/research use only. This tool is not a medical device and cannot diagnose, "
    "rule out, or guide treatment for a brain tumor. Do not upload identifiable patient data. "
    "Consult a qualified radiologist or clinician for medical interpretation."
)

left, right = st.columns([1, 1], gap="large")
with left:
    st.subheader("1. Upload MRI image")
    uploaded_file = st.file_uploader(
        "Choose a brain MRI image",
        type=["jpg", "jpeg", "png"],
        help="Use a suitable MRI image. This demo was trained on a particular public dataset and may fail on other image types."
    )
    analyze = st.button("🔍 Analyze Image", type="primary", use_container_width=True, disabled=uploaded_file is None)

with right:
    st.subheader("2. Image preview")
    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"File is too large. Please upload an image smaller than {MAX_FILE_SIZE_MB} MB.")
            uploaded_file = None
        else:
            try:
                image = Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")
                st.image(image, caption="Uploaded image", use_container_width=True)
            except (UnidentifiedImageError, OSError):
                st.error("This file could not be opened as an image.")
                uploaded_file = None
    else:
        st.info("Your selected image will appear here.")

if analyze and uploaded_file is not None:
    try:
        image = Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")
        with st.spinner("Loading model and analyzing image... First run may take a few minutes while model files download."):
            start = time.perf_counter()
            processor, model = load_model()
            inputs = processor(images=image, return_tensors="pt")
            with torch.inference_mode():
                outputs = model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)[0]
            elapsed = time.perf_counter() - start

        id2label = getattr(model.config, "id2label", {}) or {}
        labels = [readable_label(id2label.get(i, f"Class {i}")) for i in range(len(probabilities))]
        sorted_indices = torch.argsort(probabilities, descending=True).tolist()
        top_idx = sorted_indices[0]
        predicted_label = labels[top_idx]
        confidence = float(probabilities[top_idx]) * 100

        st.divider()
        st.subheader("3. Model result")
        m1, m2 = st.columns(2)
        m1.metric("Predicted class", predicted_label)
        m2.metric("Top-class model score", f"{confidence:.1f}%")
        st.caption(f"Inference time including model loading on first run: {elapsed:.2f} seconds. This is a model score, not a medically calibrated probability.")

        st.subheader("Class scores")
        for idx in sorted_indices:
            st.write(f"**{labels[idx]}** — {float(probabilities[idx]) * 100:.2f}%")
            st.progress(float(probabilities[idx]))

        st.download_button(
            "⬇️ Download text report",
            data=(
                "MedVision AI - Educational Analysis Report\n"
                "===========================================\n"
                f"File name: {uploaded_file.name}\n"
                f"Predicted class: {predicted_label}\n"
                f"Top-class model score: {confidence:.2f}%\n"
                f"Inference time: {elapsed:.2f} seconds\n"
                f"Model: {MODEL_ID}\n\n"
                "DISCLAIMER: This is an educational/research output, not a diagnosis. "
                "A model score is not a calibrated clinical probability. Seek a qualified clinician's interpretation.\n"
            ),
            file_name="medvision_analysis_report.txt",
            mime="text/plain",
        )
    except Exception as exc:
        st.error("The model could not analyze this image.")
        st.exception(exc)
        st.info("Check your internet connection and installed packages, then try again.")

st.divider()
st.caption("MedVision AI • Student project prototype • Always seek professional medical advice for real health concerns.")
