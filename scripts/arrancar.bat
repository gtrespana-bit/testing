@echo off
rem ============================================
rem  MiClaw — arranque en Windows
rem  Abre el navegador en http://localhost:8000
rem ============================================
chcp 65001 >nul
cd /d "%~dp0.."

if not exist .venv (
  echo  [!] No encuentro .venv. Ejecuta primero: scripts\instalar.bat
  pause
  exit /b 1
)

call .venv\Scripts\activate.bat

echo  Abriendo navegador...
start "" http://localhost:8000
echo  MiClaw arrancando... (cierra esta ventana para parar)
python -m asistente.main
pause
