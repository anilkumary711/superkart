# SuperKart AKY project — completed starter

Open **Model_Deployment_AKY_Notebook.ipynb** for the executed source or **Model_Deployment_AKY_Report.html** for a readable report. The original starter structure is retained, all code blanks are filled, all 158 code cells have explanatory comments, and every code cell is immediately followed by observations.

## Verified results

- Split: 70:30, random_state=1, as specified by this starter.
- Two selected model families: Random Forest and Gradient Boosting; both tuned by fixed eight-combination, three-fold grid searches.
- Selected model: Random Forest tuned; training CV RMSE 281.02.
- Held-out RMSE 289.66, MAE 109.84, R² 0.9267.
- Eight API/frontend integration tests passed; see results/test_results.txt.
- Serialization reload reproduces all held-out predictions.

## What was corrected

The starter transformer would drop numeric predictors; the completed pipeline retains them. It clones preprocessors per candidate, uses a valid grid-search scorer, chooses the model by training-only CV, updates dependency/Python pins, corrects inherited observations and improves API/frontend validation and batch output.

The optional unselected algorithms remain commented, with filled examples. They were not trained or validated in this submission. The online API preserves the starter's Sales response key. Batch output maps row indexes to predictions; the frontend adds them back to the input rows and provides a CSV download.

## Files

- data/: the two supplied datasets.
- backend_files/: Flask application, saved fitted pipeline, metadata, pinned requirements, Dockerfile and Hugging Face README.
- frontend_files/: Streamlit application and matching deployment configuration.
- docker-compose.yml: two services connected through the Compose network.
- results/: CV/grid results, train/test tables, residual and feature diagnostics, batch predictions and local API evidence.
- tests/: API and Streamlit integration tests.
- DEPLOYMENT.md and verify_remote.py: instructions and a verifier for actual hosted endpoints.

## Running

Use Python 3.12, install requirements-notebook.txt and run the notebook from this folder. If using Colab, upload the two CSVs and use the optional installer cell before restarting the runtime. The notebook regenerates deployment files. To start locally with Docker, run `docker compose up --build -d`, then open port 8501. For a local code-only run, start `python backend_files/app.py`, then `python -m streamlit run frontend_files/app.py --server.port=8501` in a separate terminal.

## Hosting and submission

No repository upload, Docker build or cloud deployment was performed in the preparation environment. GitHub upload defaults to disabled and reads credentials only when enabled. Inference outputs in the delivered notebook are explicitly labeled LOCAL FLASK TEST CLIENT — NOT HOSTED. To obtain actual remote evidence, deploy using your account, set SUPERKART_API_URL, and rerun the inference section. Include actual backend/frontend links and UI/hosting screenshots in the required presentation. The starter specifies Codespaces while the supplied rubric screenshot specifies Hugging Face; confirm the required host.

Store age is frozen at reference year 2025 and product grouping follows this AKY starter. Currency and the sales time interval are unknown. Four-store random-split performance does not establish new-store or next-quarter forecasting accuracy. No separate slide deck is included in this notebook-completion request.
