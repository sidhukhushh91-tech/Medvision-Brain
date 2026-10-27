import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Annotated

import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL_ID = os.getenv("MEDVISION_MODEL_ID", "Devarshi/Brain_Tumor_Classification")
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

logger = logging.getLogger("medvision")
_model_lock = threading.Lock()
_inference_lock = threading.Lock()
_processor = None
_model = None
_model_error = None


class ModelUnavailableError(RuntimeError):
    pass


class ClassScore(BaseModel):
    label: str
    score: float


class PredictionResponse(BaseModel):
    predicted_class: str
    confidence: float
    scores: list[ClassScore]
    inference_seconds: float
    model_id: str
    disclaimer: str


class HealthResponse(BaseModel):
    status: str
    model_id: str
    model_loaded: bool
    model_error: str | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await run_in_threadpool(_load_model)
    except ModelUnavailableError:
        logger.warning("Starting API without a loaded classifier; predictions will be unavailable.")
    yield


app = FastAPI(
    title="MedVision AI API",
    description="Educational brain MRI image classification API.",
    version="1.0.0",
    lifespan=lifespan,
)
configured_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("MEDVISION_CORS_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _load_model():
    global _processor, _model, _model_error

    if _model is not None and _processor is not None:
        return _processor, _model

    with _model_lock:
        if _model is not None and _processor is not None:
            return _processor, _model
        try:
            processor = AutoImageProcessor.from_pretrained(MODEL_ID)
            model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
            model.eval()
        except Exception as exc:
            _model_error = "Model failed to load. Check your internet connection and model configuration."
            logger.exception("Could not load classifier model %s", MODEL_ID)
            raise ModelUnavailableError(
                "The classifier model is unavailable. Check your internet connection "
                "and model configuration, then try again."
            ) from exc

        _processor = processor
        _model = model
        _model_error = None
        return _processor, _model


def _display_label(label: str) -> str:
    cleaned = str(label).strip().replace("_", " ").replace("-", " ")
    if cleaned.casefold() in {"notumor", "no tumor"}:
        return "No tumor"
    return cleaned.title()


def _decode_image(image_bytes: bytes, filename: str) -> Image.Image:
    extension = os.path.splitext(filename)[1].casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a JPG, JPEG, or PNG image.",
        )

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            if source.format not in {"JPEG", "PNG"}:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file contents are not a JPG, JPEG, or PNG image.",
                )
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=413,
                    detail="The image dimensions are too large. Upload an image under 20 megapixels.",
                )
            source.load()
            return source.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a readable image. Choose a valid JPG, JPEG, or PNG file.",
        ) from exc


def _classify(image_bytes: bytes, filename: str) -> PredictionResponse:
    started = time.perf_counter()
    image = _decode_image(image_bytes, filename)
    try:
        processor, model = _load_model()
        inputs = processor(images=image, return_tensors="pt")
        with _inference_lock, torch.inference_mode():
            logits = model(**inputs).logits
            probabilities = torch.softmax(logits, dim=-1)[0]
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Image inference failed for model %s", MODEL_ID)
        raise HTTPException(
            status_code=500,
            detail="The classifier could not process this image. Please try another image.",
        ) from exc

    id2label = getattr(model.config, "id2label", {}) or {}
    scores = [
        ClassScore(
            label=_display_label(id2label.get(index, f"Class {index}")),
            score=float(probabilities[index]) * 100,
        )
        for index in range(len(probabilities))
    ]
    scores.sort(key=lambda item: item.score, reverse=True)
    if not scores:
        raise HTTPException(status_code=503, detail="The classifier returned no class scores.")

    return PredictionResponse(
        predicted_class=scores[0].label,
        confidence=scores[0].score,
        scores=scores,
        inference_seconds=time.perf_counter() - started,
        model_id=MODEL_ID,
        disclaimer=(
            "Educational output only; not a diagnosis. Model scores are not "
            "clinically calibrated probabilities."
        ),
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_id=MODEL_ID,
        model_loaded=_model is not None,
        model_error=_model_error,
    )


@app.post("/api/predict", response_model=PredictionResponse)
async def predict_image(
    file: Annotated[UploadFile, File(description="A brain MRI image in JPG, JPEG, or PNG format")],
) -> PredictionResponse:
    extension = os.path.splitext(file.filename or "")[1].casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a JPG, JPEG, or PNG image.",
        )

    image_bytes = bytearray()
    try:
        while chunk := await file.read(1024 * 1024):
            image_bytes.extend(chunk)
            if len(image_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="The file is too large. Upload an image smaller than 10 MB.",
                )
    finally:
        await file.close()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    return await run_in_threadpool(_classify, bytes(image_bytes), file.filename or "")


@app.exception_handler(HTTPException)
async def http_error_response(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


STATIC_DIR = Path(__file__).with_name("static")
if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_frontend() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")
