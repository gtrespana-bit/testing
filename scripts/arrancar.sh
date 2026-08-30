#!/usr/bin/env bash
# MiClaw — arranca el asistente en http://localhost:8000
cd "$(dirname "$0")/.."

if [ -d .venv ]; then
  source .venv/bin/activate
else
  echo "No encuentro .venv. Ejecuta primero: scripts/instalar.sh"
  exit 1
fi

echo "MiClaw arrancando en http://localhost:8000  (Ctrl+C para parar)"
exec python -m asistente.main
