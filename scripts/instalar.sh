#!/usr/bin/env bash
# MiClaw — instalación en Linux/macOS (un solo comando)
set -e

echo "== MiClaw: instalando dependencias =="
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cat <<'EOF'

✔ Instalado. Para arrancar el asistente:

   ./arrancar.sh
   (o: source .venv/bin/activate && python -m asistente.main)

Luego abre http://localhost:8000 en tu navegador.

Opcional — modelos 100% locales (gratis, sin internet):
   Instala Ollama desde https://ollama.com y ejecuta:  ollama pull llama3.2
EOF
