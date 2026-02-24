# EdgeMed Agent — Task Tracking

## Status Legend
- ✅ Done
- ⏳ Pending (requires manual/infra action)
- 🔧 Needs verification

---

## A. Legal & Compliance (HAI-DEF / Challenge)

- [x] ✅ Create `HAI-DEF_NOTICE.txt` with exact required text
- [x] ✅ README: "Third-party / HAI-DEF" section + links to ToU & Prohibited Use Policy
- [x] ✅ Web app disclaimer: Landing footer, AppLayout sidebar, Docs page banner
- [ ] ⏳ Review Prohibited Use Policy and confirm usage is permitted (manual review)

## B. MedGemma Integration

- [x] ✅ **Confirmed:** MedGemma IS on Vertex AI Model Garden
  - Model ID: `publishers/google/models/medgemma`
  - Version: `google/medgemma-4b-it` (MedGemma 1.5, 4B multimodal)
  - Region: `us-central1`
  - Requires deployment to Vertex AI endpoint first
- [x] ✅ Cloud: `extraction.py` supports MedGemma endpoint (priority) → Gemini fallback
- [x] ✅ Cloud: `config.py` updated with MEDGEMMA_ENDPOINT_ID, MEDGEMMA_VERSION, MEDGEMMA_REGION
- [x] ✅ Cloud: `model_info` dynamically reflects which model served the request
- [x] ✅ Local: Created `medgemma_extractor.py` with full HuggingFace pipeline
- [x] ✅ Local: Added dependencies in `requirements-medgemma.txt`
- [x] ✅ Local: Added `USE_MEDGEMMA_LOCAL`, `MEDGEMMA_MODEL_ID`, `MEDGEMMA_DEVICE` to config
- [x] ✅ Local: `local_api.py` selects extractor based on `USE_MEDGEMMA_LOCAL`
- [x] ✅ README: MedGemma local activation instructions documented
- [ ] ⏳ **Deploy MedGemma** to Vertex AI endpoint in GCP Console
- [ ] ⏳ Set `EDGEMED_MEDGEMMA_ENDPOINT_ID` after deployment
- [ ] 🔧 Test extraction with MedGemma endpoint
- [ ] 🔧 Test extraction with MedGemma local (requires GPU + model download)

## C. Frontend & API

- [x] ✅ Added `/v1/analytics/overview` backend route matching frontend call
- [x] ✅ Field mapping: backend → frontend contract
- [x] ✅ `AnalyticsData` type updated with `total_extractions` field
- [ ] ⏳ Create `web/.env` from `web/.env.example` with real Firebase + API URL values

## D. Deployment & Infra (Project: edgemedSOINAR)

- [x] ✅ Config updated: project ID = `edgemedSOINAR`, region = `us-central1`
- [x] ✅ `.firebaserc` updated with `edgemedSOINAR`
- [ ] ⏳ GCP: Enable APIs (Cloud Run, Vertex AI, Firestore, BigQuery)
- [ ] ⏳ BigQuery: Run table creation scripts
- [ ] ⏳ Cloud Run: Deploy with Docker
- [ ] ⏳ Firebase: Enable Auth, Firestore, deploy Hosting
- [ ] ⏳ Service account: Permissions for Vertex AI, Firestore, BigQuery

## E. Evaluation & Reproducibility

- [ ] 🔧 Run `scripts/generate_synth_dataset.py` and `scripts/eval_pipeline.py`
- [ ] 🔧 Verify `eval_results.json` / `eval_summary.csv` generate without errors

## F. Submission (Med-Gemma Impact Challenge)

- [ ] ⏳ Accept challenge rules & HAI-DEF ToU
- [ ] ⏳ Single submission: writeup + repo
- [x] ✅ Repo: README clear, NOTICE HAI-DEF, instructions for deployment
- [ ] ⏳ Writeup: usage of MedGemma/HAI-DEF, data, limitations, repo link
