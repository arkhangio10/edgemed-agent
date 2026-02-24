.PHONY: help kaggle-assets synth-data eval test local-api local-ui cloud-api

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

kaggle-assets:  ## (Optional) Fetch official Kaggle competition assets
	python scripts/fetch_kaggle_assets.py

synth-data:  ## Generate synthetic dataset (deterministic, seed=42)
	python scripts/generate_synth_dataset.py --count 50 --seed 42

eval:  ## Run evaluation pipeline on synthetic data
	python scripts/eval_pipeline.py

test:  ## Run all unit tests
	python tests/test_schemas.py
	python tests/test_validator.py
	python tests/test_extraction.py
	python tests/test_queue_manager.py
	python tests/test_sync.py

local-api:  ## Start local FastAPI server (port 8000)
	PYTHONPATH=. uvicorn local.local_api:app --host 0.0.0.0 --port 8000

local-ui:  ## Start local Streamlit UI (port 8501)
	PYTHONPATH=. streamlit run local/app.py --server.port 8501

cloud-api:  ## Start cloud FastAPI server locally (port 8080)
	PYTHONPATH=. uvicorn cloud.main:app --host 0.0.0.0 --port 8080
