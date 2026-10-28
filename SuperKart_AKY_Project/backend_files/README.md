---
# Generate backend_files/README.md as a reproducible deployment artifact.
title: SuperKart Prediction API
emoji: 🛒
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# SuperKart Prediction API

Upload the contents of this folder to a Blank Docker Hugging Face Space.
The pipeline is already trained. `GET /health` checks readiness.

- `POST /v1/predict`: JSON object with the 10 prepared feature columns.
- `POST /v1/predictbatch`: multipart CSV upload in field `file`.

Currency and sales time interval are unspecified. Store age uses 2025.
Unknown categories are accepted with extrapolation warnings.
