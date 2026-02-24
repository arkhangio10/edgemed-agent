@echo off
REM Rebuild image, push to GCR, deploy Cloud Run with secret.
REM Run from repo root. Ensure Docker Desktop is running and you are logged in:
REM   gcloud auth configure-docker gcr.io

set PROJECT_ID=edgemedsoinar
set IMAGE=gcr.io/%PROJECT_ID%/edgemed-api
set REGION=us-central1

echo === Building Docker image ===
docker build -t %IMAGE% -f cloud/Dockerfile .
if errorlevel 1 goto :error

echo === Pushing to GCR ===
docker push %IMAGE%
if errorlevel 1 goto :error

echo === Deploying to Cloud Run (with API key secret) ===
gcloud run deploy edgemed-api ^
  --image %IMAGE% ^
  --region %REGION% ^
  --project %PROJECT_ID% ^
  --platform managed ^
  --allow-unauthenticated ^
  --set-env-vars "EDGEMED_PROJECT_ID=%PROJECT_ID%,EDGEMED_GOOGLE_CLOUD_PROJECT=%PROJECT_ID%,EDGEMED_DEMO_MODE_ENABLED=true,EDGEMED_PROD_MODE_ENABLED=false,EDGEMED_MEDGEMMA_ENDPOINT_ID=mg-endpoint-af28625e-9f0d-408f-9ea8-efb8cf1e1abe,EDGEMED_MEDGEMMA_REGION=us-central1" ^
  --set-secrets "EDGEMED_GOOGLE_API_KEY=edgemed-google-api-key:latest" ^
  --memory 1Gi ^
  --cpu 1 ^
  --min-instances 0 ^
  --max-instances 5 ^
  --timeout 300
if errorlevel 1 goto :error

echo.
echo === Deploy complete ===
echo Service URL: https://edgemed-api-499665737458.us-central1.run.app
goto :eof

:error
echo Failed. Check Docker is running and gcloud is logged in.
exit /b 1
