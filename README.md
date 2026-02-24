# EdgeMed Agent

AI-powered clinical documentation agent that converts free-text clinician notes into structured EHR-grade JSON using MedGemma, with offline-first architecture, agentic validation, and encrypted local storage.

## Architecture

- **Web Demo (DEMO_MODE):** React SPA on Firebase Hosting, Firebase Anonymous Auth, Cloud Run API, Firestore for structured records, BigQuery for metrics
- **Local Offline App (PROD_MODE):** Streamlit UI + FastAPI, local extraction (stub/MedGemma), Tink AEAD encrypted SQLite queue, auto-sync to cloud
- **Cloud API:** FastAPI on Cloud Run with `/v1/extract`, `/v1/chat`, `/v1/sync`, `/v1/interpret-image`, `/v1/prescription-from-image`, `/v1/health`

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for containerized deployment)
- Google Cloud SDK (for cloud deployment)

### 1. Local Offline App (no internet required)

```bash
# Install dependencies
pip install -r local/requirements.txt

# Generate synthetic data
python scripts/generate_synth_dataset.py

# Start the local API server
PYTHONPATH=. uvicorn local.local_api:app --host 0.0.0.0 --port 8000

# In another terminal, start the Streamlit UI
PYTHONPATH=. streamlit run local/app.py --server.port 8501
```

Open http://localhost:8501 to use the local app.

### 2. Cloud API (development)

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your Google Cloud project details

# Install dependencies
pip install -r cloud/requirements.txt

# Start the cloud API locally
PYTHONPATH=. uvicorn cloud.main:app --host 0.0.0.0 --port 8080
```

### 3. Web Demo Frontend

```bash
cd web
npm install

# Copy and configure Firebase settings
cp .env.example .env
# Edit .env with your Firebase config

npm run dev
```

Open http://localhost:5173 for the web demo. The chat and image features call the Cloud API (Vertex AI); set `VITE_API_BASE_URL` to your Cloud Run URL. No API key is required in the frontend — auth uses Firebase ID tokens.

### Google API key (chatbot and prescription only)

To use the **chatbot** and **prescription-from-image** endpoints, set a Google API key (Gemini API) in your environment. This key is **not** used for note extraction or for **medical image interpretation** (to avoid losing points in the competition).

- Get a key at [Google AI Studio](https://aistudio.google.com/apikey).
- Set in `.env`: `EDGEMED_GOOGLE_API_KEY=your_key` (do not commit the key).
- **Medical image interpretation** uses only **MedGemma** (vision endpoint) or **Vertex AI** — never the Gemini API key.

### 4. Docker Compose (full stack)

```bash
cp .env.example .env
# Edit .env

