# MedVision AI

An educational brain MRI image-classification demo. The project now includes a React frontend and FastAPI backend, and retains the original Streamlit app as a lightweight alternative.

> **Important:** This project is not a medical device. Model outputs are educational only, are not diagnoses, and must not guide medical decisions. The displayed score is not a clinically calibrated probability. Do not upload identifiable patient information.

## Features

- Responsive medical-themed React dashboard with image preview, loading state, validation, and class-score display
- FastAPI endpoints for health status and image classification
- Real inference through the pretrained four-class Swin model `Devarshi/Brain_Tumor_Classification`
- JPG, JPEG, and PNG validation, with a 10 MB file limit
- Images are not retained by the app after a request (the multipart upload handler may use temporary buffers)
- Explicit service errors when the model cannot be loaded or an image cannot be analyzed; no mock predictions
- Original Streamlit app remains available in `app.py`

The model files download from Hugging Face on first analysis. Internet access is required for that download. The model's published evaluation is not independently verified and does not establish clinical reliability.

Model page: https://huggingface.co/Devarshi/Brain_Tumor_Classification

## Requirements

- Windows 10/11
- Python 3.11 recommended (the existing environment was also verified with Python 3.13)
- Node.js 20 or newer with npm
- Internet access for dependency installation and first-time model download
- Several GB of free storage recommended for the Python environment and model cache

## Run the React + FastAPI application on Windows

1. Install Python and Node.js if they are not already installed.
2. Double-click `run_website_windows.bat`. It creates a local Python environment if needed, installs missing dependencies, starts the API and frontend in separate windows, and opens **http://localhost:5173**.

To run the services manually instead:

1. Open a terminal in this project folder.
2. Create and activate the Python environment, then install backend dependencies:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Install the frontend packages:

   ```powershell
   cd frontend
   npm install
   cd ..
   ```

4. Start the backend in one terminal:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. Start the frontend in a second terminal:

   ```powershell
   cd frontend
   npm run dev
   ```

6. Open **http://localhost:5173**. The API health check is available at **http://127.0.0.1:8000/api/health**, and interactive API documentation is at **http://127.0.0.1:8000/docs**.

The model loads the first time an image is analyzed. Until the backend is reachable, or if model loading fails, the page shows a service error instead of fabricated results.

## Deploy one shareable website for free

The Docker Space serves the React website and FastAPI analysis API from the same public URL. It avoids needing a separate Vercel frontend, backend URL, or CORS setup.

1. Sign in to [Hugging Face](https://huggingface.co/) and create a **public Docker Space** named `medvision-ai` (or another available name).
2. Upload the following files to the Space repository, preserving the listed paths:

   ```text
   backend/README.md             -> README.md
   backend/Dockerfile            -> Dockerfile
   backend/main.py               -> main.py
   backend/requirements.txt      -> requirements.txt
   frontend/package.json         -> frontend/package.json
   frontend/package-lock.json    -> frontend/package-lock.json
   frontend/index.html           -> frontend/index.html
   frontend/src/                 -> frontend/src/
   ```

3. Wait for the Space to build. The single public website/API URL will be `https://YOUR-USERNAME-medvision-ai.hf.space`. Open it; the site reports the analysis service online when the model is loaded. The API health check is at `/api/health`.
4. Share the Space URL.

The backend preloads the classifier at startup to avoid downloading it on the first image request while it is running. Free Spaces may sleep after inactivity, however, so the first visit after a period of inactivity can still be delayed while the Space wakes and the model loads. Free hosting cannot guarantee an always-ready, zero-delay link. Do not upload patient-identifying images.

Creating the Space requires signing in to your own Hugging Face account. Never share your password or access token in chat.

### Configuration

Set `MEDVISION_MODEL_ID` before starting the backend to select a compatible Hugging Face image-classification checkpoint. The default is `Devarshi/Brain_Tumor_Classification`. A compatible checkpoint must include both model weights/configuration and an image processor configuration.

For a different frontend/API origin, set `VITE_API_URL` in `frontend/.env.local`, for example:

```text
VITE_API_URL=http://127.0.0.1:8000
```

Copy `frontend/.env.example` to `frontend/.env.local` to explicitly configure local development. The development server defaults to localhost; the production build intentionally does not fall back to a localhost API if `VITE_API_URL` is missing.

### Production frontend build

```powershell
cd frontend
npm run build
npm run preview
```

The development server is configured for local use. If exposing the API beyond localhost, configure appropriate CORS origins, HTTPS, authentication, and deployment security before doing so.

### Run backend validation tests

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

## Run the retained Streamlit application

The original implementation is preserved in `app.py`. To run it instead:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Or use `run_windows.bat` for its original setup-and-run workflow.

## Project structure

```text
MedVisionAI_Ready_Project/
├── backend/
│   ├── __init__.py
│   ├── Dockerfile
│   ├── README.md
│   ├── requirements.txt
│   ├── main.py
│   └── tests/
│       └── test_api.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── .env.example
│   ├── package.json
│   ├── package-lock.json
│   └── vercel.json
├── app.py                 # Retained Streamlit application
├── requirements.txt
├── run_windows.bat        # Retained Streamlit launcher
└── README.md
```

## Troubleshooting

- **Frontend says the analysis service is offline:** Start the FastAPI command in the second terminal and check `http://127.0.0.1:8000/api/health`.
- **Classifier model unavailable:** Check internet connectivity and the model ID. First-time downloads can take several minutes.
- **`npm` is not recognized:** Install Node.js 20+ and reopen the terminal.
- **Image rejected:** Use a readable JPG/JPEG/PNG under 10 MB and 20 megapixels.
- **Python package install fails:** Verify Python 3.11+ is active, then review the package-install error.
- **Port already in use:** Start Uvicorn with another port and update `VITE_API_URL` to match.
