# Setup de un comando (reproducibilidad).
# Requisitos previos: Ollama instalado y en PATH, Python 3.13, git.
# Uso:  .\setup.ps1

$ErrorActionPreference = "Stop"

Write-Host "[1/4] Entorno virtual + dependencias fijadas..."
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet

Write-Host "[2/4] Modelos locales (3 cuantizaciones + embeddings)..."
ollama pull llama3.2:3b-instruct-q8_0
ollama pull llama3.2:3b-instruct-q4_K_M
ollama pull llama3.2:3b-instruct-q3_K_M
ollama pull nomic-embed-text

Write-Host "[3/4] Corpus RAG (docs de Ollama y llama.cpp)..."
if (-not (Test-Path corpus\api.md)) {
    $tmp = "$env:TEMP\rag_clone"
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    git clone --depth 1 https://github.com/ollama/ollama $tmp\ollama
    git clone --depth 1 https://github.com/ggml-org/llama.cpp $tmp\llamacpp
    New-Item -ItemType Directory -Force corpus\llamacpp | Out-Null
    Copy-Item "$tmp\ollama\docs\*.md" corpus\ -Force
    Copy-Item "$tmp\llamacpp\docs" corpus\llamacpp -Recurse -Force
    Copy-Item "$tmp\llamacpp\README.md" corpus\llamacpp\ -Force
    # Docs de la web oficial de Ollama (mintlify expone .md)
    New-Item -ItemType Directory -Force corpus\ollama-site | Out-Null
    $idx = (Invoke-WebRequest -Uri "https://docs.ollama.com/llms.txt" -UseBasicParsing).Content
    $urls = [regex]::Matches($idx, 'https://docs\.ollama\.com/[^\s\)]+\.md') |
            ForEach-Object { $_.Value } | Select-Object -Unique
    foreach ($u in $urls) {
        $name = ($u -replace 'https://docs\.ollama\.com/', '' -replace '/', '_')
        try { Invoke-WebRequest -Uri $u -UseBasicParsing -OutFile "corpus\ollama-site\$name" } catch {}
    }
}

Write-Host "[4/4] Indice vectorial RAG (sqlite-vec + nomic-embed-text)..."
.\.venv\Scripts\python.exe parte_c_rag.py ingest

Write-Host ""
Write-Host "Listo. Prueba:  .\.venv\Scripts\python.exe jarvis.py"
Write-Host "Correo opcional: copia .env.example a .env y configura la app password."