docker compose up --build
```

- Cloud API: http://localhost:8080
- Local Streamlit UI: http://localhost:8501
- Local API: http://localhost:8000

## Cloud Deployment

### Deploy Cloud Run API

```bash
chmod +x scripts/deploy_cloud_run.sh
EDGEMED_PROJECT_ID=edgemedsoinar scripts/deploy_cloud_run.sh
```

To **deploy new code changes**, run the same script again from the repo root: it rebuilds the image, pushes to GCR, and deploys the new revision.

### API key via Secret Manager (recommended)

Do not pass the Google API key as a plain environment variable. Use [Secret Manager](https://console.cloud.google.com/security/secret-manager):

1. **Create the secret:** In Console go to **Security > Secret Manager > Create secret**. Name it e.g. `edgemed-google-api-key`, value = your Gemini API key. Or via CLI:
   ```bash
   echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create edgemed-google-api-key --data-file=- --project=edgemedsoinar
   ```
2. **Grant Cloud Run access:** In Secret Manager, open the secret → **Permissions** → Add principal: `499665737458-compute@developer.gserviceaccount.com` (use your project number), role **Secret Manager Secret Accessor**.
3. **Deploy with the secret:**
   - **Linux/Mac/Git Bash:**
     ```bash
     EDGEMED_PROJECT_ID=edgemedsoinar EDGEMED_GOOGLE_API_KEY_SECRET=edgemed-google-api-key scripts/deploy_cloud_run.sh
     ```
   - **Windows (PowerShell):**
     ```powershell
     $env:EDGEMED_PROJECT_ID = "edgemedsoinar"
     $env:EDGEMED_GOOGLE_API_KEY_SECRET = "edgemed-google-api-key"
     .\scripts\deploy_cloud_run.ps1
     ```
   - **Or run gcloud directly (any OS):**
     ```bash
     gcloud run deploy edgemed-api --image gcr.io/edgemedsoinar/edgemed-api --region us-central1 --project edgemedsoinar --platform managed --allow-unauthenticated --set-env-vars "EDGEMED_PROJECT_ID=edgemedsoinar,EDGEMED_GOOGLE_CLOUD_PROJECT=edgemedsoinar,EDGEMED_DEMO_MODE_ENABLED=true,EDGEMED_PROD_MODE_ENABLED=false" --set-secrets "EDGEMED_GOOGLE_API_KEY=edgemed-google-api-key:latest" --memory 1Gi --cpu 1 --min-instances 0 --max-instances 5 --timeout 300
     ```

The service will receive `EDGEMED_GOOGLE_API_KEY` from the secret at runtime (used only for chatbot and prescription-from-image).

### Setup BigQuery Tables

```bash
chmod +x scripts/setup_bigquery.sh
EDGEMED_PROJECT_ID=your-project-id scripts/setup_bigquery.sh
```

### Deploy Firebase Hosting

```bash
cd web && npm run build && cd ..
cd firebase && firebase deploy --only hosting,firestore
```

### Deploy Firestore Rules

```bash
cd firebase && firebase deploy --only firestore:rules
```

## Kaggle Competition Assets (Optional)

This project is built for the [Med-Gemma Impact Challenge](https://www.kaggle.com/competitions/med-gemma-impact-challenge) on Kaggle. The competition states "Competition Data: None" — no datasets are provided. However, official assets such as write-up templates, submission instructions, or starter notebooks may appear on the competition Data tab over time.

A helper script can fetch any available assets. **This step is entirely optional** — EdgeMed Agent runs fully without it and may download nothing.

### Setup Kaggle API (one-time)

```bash
pip install kaggle
```

Get your API token from [kaggle.com/settings](https://www.kaggle.com/settings) -> API -> Create New Token. This downloads a `kaggle.json` file. Place it at:

- **Linux/Mac:** `~/.kaggle/kaggle.json` (then `chmod 600 ~/.kaggle/kaggle.json`)
- **Windows:** `%USERPROFILE%\.kaggle\kaggle.json`

**Do not commit `kaggle.json` to git.** It is already in `.gitignore`.

### Fetch Assets

```bash
python scripts/fetch_kaggle_assets.py
```

The script will:
1. Verify the kaggle CLI and credentials are present
2. List any files available in the competition
3. Download them to `assets/kaggle/` if they exist
4. Exit gracefully with a clear message if no files are available

Downloaded assets are gitignored. Review them manually before use — verify no PHI or restricted data is present, and use the official write-up template for your submission if one is provided.

## Evaluation

### Generate Synthetic Dataset

```bash
python scripts/generate_synth_dataset.py --count 50 --seed 42
```

### Run Evaluation Pipeline

```bash
python scripts/eval_pipeline.py
```

Outputs:
- `eval_results.json` — per-note and aggregate metrics
- `eval_summary.csv` — one row per metric

Metrics computed:
- Field-level F1 for medications, allergies, problems
- Critical recall for allergies and medications (safety-critical)
- Avg / median / P95 latency per note

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/v1/health` | GET | Health check |
| `/v1/extract` | POST | Extract structured record from clinical note |
| `/v1/chat` | POST | Grounded Q&A about a patient record (Vertex AI in backend; no API key in frontend) |
| `/v1/sync` | POST | Sync local records to cloud (idempotent) |
| `/v1/interpret-image` | POST | Interpret medical image (MedGemma or Vertex only; no Gemini API key) |
| `/v1/prescription-from-image` | POST | Extract medications from prescription/handwritten image |
| `/v1/analytics` | GET | Aggregated BigQuery metrics for dashboard |

## Privacy & Security

