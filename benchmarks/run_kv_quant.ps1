# Parte B.4 — Repite la medición del KV cache pero cuantizado a Q8_0.
#
# Ollama lee la variable OLLAMA_KV_CACHE_TYPE al ARRANCAR, así que hay que
# parar la app de la bandeja y lanzar un servidor temporal con esa variable.
# La cuantización del KV cache necesita flash attention activado.
#
# Uso (desde la raíz del proyecto):  .\benchmarks\run_kv_quant.ps1

Write-Host "Parando Ollama (app de bandeja y servidor)..."
Get-Process -Name "ollama*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

Write-Host "Arrancando servidor temporal con KV cache q8_0 + flash attention..."
$env:OLLAMA_FLASH_ATTENTION = "1"
$env:OLLAMA_KV_CACHE_TYPE = "q8_0"
$server = Start-Process -FilePath "ollama" -ArgumentList "serve" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 5

Write-Host "Ejecutando benchmark (filas etiquetadas kv_cache_type=q8_0)..."
& .\.venv\Scripts\python.exe benchmarks\parte_b_kvcache.py --kv q8_0

Write-Host "Parando servidor temporal..."
Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue

Write-Host "Listo. Vuelve a abrir la app de Ollama normal si la necesitas."
