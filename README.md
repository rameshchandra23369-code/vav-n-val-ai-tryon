
# Vav n Val — FASHN AI Virtual Try-On

This is a ready-to-deploy Streamlit web app for Vav n Val.

## What it does

1. Upload a model photo.
2. Upload a garment/dress photo.
3. Choose resolution, quality, and number of results.
4. Send the images to FASHN `tryon-max`.
5. Show generated try-on images.
6. Download the result.

## Security

Do NOT put your FASHN API key in `app.py` or commit it to GitHub.

For Streamlit Community Cloud, add this secret:

```toml
FASHN_API_KEY = "YOUR_FASHN_API_KEY"
```

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload:
   - `app.py`
   - `requirements.txt`
3. Go to https://share.streamlit.io/
4. Create a new app and select your GitHub repository.
5. Choose `app.py` as the main file.
6. Open Advanced settings → Secrets.
7. Paste:

```toml
FASHN_API_KEY = "YOUR_FASHN_API_KEY"
```

8. Deploy.

After deployment, Streamlit gives you a shareable `*.streamlit.app` URL.

## Local test

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit.

## FASHN API

This app uses:

- `POST https://api.fashn.ai/v1/run`
- `GET https://api.fashn.ai/v1/status/{prediction_id}`

Model:
- `tryon-max`

The app sends local uploads as base64 data URIs and asks FASHN to return base64 output.
