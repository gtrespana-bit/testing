@echo off
setlocal EnableExtensions
title MiClaw
cd /d "%~dp0.."

echo(
echo  ============================================
echo    MiClaw - arranque
echo  ============================================
echo(

if not exist ".venv\Scripts\python.exe" (
  echo  Primera vez: voy a instalar las dependencias...
  echo(
  call "%~dp0instalar.bat"
  if not exist ".venv\Scripts\python.exe" (
    echo(
    echo  [!] La instalacion no termino bien.
    echo      Ejecuta INSTALAR.bat y lee el mensaje de error.
    echo(
    pause
    exit /b 1
  )
)

rem Limpia la cache de bytecode para forzar la nueva version del codigo
rem (evita seguir usando un __pycache__ viejo con "name 'json' is not defined").
if exist "asistente\__pycache__" rmdir /s /q "asistente\__pycache__"

echo  Abriendo el navegador en http://localhost:8000 ...
start "" cmd /c "ping 127.0.0.1 -n 3 >nul & start http://localhost:8000"
echo  MiClaw arrancando. Cierra esta ventana para parar.
echo(

".venv\Scripts\python.exe" -m asistente.main
set "ERR=%ERRORLEVEL%"

echo(
if not "%ERR%"=="0" (
  echo  [!] MiClaw se detuvo con un error.
)
pause
