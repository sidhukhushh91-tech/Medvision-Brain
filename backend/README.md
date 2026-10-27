---
title: MedVision AI API
emoji: 🧠
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# MedVision AI

This Docker Space serves both the MedVision AI website and its image-analysis API from one public URL.

Educational-only brain MRI classification API. This service is not a medical device.

The Docker build expects `main.py`, `requirements.txt`, and the `frontend` folder (including `package.json`, `package-lock.json`, `index.html`, and `src`). It builds the React app and serves it from the API, so no separate Vercel project or CORS configuration is needed.

The classifier loads when the Space starts. Free Spaces may sleep after inactivity, and the first visit after sleep can take time while the service starts and loads the model. Allow sufficient memory and storage for the model and PyTorch.
