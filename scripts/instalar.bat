@echo off
rem ============================================
rem  MiClaw — instalador para Windows
rem  (un solo clic: crea el entorno e instala)
rem ============================================
chcp 65001 >nul
cd /d "%~dp0.."

echo.
echo  ============================================
echo    MiClaw — instalando dependencias...
echo  ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo  [!] No encuentro Python. Instala Python 3.10+ desde https://python.org
  echo      (marca "Add Python to PATH" durante la instalacion)
  pause
  exit /b 1
)

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

echo.
echo  ============================================
echo    Instalado. Para arrancar MiClaw:
echo      doble clic en scripts\arrancar.bat
echo    Luego abre http://localhost:8000
echo  ============================================
echo.
pause
