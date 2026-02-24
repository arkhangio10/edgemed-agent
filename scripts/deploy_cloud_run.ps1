# Deploy EdgeMed API to Cloud Run (Windows PowerShell).
# Optional: set $env:EDGEMED_GOOGLE_API_KEY_SECRET = "edgemed-google-api-key" to use Secret Manager for the API key.

$ErrorActionPreference = "Stop"
$ProjectId = if ($env:EDGEMED_PROJECT_ID) { $env:EDGEMED_PROJECT_ID } else { "edgemed-agent" }
$Region = if ($env:EDGEMED_REGION) { $env:EDGEMED_REGION } else { "us-central1" }
$ServiceName = "edgemed-api"
$Image = "gcr.io/$ProjectId/$ServiceName"

$EnvVars = "EDGEMED_PROJECT_ID=$ProjectId,EDGEMED_GOOGLE_CLOUD_PROJECT=$ProjectId,EDGEMED_DEMO_MODE_ENABLED=true,EDGEMED_PROD_MODE_ENABLED=false"

Write-Host "=== Building Docker image ==="
docker build -t $Image -f cloud/Dockerfile .

Write-Host "=== Pushing to GCR ==="
docker push $Image

Write-Host "=== Deploying to Cloud Run ==="
$DeployArgs = @(
    "run", "deploy", $ServiceName,
    "--image", $Image,
    "--region", $Region,
    "--project", $ProjectId,
    "--platform", "managed",
    "--allow-unauthenticated",
    "--set-env-vars", $EnvVars,
    "--memory", "1Gi",
    "--cpu", "1",
    "--min-instances", "0",
    "--max-instances", "5",
    "--timeout", "300"
)
if ($env:EDGEMED_GOOGLE_API_KEY_SECRET) {
    $SecretRef = $env:EDGEMED_GOOGLE_API_KEY_SECRET
    if ($SecretRef -notmatch ":") { $SecretRef = "${SecretRef}:latest" }
    $DeployArgs += "--set-secrets=EDGEMED_GOOGLE_API_KEY=$SecretRef"
}
& gcloud $DeployArgs

Write-Host "=== Deployment complete ==="
& gcloud run services describe $ServiceName --region $Region --project $ProjectId --format "value(status.url)"
