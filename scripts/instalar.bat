@echo off
setlocal EnableExtensions
title MiClaw - instalar
cd /d "%~dp0.."

echo(
echo  ============================================
echo    MiClaw - instalando dependencias...
echo  ============================================
echo(

set "PY="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  python --version >nul 2>&1
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  python3 --version >nul 2>&1
  if not errorlevel 1 set "PY=python3"
)

if not defined PY (
  echo  [!] No encuentro Python en este PC.
  echo(
  echo      1. Descarga Python 3.10 o superior:
  echo         https://www.python.org/downloads/
  echo      2. En el instalador, MARCA la casilla
  echo         "Add python.exe to PATH"
  echo      3. Cierra esta ventana y vuelve a hacer
  echo         doble clic en INSTALAR.bat
  echo(
  pause
  exit /b 1
)

echo  Python encontrado. Preparando el entorno...
if not exist ".venv\Scripts\python.exe" (
  %PY% -m venv .venv
  if errorlevel 1 (
    echo(
    echo  [!] No pude crear el entorno virtual.
    echo      Prueba a reinstalar Python marcando "Add to PATH".
    echo(
    pause
    exit /b 1
  )
)

echo  Instalando paquetes (puede tardar un minuto)...
echo(
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo(
  echo  [!] pip fallo. Revisa la conexion a internet e intentalo de nuevo.
  echo(
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo(
  echo  [!] No se pudieron instalar las dependencias.
  echo      Revisa la conexion a internet e intentalo de nuevo.
  echo(
  pause
  exit /b 1
)

echo(
echo  ============================================
echo    Listo. Ahora haz doble clic en:
echo      ARRANCAR.bat
echo    Se abrira http://localhost:8000
echo  ============================================
echo(
pause
