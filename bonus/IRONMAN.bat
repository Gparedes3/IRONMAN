@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo            Iniciando IRONMAN...
echo   (Habla cuando veas "Escuchando". Di "adios" para salir)
echo ============================================
".venv\Scripts\python.exe" main.py
echo.
echo IRONMAN se ha cerrado. Pulsa una tecla para salir.
pause >nul
