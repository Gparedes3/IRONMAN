# Parte B.4 — Repetir el benchmark con el KV cache cuantizado a Q8_0.
#
# Ollama lee OLLAMA_KV_CACHE_TYPE al ARRANCAR, así que hay que parar la app
# de la bandeja y lanzar un servidor temporal con las variables puestas.
# La cuantización del KV cache requiere flash attention activado.
#
# Uso (desde la raíz del repo):  .\benchmarks\run_kv_quant.ps1

Write-Host "Parando Ollama (app de bandeja y servidor)..."
Get-Process -Name "ollama*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

Write-Host "Arrancando servidor temporal con KV cache q8_0 + flash attention..."
$env:OLLAMA_FLASH_ATTENTION = "1"
$env:OLLAMA_KV_CACHE_TYPE = "q8_0"
$server = Start-Process -FilePath "ollama" -ArgumentList "serve" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 5

Write-Host "Ejecutando benchmark (filas etiquetadas kv_cache_type=q8_0)..."
& .\.venv\Scripts\python.exe benchmarks\bench_kv.py --kv q8_0

Write-Host "Parando servidor temporal..."
Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue

Write-Host "Listo. Vuelve a abrir la app de Ollama normal si la necesitas."
Write-Host "(El servidor normal usa KV f16; las filas f16 vienen de bench_kv.py sin flags.)"
