Write-Host "--- Nutri-RAG: Research Assistant Initialization ---" -ForegroundColor Cyan

# -------------------------------
# 1. Check Python
# -------------------------------
$pythonFound = $false
try {
    python --version > $null 2>&1
    $pythonFound = $true
} catch {}

# -------------------------------
# 2. Check Docker
# -------------------------------
$dockerRunning = $false
docker info > $null 2>&1
if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }

# -------------------------------
# 3. Validate Environment
# -------------------------------
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file missing. Please configure environment variables." -ForegroundColor Red
    exit 1
}

# -------------------------------
# 4. Launch Logic
# -------------------------------
if ($dockerRunning) {
    Write-Host "[OPS MODE] Docker detected. Launching full stack..." -ForegroundColor Green
    
    Set-Location ops

    docker-compose up -d --build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker failed to start services." -ForegroundColor Red
        exit 1
    }

    Write-Host ">>> Backend: http://localhost:8000" -ForegroundColor Green
    Write-Host ">>> Grafana: http://localhost:3001" -ForegroundColor Cyan

    docker-compose logs -f nutri-rag

} else {
    Write-Host "[LOCAL MODE] Docker not available. Starting FastAPI backend..." -ForegroundColor Yellow
    
    if (-not $pythonFound) {
        Write-Host "ERROR: Python not found." -ForegroundColor Red
        exit 1
    }

    Set-Location backend

    # Install only if needed
    if (-not (Test-Path "venv")) {
        python -m venv venv
        .\venv\Scripts\Activate
        pip install -r requirements.txt
    } else {
        .\venv\Scripts\Activate
    }

    Write-Host ">>> Starting backend server..." -ForegroundColor Green
    uvicorn main:app --reload
}