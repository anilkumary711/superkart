# Generate frontend_files/app.py as a reproducible deployment artifact.
"""Streamlit client for the separate Flask service."""
import json
import os
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title='SuperKart Sales Planner', page_icon='🛒', layout='wide')
st.title('SuperKart Sales Planner')
st.caption('Estimate product sales revenue from product and store attributes.')
API_URL = os.getenv('BACKEND_URL', 'http://localhost:7860').rstrip('/')
st.info('Store age uses the fixed project reference year 2025. Estimates reflect the sales period represented by the training data; no currency or quarter dates were supplied.')


def post(endpoint, **kwargs):
    response = requests.post(API_URL + endpoint, timeout=60, **kwargs)
    if not response.ok:
        try:
            detail = response.json().get('error', response.text)
        except ValueError:
            detail = response.text
        raise ValueError(f'API returned {response.status_code}: {detail}')
    return response


single, batch = st.tabs(['Single prediction', 'Batch CSV prediction'])
with single:
    with st.form('prediction'):
        left, right = st.columns(2)
        with left:
            weight = st.number_input('Product weight', min_value=0.01, value=12.66)
            sugar = st.selectbox('Sugar content', ['Low Sugar', 'Regular', 'No Sugar'])
            area = st.number_input('Allocated display area ratio', min_value=0.0, max_value=1.0, value=0.027, format='%.3f', step=0.001)
            price = st.number_input('Maximum retail price', min_value=0.01, value=117.08)
            prefix = st.selectbox('Product ID prefix', ['FD', 'DR', 'NC'])
        with right:
            size = st.selectbox('Store size', ['Medium', 'Small', 'High'])
            tier = st.selectbox('City tier', ['Tier 2', 'Tier 1', 'Tier 3'])
            kind = st.selectbox('Store type', ['Supermarket Type2', 'Supermarket Type1', 'Departmental Store', 'Food Mart', 'Supermarket Type3'])
            age = st.number_input('Store age in 2025 (years)', min_value=0, max_value=200, value=16)
            category = st.selectbox('Product category', ['Non Perishables', 'Perishables'])
        submitted = st.form_submit_button('Predict sales', type='primary')
    if submitted:
        payload = dict(Product_Weight=weight, Product_Sugar_Content=sugar,
                       Product_Allocated_Area=area, Product_MRP=price,
                       Store_Size=size, Store_Location_City_Type=tier,
                       Store_Type=kind, Product_Id_char=prefix,
                       Store_Age_Years=age, Product_Type_Category=category)
        try:
            result = post('/v1/predict', json=payload).json()
            st.metric('Estimated sales revenue (dataset units)', f"{result['Sales']:,.2f}")
            for notice in result.get('warnings', []):
                st.warning(notice)
        except (requests.RequestException, ValueError, KeyError) as exc:
            st.error(f'Could not obtain a prediction: {exc}')

with batch:
    st.write('Upload a CSV with the 10 prepared feature columns, matching Batch_Data_SuperKart.csv.')
    features = ['Product_Weight', 'Product_Sugar_Content', 'Product_Allocated_Area',
                'Product_MRP', 'Store_Size', 'Store_Location_City_Type', 'Store_Type',
                'Product_Id_char', 'Store_Age_Years', 'Product_Type_Category']
    st.download_button('Download CSV column template', ','.join(features) + '\n', 'superkart_template.csv', 'text/csv')
    upload = st.file_uploader('Choose CSV', type=['csv'])
    if upload is not None and st.button('Predict batch', type='primary'):
        try:
            raw = upload.getvalue()
            response = post('/v1/predictbatch', files={'file': (upload.name, raw, 'text/csv')})
            frame = pd.read_csv(__import__('io').BytesIO(raw))
            values = response.json()
            frame['Predicted_Product_Store_Sales_Total'] = [values[str(i)] for i in range(len(frame))]
            for notice in json.loads(response.headers.get('X-SuperKart-Warnings', '[]')):
                st.warning(notice)
            st.session_state['batch_results'] = frame
        except (requests.RequestException, ValueError, KeyError) as exc:
            st.error(f'Could not process the CSV: {exc}')
    if 'batch_results' in st.session_state:
        frame = st.session_state['batch_results']
        st.dataframe(frame, hide_index=True, width='stretch')
        st.download_button('Download predictions', frame.to_csv(index=False), 'superkart_predictions.csv', 'text/csv')

with st.expander('How to interpret estimates'):
    st.write('Predictions describe associations learned from four stores. New store types or combinations of attributes may be unreliable. Use estimates as planning inputs and compare them against actual sales. They do not measure the causal effect of changing prices or shelf space.')