- **DEMO_MODE:** Synthetic notes only; raw note_text never stored in cloud
- **PROD_MODE:** Raw note_text optionally stored in Firestore only (never in BigQuery or logs)
- **BigQuery:** Metrics only with hashed identifiers; never PHI
- **Cloud Logging:** Metadata only; never raw note content
- **Local Queue:** All payloads encrypted with Google Tink AEAD (AES128_GCM); only ciphertext in SQLite
- **Firestore Rules:** UID-scoped access; DEMO and PROD namespaces fully isolated

## Project Structure

```
version_1/
├── shared/          # Canonical Pydantic schemas, validator, prompts
├── cloud/           # Cloud Run FastAPI API
├── local/           # Local offline app (Streamlit + FastAPI)
├── web/             # React web demo frontend
├── firebase/        # Firebase config + Firestore rules
├── bigquery/        # BigQuery DDL + sample queries
├── scripts/         # Synthetic data generator, eval, deploy, Kaggle fetch
├── data/            # Generated synthetic notes + ground truth
├── assets/kaggle/   # (gitignored) Downloaded Kaggle competition assets
├── tests/           # Unit tests
└── Makefile         # Convenience targets (make help)
```

## Third-party / HAI-DEF

This project uses [MedGemma](https://developers.google.com/health-ai-developer-foundations) — a medical AI model by Google — as part of the [Health AI Developer Foundations (HAI-DEF)](https://developers.google.com/health-ai-developer-foundations) initiative.

- **Model card:** [MedGemma 1.5](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card) (4B multimodal instruction-tuned; supports 2D/3D imaging, WSI, longitudinal CXR, document understanding, EHR).
- **Repository:** [Google-Health/medgemma](https://github.com/Google-Health/medgemma) (notebooks, tutorials).
- **Model Garden:** [MedGemma on Vertex AI](https://console.cloud.google.com/vertex-ai/model-garden) — for production scale, use the custom container with server-side image processing (WSI, CT/MRI from DICOM/GCS).

MedGemma / HAI-DEF is provided under and subject to the **Health AI Developer Foundations Terms of Use**:
- **Terms of Use:** https://developers.google.com/health-ai-developer-foundations/terms
- **Prohibited Use Policy:** https://ai.google.dev/gemma/prohibited_use_policy

See [`HAI-DEF_NOTICE.txt`](./HAI-DEF_NOTICE.txt) in the repository root for the required notice.

### MedGemma in EdgeMed

- **Note extraction:** When `EDGEMED_MEDGEMMA_ENDPOINT_ID` is set, the cloud API uses the deployed MedGemma endpoint (text or multimodal) for structured extraction.
- **Medical image interpretation:** `/v1/interpret-image` uses **only** MedGemma (vision endpoint) or Vertex AI — the Gemini API key is **not** used here. Configure a MedGemma **multimodal** endpoint for best results. For high-dimensional imaging (CT/MRI, WSI), deploy via Model Garden with the custom container.

### MedGemma Local Mode (Optional)

To activate MedGemma for local extraction (requires ~16 GB RAM / GPU recommended):

```bash
# Set environment variables (MedGemma 1.5 4B instruction-tuned)
EDGEMED_USE_MEDGEMMA_LOCAL=true
EDGEMED_MEDGEMMA_MODEL_ID=google/medgemma-1.5-4b-it

# Install extra dependencies
pip install -r local/requirements-medgemma.txt

# Start the local API as usual
PYTHONPATH=. uvicorn local.local_api:app --host 0.0.0.0 --port 8000
```

If `USE_MEDGEMMA_LOCAL` is not set or `false`, the local app defaults to the lightweight rule-based stub extractor (no GPU or heavy dependencies required).

## Disclaimer

**EdgeMed Agent is a clinical documentation support tool only. It does NOT provide diagnoses, treatment recommendations, or medical advice. It is NOT a substitute for professional clinical judgment.** All outputs must be reviewed and validated by a licensed healthcare professional before use in any clinical context.

This tool is intended for **documentation assistance and research purposes only**. See the [HAI-DEF Prohibited Use Policy](https://ai.google.dev/gemma/prohibited_use_policy) for restrictions on usage.
