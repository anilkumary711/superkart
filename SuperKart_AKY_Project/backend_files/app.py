# Generate backend_files/app.py as a reproducible deployment artifact.
"""SuperKart prediction API. Run from backend_files with gunicorn app:superkart_api."""
from pathlib import Path
import io
import json
import logging
import os

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
import joblib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv('MODEL_PATH', str(HERE / 'superkart_model.joblib')))
model = joblib.load(MODEL_PATH)
metadata = json.loads((HERE / 'model_metadata.json').read_text())
FEATURES = metadata['features']
NUMERIC = metadata['numeric_features']
CATEGORICAL = [c for c in FEATURES if c not in NUMERIC]
superkart_api = Flask(__name__)
superkart_api.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024


def validate_frame(frame):
    if frame.empty or len(frame) > 10000:
        raise ValueError('Provide between 1 and 10,000 rows.')
    if frame.columns.duplicated().any():
        raise ValueError('Duplicate column names are not allowed.')
    missing = sorted(set(FEATURES) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(FEATURES))
    if missing or extra:
        raise ValueError(f'Missing columns: {missing}; unexpected columns: {extra}')
    frame = frame[FEATURES].copy()
    if frame.isna().any().any():
        raise ValueError('Inputs must not contain missing values.')
    for col in NUMERIC:
        if frame[col].map(lambda value: isinstance(value, (bool, np.bool_))).any():
            raise ValueError(f'{col} must be numeric, not boolean.')
        frame[col] = pd.to_numeric(frame[col], errors='raise')
        if not np.isfinite(frame[col].to_numpy(dtype=float)).all():
            raise ValueError(f'{col} must contain finite numeric values.')
    for col in CATEGORICAL:
        if not frame[col].map(lambda value: isinstance(value, str)).all():
            raise ValueError(f'{col} must contain text values.')
        frame[col] = frame[col].str.strip()
        if frame[col].eq('').any():
            raise ValueError(f'{col} must not be blank.')
    frame['Product_Sugar_Content'] = frame['Product_Sugar_Content'].replace({'reg': 'Regular'})
    if (frame['Product_Weight'] <= 0).any() or (frame['Product_MRP'] <= 0).any():
        raise ValueError('Product_Weight and Product_MRP must be greater than zero.')
    if not frame['Product_Allocated_Area'].between(0, 1).all():
        raise ValueError('Product_Allocated_Area must be between 0 and 1.')
    age = frame['Store_Age_Years']
    if not age.between(0, 200).all() or (age % 1 != 0).any():
        raise ValueError('Store_Age_Years must be an integer between 0 and 200.')
    notices = []
    for col in CATEGORICAL:
        unseen = sorted(set(frame[col]) - set(metadata['categories'][col]))
        if unseen:
            notices.append(f'{col}: unseen categories {unseen}; predictions are extrapolations.')
    for col in NUMERIC:
        low, high = metadata['training_ranges'][col]
        if not frame[col].between(low, high).all():
            notices.append(f'{col}: some values are outside the training range [{low}, {high}].')
    return frame, notices


@superkart_api.get('/')
def home():
    return 'Welcome to the SuperKart System'


@superkart_api.get('/health')
def health():
    return jsonify(status='ok', model=metadata['selected_model'], reference_year=2025)


@superkart_api.post('/v1/predict')
def predict():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError('Send one JSON object containing the 10 model features.')
    frame, notices = validate_frame(pd.DataFrame([payload]))
    value = float(model.predict(frame)[0])
    return jsonify(Sales=value, warnings=notices)


@superkart_api.post('/v1/predictbatch')
def predictbatch():
    if 'file' not in request.files:
        raise ValueError('Upload a CSV using the multipart field named file.')
    raw = request.files['file'].read()
    try:
        # Inspect the raw header: pandas otherwise renames duplicate columns silently.
        import csv
        header = next(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
        if len(header) != len(set(header)):
            raise ValueError('Duplicate column names are not allowed.')
        frame = pd.read_csv(io.BytesIO(raw))
    except (UnicodeDecodeError, StopIteration, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise ValueError('Upload a nonempty, valid UTF-8 CSV.') from exc
    frame, notices = validate_frame(frame)
    values = model.predict(frame)
    response = jsonify({str(i): float(value) for i, value in enumerate(values)})
    # Preserve the row-index JSON contract shown in the starter notebook.
    if notices:
        response.headers['X-SuperKart-Warnings'] = json.dumps(notices)
    return response


@superkart_api.errorhandler(ValueError)
def invalid_input(exc):
    return jsonify(error=str(exc)), 400


@superkart_api.errorhandler(HTTPException)
def http_error(exc):
    return jsonify(error=exc.description), exc.code


@superkart_api.errorhandler(Exception)
def unexpected_error(exc):
    logging.exception('Prediction request failed')
    return jsonify(error='Prediction failed. Check the server logs.'), 500


if __name__ == '__main__':
    superkart_api.run(host='0.0.0.0', port=int(os.getenv('PORT', '7860')), debug=False)
